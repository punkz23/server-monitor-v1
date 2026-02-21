#!/bin/bash

# Define the service name
SERVICE_NAME="serverwatch-backend"
SERVICE_FILE="/home/ic1/projects/server-monitor-v1/serverwatch-backend.service"

echo "🔧 Setting up $SERVICE_NAME service..."

# Copy service file to systemd
if [ -f "$SERVICE_FILE" ]; then
    sudo cp "$SERVICE_FILE" /etc/systemd/system/
    echo "✅ Service file copied to /etc/systemd/system/"
else
    echo "❌ Service file not found at $SERVICE_FILE"
    exit 1
fi

# Reload systemd
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

# Enable the service
echo "🚀 Enabling $SERVICE_NAME..."
sudo systemctl enable $SERVICE_NAME

# Start the service
echo "▶️ Starting $SERVICE_NAME..."
sudo systemctl start $SERVICE_NAME

# Check status
echo "📊 Service status:"
sudo systemctl status $SERVICE_NAME --no-pager

echo ""
echo "🎉 Setup complete! The server will now start automatically on boot and restart if it crashes."
echo "   Use 'sudo systemctl stop $SERVICE_NAME' to stop it."
echo "   Use 'sudo systemctl start $SERVICE_NAME' to start it."
echo "   Use 'sudo systemctl restart $SERVICE_NAME' to restart it."
echo "   Use 'journalctl -u $SERVICE_NAME -f' to view logs."
