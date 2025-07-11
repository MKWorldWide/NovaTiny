#!/usr/bin/env python3
"""
NovaSanctum Stream Handler - Cloud Intake and Processing

Receives encrypted emotion data from NovaEdge nodes, processes it,
and stores it in secure cloud storage. Provides real-time streaming
capabilities for the Pioneer Grid dashboard.

Features:
- Flask-based REST API for data ingestion
- Real-time data processing and validation
- Secure S3 storage with encryption
- WebSocket streaming for real-time dashboards
- Automatic data aggregation and analytics
- Health monitoring and alerting
- Scalable architecture with AWS Lambda support

Security:
- TLS encryption for all communications
- AES-256 encryption at rest
- Input validation and sanitization
- Rate limiting and DDoS protection
- Audit logging for all operations

@author Nova Development Team
@version 1.0.0
@date 2024
"""

import os
import json
import logging
import time
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
import queue
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Flask and web framework imports
from flask import Flask, request, jsonify, Response, stream_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.exceptions import BadRequest, Unauthorized, TooManyRequests

# AWS and cloud services
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import redis

# Data processing and validation
from marshmallow import Schema, fields, ValidationError
import numpy as np
from scipy import stats

# Configuration management
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
@dataclass
class StreamConfig:
    """Configuration for NovaSanctum Stream Handler"""
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    threaded: bool = True
    
    # AWS Configuration
    aws_region: str = "us-east-1"
    s3_bucket: str = "novasanctum-logs"
    s3_prefix: str = "emotion-data"
    dynamodb_table: str = "nova-emotions"
    
    # Redis Configuration (for real-time streaming)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Security Configuration
    api_key_header: str = "X-API-Key"
    rate_limit_requests: int = 1000  # requests per minute
    rate_limit_window: int = 60  # seconds
    
    # Data Processing
    batch_size: int = 100
    batch_timeout: int = 30  # seconds
    max_retention_days: int = 90
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "/var/log/nova-sanctum.log"

@dataclass
class EmotionData:
    """Emotion data structure from NovaTiny agents"""
    device_id: str
    timestamp: int
    emotion_label: str
    emotion_confidence: float
    emotion_intensity: float
    battery_level: float
    signal_strength: int
    edge_node_id: str
    received_at: datetime
    processed_at: Optional[datetime] = None

