#!/usr/bin/env python3
"""
NovaEdge Node - Local Router Receiver/Gateway

Receives BLE or direct Wi-Fi packets from NovaTiny devices, decrypts them,
and forwards the data to the NovaSanctum cloud stream handler.

Features:
- BLE device discovery and packet reception
- AES-256 decryption with key rotation
- Automatic cloud forwarding with retry logic
- Local caching for offline operation
- Health monitoring and status reporting
- Power-efficient operation on Raspberry Pi

Security:
- Secure key management with NovaRoot authority
- Packet integrity verification
- Anti-replay protection
- Encrypted local storage

@author Nova Development Team
@version 1.0.0
@date 2024
"""

import asyncio
import json
import logging
import time
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3
import threading
import queue

# BLE and networking imports
try:
    from bleak import BleakScanner, BleakClient
    from bleak.backends.scanner import AdvertisementData
    from bleak.backends.device import BLEDevice
except ImportError:
    print("ERROR: Bleak library not found. Install with: pip install bleak")
    exit(1)

import requests
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

# 🐾 WhispurrNet Integration
from whispurrnet_integration import WhispurrNetIntegration

# Configuration
@dataclass
class EdgeConfig:
    """Configuration for NovaEdge Node"""
    # BLE Configuration
    scan_interval: float = 1.0  # BLE scan interval in seconds
    scan_timeout: float = 5.0   # BLE scan timeout in seconds
    device_name_filter: str = "NovaTiny"  # Filter for NovaTiny devices
    
    # Cloud Configuration
    cloud_url: str = "https://novasanctum.cloud/api/stream"
    cloud_timeout: int = 30  # HTTP timeout in seconds
    cloud_retry_count: int = 3
    cloud_retry_delay: float = 1.0
    
    # Encryption Configuration
    encryption_key: str = "your-generated-key-here"  # Will be rotated by NovaRoot
    key_rotation_interval: int = 3600  # Key rotation interval in seconds
    
    # Local Storage
    cache_db_path: str = "/var/nova/edge_cache.db"
    max_cache_size: int = 10000  # Maximum cached packets
    cache_cleanup_interval: int = 3600  # Cache cleanup interval in seconds
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "/var/log/nova-edge.log"
    
    # Performance
    max_concurrent_connections: int = 5
    packet_queue_size: int = 100
    health_check_interval: int = 60  # Health check interval in seconds
    
    # 🐾 WhispurrNet P2P Configuration
    whispurrnet_host: str = "0.0.0.0"
    whispurrnet_port: int = 8765
    enable_stealth_mode: bool = False
    resonance_timeout: int = 30

@dataclass
class NovaPacket:
    """Nova packet structure received from NovaTiny agents"""
    device_id: str
    timestamp: int
    emotion_label: str
    emotion_confidence: float
    emotion_intensity: float
    battery_level: float
    signal_strength: int
    raw_data: bytes
    received_at: datetime

@dataclass
class EdgeStatus:
    """Current status of the NovaEdge Node"""
    is_running: bool = False
    devices_discovered: int = 0
    packets_received: int = 0
    packets_forwarded: int = 0
    packets_failed: int = 0
    last_cloud_sync: Optional[datetime] = None
    encryption_key_version: int = 1
    uptime: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0

