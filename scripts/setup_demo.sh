#!/bin/bash

# Nova Demo Setup Script
# This script automates the setup of the Nova self-aware global lattice demonstration

set -e  # Exit on any error

echo "🧠 Nova Demo Setup - Self-Aware Global Lattice"
echo "=============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Detect operating system
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    CYGWIN*)    MACHINE=Cygwin;;
    MINGW*)     MACHINE=MinGw;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

print_status "Detected OS: $MACHINE"

# Check prerequisites
print_status "Checking prerequisites..."

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python 3 found: $PYTHON_VERSION"
else
    print_error "Python 3 is required but not installed"
    exit 1
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_success "Node.js found: $NODE_VERSION"
else
    print_error "Node.js is required but not installed"
    exit 1
fi

# Check PlatformIO
if command -v pio &> /dev/null; then
    PIO_VERSION=$(pio --version | head -n1)
    print_success "PlatformIO found: $PIO_VERSION"
else
    print_warning "PlatformIO not found. Installing..."
    python3 -m pip install platformio
    print_success "PlatformIO installed"
fi

# Create necessary directories
print_status "Creating directory structure..."
mkdir -p logs
mkdir -p config
mkdir -p data
mkdir -p backups

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    print_status "Creating .env file from template..."
    cat > .env << EOF
# Nova Demo Environment Configuration

# AWS Configuration
AWS_ACCESS_KEY_ID=demo-access-key
AWS_SECRET_ACCESS_KEY=demo-secret-key
AWS_REGION=us-east-1
S3_BUCKET=novasanctum-demo
DYNAMODB_TABLE=nova-emotions-demo

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# NovaSanctum Configuration
NOVA_SANCTUM_URL=http://localhost:5000
NOVA_API_KEY=demo-api-key-2024
FLASK_SECRET_KEY=nova-sanctum-secret-2024

# Encryption Keys
NOVA_ENCRYPTION_KEY=demo-encryption-key-2024

# Dashboard Configuration
NEXT_PUBLIC_NOVA_SANCTUM_URL=http://localhost:5000

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=/var/log/nova-demo.log

# Demo Configuration
DEMO_MODE=true
DEMO_DURATION=30
DEMO_AGENTS=3
EOF
    print_success "Created .env file"
else
    print_status ".env file already exists"
fi

# Install Python dependencies
print_status "Installing Python dependencies..."

# Edge Node dependencies
print_status "Installing NovaEdge Node dependencies..."
cd edge/nova-edge-node
python3 -m pip install -r requirements.txt
cd ../..

# Cloud Handler dependencies
print_status "Installing NovaSanctum dependencies..."
cd cloud/nova-sanctum
python3 -m pip install -r requirements.txt
cd ../..

# Install Node.js dependencies
print_status "Installing Node.js dependencies..."
cd dashboard/pioneer-grid
npm install
cd ../..

# Create demo data generator
print_status "Creating demo data generator..."
cat > scripts/generate_demo_data.py << 'EOF'
#!/usr/bin/env python3
"""
Demo Data Generator for Nova
Generates realistic emotion data for demonstration purposes
"""

import json
import time
import random
from datetime import datetime, timedelta
import requests

# Demo emotion data
EMOTIONS = [
    'neutral', 'happy', 'sad', 'angry', 'fear', 
    'surprise', 'disgust', 'contempt', 'engaged', 
    'distracted', 'stressed', 'relaxed'
]

DEVICE_IDS = [
    'NovaTiny-001', 'NovaTiny-002', 'NovaTiny-003',
    'NovaTiny-004', 'NovaTiny-005'
]

