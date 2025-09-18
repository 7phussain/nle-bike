#!/bin/bash

# NLE Bike - Setup Script
# Author: MiniMax Agent

echo "🚀 Setting up NLE Bike Drop Shipping Site..."

# Create project structure
echo "📁 Creating project directories..."
mkdir -p data logs static/images static/css static/js

# Setup Python virtual environment
echo "🐍 Setting up Python environment..."
if command -v python3 &> /dev/null; then
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ Virtual environment created"
else
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
cd backend
pip install -r requirements.txt
echo "✅ Python dependencies installed"
cd ..

# Install Node.js dependencies (if needed)
if command -v npm &> /dev/null; then
    echo "📦 Installing Node.js dependencies..."
    npm init -y
    npm install --save-dev live-server
    echo "✅ Node.js dependencies installed"
fi

# Setup database
echo "🗄️ Initializing database..."
python3 backend/inventory_manager.py &
SCRAPER_PID=$!
sleep 5
kill $SCRAPER_PID
echo "✅ Database initialized"

# Setup systemd service (optional)
if command -v systemctl &> /dev/null; then
    echo "⚙️ Setting up systemd service..."
    sudo tee /etc/systemd/system/electroride-pro.service > /dev/null <<EOF
[Unit]
Description=NLE Bike API Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)/backend
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python api_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    echo "✅ Systemd service created (run 'sudo systemctl enable electroride-pro' to enable)"
fi

# Create environment file
echo "📝 Creating environment configuration..."
cat > .env <<EOF
# NLE Bike Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
DATABASE_PATH=data/inventory.db
LOG_LEVEL=INFO
SYNC_INTERVAL_MINUTES=30
SOURCE_SITE_URL=https://engwe.com/
APP_NAME=NLE Bike
APP_VERSION=1.0.0
EOF

echo "✅ Environment configuration created"

# Create start script
echo "📝 Creating start script..."
cat > start.sh <<EOF
#!/bin/bash
echo "Starting NLE Bike..."
source venv/bin/activate
cd backend
python api_server.py
EOF
chmod +x start.sh

# Create development script
cat > dev.sh <<EOF
#!/bin/bash
echo "Starting NLE Bike in development mode..."
source venv/bin/activate

# Start API server in background
cd backend
python api_server.py &
API_PID=\$!

# Start inventory manager in background
python inventory_manager.py &
INVENTORY_PID=\$!

echo "API Server PID: \$API_PID"
echo "Inventory Manager PID: \$INVENTORY_PID"
echo "Access the site at: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo "Press Ctrl+C to stop..."

# Wait for user interrupt
trap "echo 'Stopping services...'; kill \$API_PID \$INVENTORY_PID; exit" INT
wait
EOF
chmod +x dev.sh

echo "✅ Start scripts created"

echo ""
echo "🎉 NLE Bike setup complete!"
echo ""
echo "To start the application:"
echo "  Development mode: ./dev.sh"
echo "  Production mode: ./start.sh"
echo ""
echo "URLs:"
echo "  Website: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  Admin Panel: http://localhost:8000/api/inventory/stats"
echo ""
echo "Features:"
echo "  ✅ Modern responsive design"
echo "  ✅ Automated inventory sync from ENGWE"
echo "  ✅ Real-time price monitoring"
echo "  ✅ RESTful API"
echo "  ✅ Dark/Light theme support"
echo "  ✅ Mobile-first design"
echo "  ✅ Advanced search and filtering"
echo "  ✅ Product recommendations"
echo "  ✅ Cart and checkout system"
echo "  ✅ Automated background tasks"
echo ""
echo "Happy drop shipping! 🚀"