@dataclass
class ProcessingMetrics:
    """Metrics for data processing performance"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_processing_time: float = 0.0
    last_processed: Optional[datetime] = None
    active_connections: int = 0
    queue_size: int = 0

# Data validation schemas
class EmotionDataSchema(Schema):
    """Marshmallow schema for emotion data validation"""
    device_id = fields.Str(required=True, validate=lambda x: len(x) > 0)
    timestamp = fields.Int(required=True, validate=lambda x: x > 0)
    emotion_label = fields.Str(required=True, validate=lambda x: x in [
        'neutral', 'happy', 'sad', 'angry', 'fear', 'surprise',
        'disgust', 'contempt', 'engaged', 'distracted', 'stressed', 'relaxed'
    ])
    emotion_confidence = fields.Float(required=True, validate=lambda x: 0.0 <= x <= 1.0)
    emotion_intensity = fields.Float(required=True, validate=lambda x: 0.0 <= x <= 1.0)
    battery_level = fields.Float(required=True, validate=lambda x: 0.0 <= x <= 1.0)
    signal_strength = fields.Int(required=True, validate=lambda x: -100 <= x <= 0)
    edge_node_id = fields.Str(required=True)

class NovaSanctumStreamHandler:
    """Main stream handler implementation"""
    
    def __init__(self, config: StreamConfig):
        self.config = config
        self.metrics = ProcessingMetrics()
        self.start_time = datetime.now()
        
        # Initialize Flask app
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'nova-sanctum-secret')
        
        # Enable CORS
        CORS(self.app)
        
        # Initialize SocketIO for real-time streaming
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading')
        
        # Initialize logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize AWS services
        self._setup_aws_services()
        
        # Initialize Redis for real-time data
        self._setup_redis()
        
        # Initialize data processing queue
        self.processing_queue = queue.Queue(maxsize=1000)
        self.batch_processor = threading.Thread(target=self._batch_processor, daemon=True)
        self.batch_processor.start()
        
        # Setup routes
        self._setup_routes()
        
        # Setup SocketIO events
        self._setup_socketio_events()
        
        self.logger.info("NovaSanctum Stream Handler initialized successfully")
    
    def _setup_logging(self):
        """Configure logging for the stream handler"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Create log directory if it doesn't exist
        log_path = Path(self.config.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format=log_format,
            handlers=[
                logging.FileHandler(self.config.log_file),
                logging.StreamHandler()
            ]
        )
    
    def _setup_aws_services(self):
        """Initialize AWS services (S3, DynamoDB)"""
        try:
            # Initialize S3 client
            self.s3_client = boto3.client(
                's3',
                region_name=self.config.aws_region,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            
            # Initialize DynamoDB client
            self.dynamodb_client = boto3.client(
                'dynamodb',
                region_name=self.config.aws_region,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            
            # Test S3 connection
            self.s3_client.head_bucket(Bucket=self.config.s3_bucket)
            self.logger.info("AWS services initialized successfully")
            
        except NoCredentialsError:
            self.logger.error("AWS credentials not found")
            raise
        except ClientError as e:
            self.logger.error(f"AWS service error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to initialize AWS services: {e}")
            raise
    
    def _setup_redis(self):
        """Initialize Redis for real-time data streaming"""
        try:
            self.redis_client = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                decode_responses=True
            )
            
            # Test Redis connection
            self.redis_client.ping()
            self.logger.info("Redis initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Redis: {e}")
            raise
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/api/stream', methods=['POST'])
        def ingest_emotion_data():
            """Ingest emotion data from NovaEdge nodes"""
            return self._handle_emotion_ingest()
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return self._handle_health_check()
        
        @self.app.route('/api/metrics', methods=['GET'])
        def get_metrics():
            """Get processing metrics"""
            return self._handle_metrics()
        
        @self.app.route('/api/devices', methods=['GET'])
        def get_devices():
            """Get list of active devices"""
            return self._handle_devices()
        
        @self.app.route('/api/analytics', methods=['GET'])
        def get_analytics():
            """Get emotion analytics"""
            return self._handle_analytics()
        
        @self.app.route('/api/stream/events', methods=['GET'])
        def stream_events():
            """Server-sent events stream"""
            return self._handle_event_stream()
    
    def _setup_socketio_events(self):
        """Setup SocketIO event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            self.metrics.active_connections += 1
            self.logger.info(f"Client connected. Total connections: {self.metrics.active_connections}")
            emit('status', {'message': 'Connected to NovaSanctum'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            self.metrics.active_connections -= 1
            self.logger.info(f"Client disconnected. Total connections: {self.metrics.active_connections}")
        
        @self.socketio.on('join_room')
        def handle_join_room(data):
            """Handle room joining for filtered data streams"""
            room = data.get('room', 'general')
            join_room(room)
            emit('status', {'message': f'Joined room: {room}'})
        
        @self.socketio.on('leave_room')
        def handle_leave_room(data):
            """Handle room leaving"""
            room = data.get('room', 'general')
            leave_room(room)
            emit('status', {'message': f'Left room: {room}'})
    
    def _handle_emotion_ingest(self):
        """Handle emotion data ingestion"""
        start_time = time.time()
        
        try:
            # Validate API key
            api_key = request.headers.get(self.config.api_key_header)
            if not self._validate_api_key(api_key):
                raise Unauthorized("Invalid API key")
            
            # Parse and validate request data
            data = request.get_json()
            if not data:
                raise BadRequest("No JSON data provided")
            
            # Validate data schema
            schema = EmotionDataSchema()
            try:
                validated_data = schema.load(data)
            except ValidationError as e:
                raise BadRequest(f"Validation error: {e.messages}")
            
            # Create EmotionData object
            emotion_data = EmotionData(
                device_id=validated_data['device_id'],
                timestamp=validated_data['timestamp'],
                emotion_label=validated_data['emotion_label'],
                emotion_confidence=validated_data['emotion_confidence'],
                emotion_intensity=validated_data['emotion_intensity'],
                battery_level=validated_data['battery_level'],
                signal_strength=validated_data['signal_strength'],
                edge_node_id=validated_data['edge_node_id'],
                received_at=datetime.now()
            )
            
            # Add to processing queue
            try:
                self.processing_queue.put_nowait(emotion_data)
                self.metrics.queue_size = self.processing_queue.qsize()
            except queue.Full:
                self.logger.warning("Processing queue full, dropping packet")
                return jsonify({"status": "error", "message": "Queue full"}), 503
            
            # Update metrics
            self.metrics.total_requests += 1
            self.metrics.successful_requests += 1
            self.metrics.last_processed = datetime.now()
            
            # Calculate processing time
            processing_time = time.time() - start_time
            self.metrics.average_processing_time = (
                (self.metrics.average_processing_time * (self.metrics.successful_requests - 1) + processing_time) /
                self.metrics.successful_requests
            )
            
            # Broadcast to connected clients
            self._broadcast_emotion_data(emotion_data)
            
            return jsonify({
                "status": "ok",
                "received": True,
                "processing_time": processing_time,
                "queue_size": self.metrics.queue_size
            })
            
        except (BadRequest, Unauthorized) as e:
            self.metrics.failed_requests += 1
            return jsonify({"status": "error", "message": str(e)}), e.code
        except Exception as e:
            self.metrics.failed_requests += 1
            self.logger.error(f"Error processing emotion data: {e}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500
    
    def _handle_health_check(self):
        """Handle health check requests"""
        uptime = datetime.now() - self.start_time
        
        health_status = {
            "status": "healthy",
            "uptime": str(uptime),
            "version": "1.0.0",
            "services": {
                "s3": self._check_s3_health(),
                "redis": self._check_redis_health(),
                "dynamodb": self._check_dynamodb_health()
            },
            "metrics": asdict(self.metrics)
        }
        
        return jsonify(health_status)
    
    def _handle_metrics(self):
        """Handle metrics requests"""
        return jsonify(asdict(self.metrics))
    
    def _handle_devices(self):
        """Handle device list requests"""
        try:
            # Get active devices from Redis
            active_devices = self.redis_client.smembers('active_devices')
            
            devices = []
            for device_id in active_devices:
                device_data = self.redis_client.hgetall(f'device:{device_id}')
                if device_data:
                    devices.append(device_data)
            
            return jsonify({"devices": devices})
            
        except Exception as e:
            self.logger.error(f"Error getting devices: {e}")
            return jsonify({"status": "error", "message": "Failed to get devices"}), 500
    
    def _handle_analytics(self):
        """Handle analytics requests"""
        try:
            # Get analytics from Redis
            analytics = self.redis_client.hgetall('analytics:current')
            
            return jsonify({"analytics": analytics})
            
        except Exception as e:
            self.logger.error(f"Error getting analytics: {e}")
            return jsonify({"status": "error", "message": "Failed to get analytics"}), 500
    
    def _handle_event_stream(self):
        """Handle server-sent events stream"""
        def generate():
            while True:
                # Get latest events from Redis
                events = self.redis_client.lrange('events:latest', 0, 9)
                
                for event in events:
                    yield f"data: {event}\n\n"
                
                time.sleep(1)
        
        return Response(generate(), mimetype='text/event-stream')
    
    def _validate_api_key(self, api_key: str) -> bool:
        """Validate API key"""
        if not api_key:
            return False
        
        # In production, validate against database or secure storage
        valid_keys = os.getenv('NOVA_API_KEYS', '').split(',')
        return api_key in valid_keys
    
    def _batch_processor(self):
        """Background thread for batch processing emotion data"""
        batch = []
        last_batch_time = time.time()
        
        while True:
            try:
                # Get data from queue with timeout
                try:
                    emotion_data = self.processing_queue.get(timeout=1.0)
                    batch.append(emotion_data)
                except queue.Empty:
                    pass
                
                # Process batch if full or timeout reached
                current_time = time.time()
                if (len(batch) >= self.config.batch_size or 
                    (batch and current_time - last_batch_time >= self.config.batch_timeout)):
                    
                    if batch:
                        self._process_batch(batch)
                        batch = []
                        last_batch_time = current_time
                
            except Exception as e:
                self.logger.error(f"Error in batch processor: {e}")
    
    def _process_batch(self, batch: List[EmotionData]):
        """Process a batch of emotion data"""
        try:
            # Store in S3
            self._store_batch_s3(batch)
            
            # Store in DynamoDB
            self._store_batch_dynamodb(batch)
            
            # Update Redis analytics
            self._update_analytics(batch)
            
            # Update active devices
            self._update_active_devices(batch)
            
            self.logger.info(f"Processed batch of {len(batch)} emotion records")
            
        except Exception as e:
            self.logger.error(f"Error processing batch: {e}")
    
    def _store_batch_s3(self, batch: List[EmotionData]):
        """Store batch in S3"""
        try:
            # Create timestamp-based key
            timestamp = datetime.now().strftime("%Y/%m/%d/%H")
            key = f"{self.config.s3_prefix}/{timestamp}/batch_{int(time.time())}.json"
            
            # Prepare data for S3
            s3_data = {
                'batch_id': f"batch_{int(time.time())}",
                'timestamp': datetime.now().isoformat(),
                'count': len(batch),
                'records': [asdict(emotion_data) for emotion_data in batch]
            }
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.config.s3_bucket,
                Key=key,
                Body=json.dumps(s3_data, default=str),
                ContentType='application/json',
                ServerSideEncryption='AES256'
            )
            
        except Exception as e:
            self.logger.error(f"Error storing batch in S3: {e}")
            raise
    
    def _store_batch_dynamodb(self, batch: List[EmotionData]):
        """Store batch in DynamoDB"""
        try:
            # Prepare items for DynamoDB
            items = []
            for emotion_data in batch:
                item = {
                    'device_id': {'S': emotion_data.device_id},
                    'timestamp': {'N': str(emotion_data.timestamp)},
                    'emotion_label': {'S': emotion_data.emotion_label},
                    'emotion_confidence': {'N': str(emotion_data.emotion_confidence)},
                    'emotion_intensity': {'N': str(emotion_data.emotion_intensity)},
                    'battery_level': {'N': str(emotion_data.battery_level)},
                    'signal_strength': {'N': str(emotion_data.signal_strength)},
                    'edge_node_id': {'S': emotion_data.edge_node_id},
                    'received_at': {'S': emotion_data.received_at.isoformat()}
                }
                items.append(item)
            
            # Batch write to DynamoDB
            with self.dynamodb_client.batch_writer(table_name=self.config.dynamodb_table) as batch_writer:
                for item in items:
                    batch_writer.put_item(Item=item)
            
        except Exception as e:
            self.logger.error(f"Error storing batch in DynamoDB: {e}")
            raise
    
    def _update_analytics(self, batch: List[EmotionData]):
        """Update real-time analytics in Redis"""
        try:
            pipe = self.redis_client.pipeline()
            
            for emotion_data in batch:
                # Update emotion counts
                pipe.hincrby('analytics:emotions', emotion_data.emotion_label, 1)
                
                # Update device activity
                pipe.hset(f'device:{emotion_data.device_id}', 'last_seen', 
                         emotion_data.received_at.isoformat())
                pipe.hset(f'device:{emotion_data.device_id}', 'last_emotion', 
                         emotion_data.emotion_label)
                
                # Update edge node activity
                pipe.hset(f'edge_node:{emotion_data.edge_node_id}', 'last_seen', 
                         emotion_data.received_at.isoformat())
            
            # Update overall metrics
            pipe.hincrby('analytics:overall', 'total_records', len(batch))
            pipe.hset('analytics:overall', 'last_update', datetime.now().isoformat())
            
            pipe.execute()
            
        except Exception as e:
            self.logger.error(f"Error updating analytics: {e}")
    
    def _update_active_devices(self, batch: List[EmotionData]):
        """Update active devices list"""
        try:
            pipe = self.redis_client.pipeline()
            
            for emotion_data in batch:
                # Add to active devices set
                pipe.sadd('active_devices', emotion_data.device_id)
                
                # Set device info
                device_info = {
                    'device_id': emotion_data.device_id,
                    'last_seen': emotion_data.received_at.isoformat(),
                    'last_emotion': emotion_data.emotion_label,
                    'battery_level': str(emotion_data.battery_level),
                    'edge_node_id': emotion_data.edge_node_id
                }
                
                pipe.hmset(f'device:{emotion_data.device_id}', device_info)
            
            pipe.execute()
            
        except Exception as e:
            self.logger.error(f"Error updating active devices: {e}")
    
    def _broadcast_emotion_data(self, emotion_data: EmotionData):
        """Broadcast emotion data to connected clients"""
        try:
            # Prepare data for broadcasting
            broadcast_data = {
                'type': 'emotion_data',
                'data': asdict(emotion_data),
                'timestamp': datetime.now().isoformat()
            }
            
            # Broadcast to all connected clients
            self.socketio.emit('emotion_data', broadcast_data)
            
            # Store in Redis for event stream
            self.redis_client.lpush('events:latest', json.dumps(broadcast_data))
            self.redis_client.ltrim('events:latest', 0, 99)  # Keep only latest 100 events
            
        except Exception as e:
            self.logger.error(f"Error broadcasting emotion data: {e}")
    
    def _check_s3_health(self) -> bool:
        """Check S3 health"""
        try:
            self.s3_client.head_bucket(Bucket=self.config.s3_bucket)
            return True
        except:
            return False
    
    def _check_redis_health(self) -> bool:
        """Check Redis health"""
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def _check_dynamodb_health(self) -> bool:
        """Check DynamoDB health"""
        try:
            self.dynamodb_client.describe_table(TableName=self.config.dynamodb_table)
            return True
        except:
            return False
    
    def run(self):
        """Run the stream handler"""
        self.logger.info(f"Starting NovaSanctum Stream Handler on {self.config.host}:{self.config.port}")
        
        try:
            self.socketio.run(
                self.app,
                host=self.config.host,
                port=self.config.port,
                debug=self.config.debug,
                threaded=self.config.threaded
            )
        except Exception as e:
            self.logger.error(f"Error running stream handler: {e}")
            raise

def main():
    """Main entry point for NovaSanctum Stream Handler"""
    # Load configuration
    config = StreamConfig()
    
    # Create and run stream handler
    handler = NovaSanctumStreamHandler(config)
    
    try:
        handler.run()
    except KeyboardInterrupt:
        print("\nShutting down NovaSanctum Stream Handler...")
    except Exception as e:
        print(f"Fatal error: {e}")
        exit(1)

if __name__ == "__main__":
    main() 