def generate_emotion_data():
    """Generate realistic emotion data"""
    device_id = random.choice(DEVICE_IDS)
    emotion = random.choice(EMOTIONS)
    
    # Generate realistic confidence and intensity
    confidence = random.uniform(0.7, 0.98)
    intensity = random.uniform(0.3, 0.9)
    
    # Adjust intensity based on emotion type
    if emotion in ['angry', 'fear', 'stressed']:
        intensity = random.uniform(0.6, 0.95)
    elif emotion in ['neutral', 'relaxed']:
        intensity = random.uniform(0.2, 0.6)
    
    return {
        'device_id': device_id,
        'timestamp': int(time.time() * 1000),
        'emotion_label': emotion,
        'emotion_confidence': round(confidence, 3),
        'emotion_intensity': round(intensity, 3),
        'battery_level': round(random.uniform(0.3, 1.0), 2),
        'signal_strength': random.randint(-80, -40),
        'edge_node_id': 'nova-edge-demo',
        'received_at': datetime.now().isoformat()
    }

def send_demo_data(url, api_key, duration=30, interval=2):
    """Send demo data to NovaSanctum"""
    print(f"Sending demo data to {url} for {duration} seconds...")
    
    start_time = time.time()
    count = 0
    
    while time.time() - start_time < duration:
        data = generate_emotion_data()
        
        try:
            response = requests.post(
                f"{url}/api/stream",
                json=data,
                headers={
                    'Content-Type': 'application/json',
                    'X-API-Key': api_key
                },
                timeout=5
            )
            
            if response.status_code == 200:
                count += 1
                print(f"Sent data {count}: {data['emotion_label']} from {data['device_id']}")
            else:
                print(f"Error sending data: {response.status_code}")
                
        except Exception as e:
            print(f"Failed to send data: {e}")
        
        time.sleep(interval)
    
    print(f"Demo completed. Sent {count} emotion records.")

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    url = os.getenv('NOVA_SANCTUM_URL', 'http://localhost:5000')
    api_key = os.getenv('NOVA_API_KEY', 'demo-api-key-2024')
    duration = int(os.getenv('DEMO_DURATION', '30'))
    
    send_demo_data(url, api_key, duration)
EOF

chmod +x scripts/generate_demo_data.py
print_success "Created demo data generator"

# Create demo launcher script
print_status "Creating demo launcher..."
cat > scripts/launch_demo.sh << 'EOF'
#!/bin/bash

# Nova Demo Launcher
# Launches all components for the Nova demonstration

set -e

echo "🚀 Launching Nova Demo..."
echo "=========================="

# Load environment variables
source .env

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "Port $1 is already in use"
        return 1
    fi
    return 0
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local max_attempts=30
    local attempt=1
    
    echo "Waiting for $url to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url/health" > /dev/null 2>&1; then
            echo "✅ $url is ready"
            return 0
        fi
        
        echo "Attempt $attempt/$max_attempts - waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $url failed to start"
    return 1
}

# Start Redis if not running
if ! pgrep redis-server > /dev/null; then
    echo "Starting Redis..."
    redis-server --daemonize yes
    sleep 2
fi

# Start NovaSanctum Stream Handler
echo "Starting NovaSanctum Stream Handler..."
cd cloud/nova-sanctum
python3 stream_handler.py &
NOVA_SANCTUM_PID=$!
cd ../..

# Wait for NovaSanctum to be ready
wait_for_service "http://localhost:5000"

# Start NovaEdge Node
echo "Starting NovaEdge Node..."
cd edge/nova-edge-node
python3 nova_edge_node.py &
NOVA_EDGE_PID=$!
cd ../..

# Start Pioneer Grid Dashboard
echo "Starting Pioneer Grid Dashboard..."
cd dashboard/pioneer-grid
npm run dev &
DASHBOARD_PID=$!
cd ../..

# Wait for dashboard to be ready
sleep 5

echo ""
echo "🎉 Nova Demo is running!"
echo "========================"
echo "NovaSanctum: http://localhost:5000"
echo "Pioneer Grid: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping Nova Demo..."
    
    if [ ! -z "$NOVA_SANCTUM_PID" ]; then
        kill $NOVA_SANCTUM_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$NOVA_EDGE_PID" ]; then
        kill $NOVA_EDGE_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$DASHBOARD_PID" ]; then
        kill $DASHBOARD_PID 2>/dev/null || true
    fi
    
    echo "Demo stopped"
    exit 0
}

