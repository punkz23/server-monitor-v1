#!/bin/bash
set -e

# Configuration
USER_HOME=$HOME
AGENT_DIR="$USER_HOME/.serverwatch-agent"
SERVICE_NAME="serverwatch-agent"
SYSTEMD_USER_DIR="$USER_HOME/.config/systemd/user"

echo "Installing ServerWatch Agent (Lightweight) in user-space..."

# Detect operating system
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected Linux system"
    PKG_MANAGER="systemd"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS system"
    PKG_MANAGER="launchd"
else
    echo "Unknown operating system: $OSTYPE"
    exit 1
fi

# Validate prerequisites
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed"
    exit 1
fi

# Create agent directory
if [ -d "$AGENT_DIR" ]; then
    echo "Agent directory exists, updating..."
    # Keep logs if they exist
    rm -rf $AGENT_DIR
fi
mkdir -p $AGENT_DIR
cp serverwatch-agent.py $AGENT_DIR/
cp requirements.txt $AGENT_DIR/

# Create config directory
mkdir -p $USER_HOME/.config/serverwatch-agent
if [ -f "/tmp/serverwatch-agent/config.json" ]; then
    cp /tmp/serverwatch-agent/config.json $USER_HOME/.config/serverwatch-agent/
fi

# Create log directory
mkdir -p $USER_HOME/logs
touch $USER_HOME/logs/serverwatch-agent.log

# Make agent executable
chmod +x $AGENT_DIR/serverwatch-agent.py

echo "Setting up Python virtual environment and installing dependencies..."
if ! python3 -m venv $AGENT_DIR/venv; then
    echo "ERROR: Virtual environment creation failed. 'python3-venv' might be missing."
    echo "Please run 'sudo apt install python3.12-venv' (or appropriate version) on the remote server."
    echo "Then re-run the deployment."
    exit 1
fi

source $AGENT_DIR/venv/bin/activate
pip install -r $AGENT_DIR/requirements.txt
deactivate

# Platform-specific service setup
if [[ "$PKG_MANAGER" == "systemd" ]]; then
    echo "Setting up systemd user service..."
    mkdir -p $SYSTEMD_USER_DIR
    
    # Create user service file
    cat <<EOF > $SYSTEMD_USER_DIR/$SERVICE_NAME.service
[Unit]
Description=ServerWatch Agent
After=network.target

[Service]
Type=simple
WorkingDirectory=$AGENT_DIR
ExecStart=$AGENT_DIR/venv/bin/python $AGENT_DIR/serverwatch-agent.py --config $USER_HOME/.config/serverwatch-agent/config.json
Restart=always
RestartSec=10
StandardOutput=append:$USER_HOME/logs/serverwatch-agent.log
StandardError=append:$USER_HOME/logs/serverwatch-agent.log

[Install]
WantedBy=default.target
EOF

    systemctl --user daemon-reload
    systemctl --user enable $SERVICE_NAME
    echo "Service enabled. Start with: systemctl --user start $SERVICE_NAME"
else
    echo "Launchd setup not implemented yet"
    exit 1
fi

echo "Installation complete!"
echo "Configuration: $USER_HOME/.config/serverwatch-agent/config.json"
echo "Logs: $USER_HOME/logs/serverwatch-agent.log"
echo "Service: $SERVICE_NAME (User mode)"