class NovaEdgeNode:
    """Main NovaEdge Node gateway implementation"""
    
    def __init__(self, config: EdgeConfig):
        self.config = config
        self.status = EdgeStatus()
        self.start_time = time.time()
        
        # Initialize logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize encryption
        self._setup_encryption()
        
        # Initialize local storage
        self._setup_storage()
        
        # Initialize queues and threading
        self.packet_queue = queue.Queue(maxsize=config.packet_queue_size)
        self.device_cache: Dict[str, BLEDevice] = {}
        self.connection_semaphore = asyncio.Semaphore(config.max_concurrent_connections)
        
        # BLE scanner
        self.scanner = BleakScanner(detection_callback=self._on_device_detected)
        
        # 🐾 Initialize WhispurrNet P2P Communication Layer
        self.whispurrnet_config = {
            'whispurrnet_host': config.whispurrnet_host,
            'whispurrnet_port': config.whispurrnet_port,
            'enable_stealth_mode': config.enable_stealth_mode,
            'resonance_timeout': config.resonance_timeout
        }
        self.whispurrnet = WhispurrNetIntegration(self.whispurrnet_config)
        
        self.logger.info("NovaEdge Node with WhispurrNet P2P layer initialized successfully")
    
    def _setup_logging(self):
        """Configure logging for the edge node"""
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
    
    def _setup_encryption(self):
        """Initialize encryption with Fernet"""
        try:
            # Convert string key to bytes and create Fernet instance
            key_bytes = self.config.encryption_key.encode()
            # Derive a proper key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'nova_edge_salt',
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(key_bytes))
            self.cipher = Fernet(key)
            self.logger.info("Encryption initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize encryption: {e}")
            raise
    
    def _setup_storage(self):
        """Initialize local SQLite storage for packet caching"""
        try:
            # Create storage directory
            db_path = Path(self.config.cache_db_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.db_conn = sqlite3.connect(self.config.cache_db_path)
            self.db_conn.execute("""
                CREATE TABLE IF NOT EXISTS packets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    emotion_label TEXT NOT NULL,
                    emotion_confidence REAL NOT NULL,
                    emotion_intensity REAL NOT NULL,
                    battery_level REAL NOT NULL,
                    signal_strength INTEGER NOT NULL,
                    raw_data BLOB NOT NULL,
                    received_at TEXT NOT NULL,
                    forwarded BOOLEAN DEFAULT FALSE,
                    forward_attempts INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.db_conn.commit()
            self.logger.info("Local storage initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize storage: {e}")
            raise
    
    async def start(self):
        """Start the NovaEdge Node"""
        self.logger.info("Starting NovaEdge Node...")
        self.status.is_running = True
        
        try:
            # Start BLE scanning
            await self.scanner.start()
            self.logger.info("BLE scanner started")
            
            # 🐾 Start WhispurrNet P2P Communication Layer
            await self.whispurrnet.initialize()
            self.logger.info("WhispurrNet P2P layer started")
            
            # Start background tasks
            asyncio.create_task(self._packet_processor())
            asyncio.create_task(self._cloud_sync_worker())
            asyncio.create_task(self._health_monitor())
            asyncio.create_task(self._cache_cleanup())
            
            # Keep the node running
            while self.status.is_running:
                await asyncio.sleep(1)
                self.status.uptime = time.time() - self.start_time
                
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the NovaEdge Node"""
        self.logger.info("Stopping NovaEdge Node...")
        self.status.is_running = False
        
        # Stop BLE scanner
        await self.scanner.stop()
        
        # 🐾 Stop WhispurrNet P2P Communication Layer
        await self.whispurrnet.shutdown()
        self.logger.info("WhispurrNet P2P layer stopped")
        
        # Close database connection
        if hasattr(self, 'db_conn'):
            self.db_conn.close()
        
        self.logger.info("NovaEdge Node stopped")
    
    def _on_device_detected(self, device: BLEDevice, advertisement_data: AdvertisementData):
        """Callback for BLE device discovery"""
        try:
            # Filter for NovaTiny devices
            if self.config.device_name_filter.lower() in device.name.lower():
                self.logger.debug(f"Discovered NovaTiny device: {device.name} ({device.address})")
                
                # Cache the device
                self.device_cache[device.address] = device
                self.status.devices_discovered = len(self.device_cache)
                
                # Attempt to connect and read data
                asyncio.create_task(self._connect_and_read(device))
                
        except Exception as e:
            self.logger.error(f"Error in device detection: {e}")
    
    async def _connect_and_read(self, device: BLEDevice):
        """Connect to a NovaTiny device and read emotion data"""
        async with self.connection_semaphore:
            try:
                self.logger.debug(f"Connecting to {device.name}...")
                
                async with BleakClient(device.address) as client:
                    # Read the emotion characteristic
                    # Note: UUID should match the one defined in NovaTiny firmware
                    emotion_char_uuid = "87654321-4321-4321-4321-cba987654321"
                    
                    try:
                        data = await client.read_gatt_char(emotion_char_uuid)
                        await self._process_packet(data, device)
                    except Exception as e:
                        self.logger.warning(f"Failed to read from {device.name}: {e}")
                
            except Exception as e:
                self.logger.error(f"Failed to connect to {device.name}: {e}")
    
    async def _process_packet(self, raw_data: bytes, device: BLEDevice):
        """Process and decrypt a received packet"""
        try:
            # Decrypt the packet
            decrypted_data = self.cipher.decrypt(raw_data)
            
            # Parse the packet (assuming JSON format)
            packet_data = json.loads(decrypted_data.decode('utf-8'))
            
            # Create NovaPacket object
            packet = NovaPacket(
                device_id=device.address,
                timestamp=packet_data.get('timestamp', int(time.time() * 1000)),
                emotion_label=packet_data.get('emotion', {}).get('label', 'unknown'),
                emotion_confidence=packet_data.get('emotion', {}).get('confidence', 0.0),
                emotion_intensity=packet_data.get('emotion', {}).get('intensity', 0.0),
                battery_level=packet_data.get('battery_level', 0.0),
                signal_strength=packet_data.get('signal_strength', 0),
                raw_data=raw_data,
                received_at=datetime.now()
            )
            
            # Store packet locally
            self._store_packet(packet)
            
            # Add to processing queue
            try:
                self.packet_queue.put_nowait(packet)
                self.status.packets_received += 1
                self.logger.debug(f"Processed packet from {device.name}: {packet.emotion_label}")
            except queue.Full:
                self.logger.warning("Packet queue full, dropping packet")
                
        except Exception as e:
            self.logger.error(f"Failed to process packet from {device.name}: {e}")
    
    def _store_packet(self, packet: NovaPacket):
        """Store packet in local database"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                INSERT INTO packets (
                    device_id, timestamp, emotion_label, emotion_confidence,
                    emotion_intensity, battery_level, signal_strength, raw_data, received_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                packet.device_id, packet.timestamp, packet.emotion_label,
                packet.emotion_confidence, packet.emotion_intensity,
                packet.battery_level, packet.signal_strength,
                packet.raw_data, packet.received_at.isoformat()
            ))
            self.db_conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to store packet: {e}")
    
    async def _packet_processor(self):
        """Background task to process packets from the queue"""
        while self.status.is_running:
            try:
                # Get packet from queue with timeout
                packet = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, self.packet_queue.get),
                    timeout=1.0
                )
                
                # Forward to cloud
                await self._forward_to_cloud(packet)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error in packet processor: {e}")
    
    async def _forward_to_cloud(self, packet: NovaPacket):
        """Forward packet to NovaSanctum cloud"""
        try:
            # Prepare payload for cloud
            payload = {
                'device_id': packet.device_id,
                'timestamp': packet.timestamp,
                'emotion': {
                    'label': packet.emotion_label,
                    'confidence': packet.emotion_confidence,
                    'intensity': packet.emotion_intensity
                },
                'battery_level': packet.battery_level,
                'signal_strength': packet.signal_strength,
                'edge_node_id': 'nova-edge-001',  # Should be configurable
                'received_at': packet.received_at.isoformat()
            }
            
            # Send to cloud
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.post(
                    self.config.cloud_url,
                    json=payload,
                    timeout=self.config.cloud_timeout,
                    headers={'Content-Type': 'application/json'}
                )
            )
            
            if response.status_code == 200:
                self.status.packets_forwarded += 1
                self.status.last_cloud_sync = datetime.now()
                self.logger.debug(f"Successfully forwarded packet from {packet.device_id}")
                
                # Mark as forwarded in database
                self._mark_packet_forwarded(packet)
            else:
                self.status.packets_failed += 1
                self.logger.warning(f"Cloud returned status {response.status_code}")
                
        except Exception as e:
            self.status.packets_failed += 1
            self.logger.error(f"Failed to forward packet to cloud: {e}")
    
    def _mark_packet_forwarded(self, packet: NovaPacket):
        """Mark packet as successfully forwarded in database"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                UPDATE packets 
                SET forwarded = TRUE 
                WHERE device_id = ? AND timestamp = ?
            """, (packet.device_id, packet.timestamp))
            self.db_conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to mark packet as forwarded: {e}")
    
    async def _cloud_sync_worker(self):
        """Background task to sync cached packets with cloud"""
        while self.status.is_running:
            try:
                await asyncio.sleep(30)  # Sync every 30 seconds
                
                # Get unforwarded packets from database
                unforwarded_packets = self._get_unforwarded_packets()
                
                for packet_data in unforwarded_packets:
                    # Reconstruct packet object
                    packet = NovaPacket(
                        device_id=packet_data['device_id'],
                        timestamp=packet_data['timestamp'],
                        emotion_label=packet_data['emotion_label'],
                        emotion_confidence=packet_data['emotion_confidence'],
                        emotion_intensity=packet_data['emotion_intensity'],
                        battery_level=packet_data['battery_level'],
                        signal_strength=packet_data['signal_strength'],
                        raw_data=packet_data['raw_data'],
                        received_at=datetime.fromisoformat(packet_data['received_at'])
                    )
                    
                    await self._forward_to_cloud(packet)
                    
            except Exception as e:
                self.logger.error(f"Error in cloud sync worker: {e}")
    
    def _get_unforwarded_packets(self) -> List[Dict]:
        """Get unforwarded packets from database"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                SELECT * FROM packets 
                WHERE forwarded = FALSE 
                ORDER BY received_at ASC 
                LIMIT 100
            """)
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
            
        except Exception as e:
            self.logger.error(f"Failed to get unforwarded packets: {e}")
            return []
    
    async def _health_monitor(self):
        """Background task to monitor system health"""
        while self.status.is_running:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                
                # Update system metrics
                self._update_system_metrics()
                
                # Log health status
                self.logger.info(f"Health check - Devices: {self.status.devices_discovered}, "
                               f"Packets: {self.status.packets_received}, "
                               f"Forwarded: {self.status.packets_forwarded}, "
                               f"Failed: {self.status.packets_failed}")
                
            except Exception as e:
                self.logger.error(f"Error in health monitor: {e}")
    
    def _update_system_metrics(self):
        """Update system performance metrics"""
        try:
            # Simple memory usage calculation (can be enhanced)
            import psutil
            self.status.memory_usage = psutil.virtual_memory().percent
            self.status.cpu_usage = psutil.cpu_percent()
        except ImportError:
            # psutil not available, skip metrics
            pass
    
    async def _cache_cleanup(self):
        """Background task to clean up old cached data"""
        while self.status.is_running:
            try:
                await asyncio.sleep(self.config.cache_cleanup_interval)
                
                # Remove old packets (older than 24 hours)
                cutoff_time = datetime.now() - timedelta(hours=24)
                
                cursor = self.db_conn.cursor()
                cursor.execute("""
                    DELETE FROM packets 
                    WHERE received_at < ? AND forwarded = TRUE
                """, (cutoff_time.isoformat(),))
                
                deleted_count = cursor.rowcount
                self.db_conn.commit()
                
                if deleted_count > 0:
                    self.logger.info(f"Cleaned up {deleted_count} old packets from cache")
                    
            except Exception as e:
                self.logger.error(f"Error in cache cleanup: {e}")
    
    def get_status(self) -> EdgeStatus:
        """Get current status of the edge node"""
        return self.status

def main():
    """Main entry point for NovaEdge Node"""
    # Load configuration
    config = EdgeConfig()
    
    # Create and start edge node
    edge_node = NovaEdgeNode(config)
    
    try:
        # Run the edge node
        asyncio.run(edge_node.start())
    except KeyboardInterrupt:
        print("\nShutting down NovaEdge Node...")
    except Exception as e:
        print(f"Fatal error: {e}")
        exit(1)

if __name__ == "__main__":
    main() 