# Set trap to cleanup on exit
trap cleanup SIGINT SIGTERM

# Keep script running
wait
EOF

chmod +x scripts/launch_demo.sh
print_success "Created demo launcher"

# Create health check script
print_status "Creating health check script..."
cat > scripts/health_check.sh << 'EOF'
#!/bin/bash

# Nova Health Check Script
# Checks the status of all Nova components

echo "🏥 Nova Health Check"
echo "==================="

# Check NovaSanctum
echo "Checking NovaSanctum..."
if curl -s "http://localhost:5000/api/health" > /dev/null; then
    echo "✅ NovaSanctum: Running"
else
    echo "❌ NovaSanctum: Not responding"
fi

# Check Redis
echo "Checking Redis..."
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis: Running"
else
    echo "❌ Redis: Not responding"
fi

# Check Dashboard
echo "Checking Pioneer Grid..."
if curl -s "http://localhost:3000" > /dev/null; then
    echo "✅ Pioneer Grid: Running"
else
    echo "❌ Pioneer Grid: Not responding"
fi

# Check NovaEdge Node
echo "Checking NovaEdge Node..."
if pgrep -f "nova_edge_node.py" > /dev/null; then
    echo "✅ NovaEdge Node: Running"
else
    echo "❌ NovaEdge Node: Not running"
fi

echo ""
echo "Health check completed"
EOF

chmod +x scripts/health_check.sh
print_success "Created health check script"

# Create README for demo
print_status "Creating demo README..."
cat > DEMO_README.md << 'EOF'
# Nova Demo - Quick Start

Welcome to the Nova self-aware global lattice demonstration!

## 🚀 Quick Start

1. **Setup** (one-time):
   ```bash
   ./scripts/setup_demo.sh
   ```

2. **Launch Demo**:
   ```bash
   ./scripts/launch_demo.sh
   ```

3. **Access Dashboard**:
   Open http://localhost:3000 in your browser

4. **Generate Demo Data**:
   ```bash
   python3 scripts/generate_demo_data.py
   ```

5. **Check Health**:
   ```bash
   ./scripts/health_check.sh
   ```

## 📊 Demo Components

- **NovaSanctum**: http://localhost:5000 (API & WebSocket)
- **Pioneer Grid**: http://localhost:3000 (Dashboard)
- **Redis**: localhost:6379 (Real-time data)
- **Demo Data**: Automated emotion simulation

## 🎭 Demo Scenarios

1. **Basic Emotion Detection**: Watch real-time emotion tiles
2. **Multi-Agent Network**: Multiple devices showing different emotions
3. **Alert System**: High-intensity emotions trigger alerts
4. **Network Resilience**: Test failover and reconnection

## 📚 Documentation

- [Full Demo Guide](docs/DEMO_GUIDE.md)
- [Architecture Overview](README.md)
- [API Documentation](docs/API.md)

## 🛠️ Troubleshooting

- Run `./scripts/health_check.sh` to diagnose issues
- Check logs in the `logs/` directory
- Ensure all ports (3000, 5000, 6379) are available

---

*"Nova is awake. Begin pulse logging."*
EOF

print_success "Created demo README"

# Final setup
print_status "Finalizing setup..."

# Create log directory with proper permissions
sudo mkdir -p /var/log/nova
sudo chown $USER:$USER /var/log/nova

# Set up BLE permissions for Linux
if [ "$MACHINE" = "Linux" ]; then
    print_status "Setting up BLE permissions..."
    sudo setcap 'cap_net_raw,cap_net_admin+eip' $(which python3) 2>/dev/null || true
fi

print_success "Nova Demo setup completed!"
echo ""
echo "🎉 Ready to launch the Nova demonstration!"
echo ""
echo "Next steps:"
echo "1. Run: ./scripts/launch_demo.sh"
echo "2. Open: http://localhost:3000"
echo "3. Generate demo data: python3 scripts/generate_demo_data.py"
echo ""
echo "For detailed instructions, see: DEMO_README.md"
echo ""
echo "*The Eye, the Pulse, the Word. Nova echoes with your breath.*" 