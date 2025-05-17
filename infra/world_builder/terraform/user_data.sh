#!/bin/bash

# Enable logging
exec > >(tee /var/log/user-data.log) 2>&1

echo "Starting setup at $(date)"
echo "Running as user: $(whoami)"

# Update system packages
echo "Updating system packages..."
sudo dnf update -y
if [ $? -eq 0 ]; then
    echo "System packages updated successfully"
else
    echo "Error updating system packages"
    exit 1
fi

echo "Installing required packages..."
sudo dnf install -y git python3.11
if [ $? -eq 0 ]; then
    echo "Required packages installed successfully"
else
    echo "Error installing required packages"
    exit 1
fi

# Create app directory
APP_DIR="/opt/world-builder/data-worldgen"
echo "Creating application directory: $APP_DIR"
sudo mkdir -p $APP_DIR
sudo chown ec2-user:ec2-user $APP_DIR
cd $APP_DIR
echo "Changed to directory: $(pwd)"

# Set up Python environment
echo "Setting up Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate
echo "Python version: $(python --version)"
echo "Pip version: $(venv/bin/pip --version)"

echo "Fresh clone of repository..."
git clone https://github.com/BenjaminHelyer/data-worldgen
echo "Repository cloned successfully"

echo "Going into the repository..."
cd data-worldgen
echo "Changed to directory: $(pwd)"

# now that we have the repo, ensure that all project files are owned by the user
sudo chown -R ec2-user:ec2-user /opt/world-builder/data-worldgen

# this is not ideal but we just use editable mode for now
echo "Installing project dependencies with pip (editable mode)..."
pip install -e .

# Set up logging directory
echo "Setting up logging directory..."
sudo mkdir -p /var/log/world-builder
sudo touch /var/log/world-builder/app.log

# Create service user
echo "Creating service user..."
sudo useradd -r -s /bin/false world-builder

# Set permissions
echo "Setting permissions..."
sudo chown -R world-builder:world-builder $APP_DIR
sudo chown -R world-builder:world-builder /var/log/world-builder

# Set up systemd service
echo "Setting up systemd service..."
sudo tee /etc/systemd/system/world-builder.service << EOF
[Unit]
Description=World Builder Service
After=network.target

[Service]
Type=simple
User=world-builder
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin
ExecStart=$APP_DIR/venv/bin/python /opt/world-builder/data-worldgen/data-worldgen/examples/world_builder/wb_s3_example.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Set up logging rotation
echo "Setting up log rotation..."
sudo tee /etc/logrotate.d/world-builder << EOF
/var/log/world-builder/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 world-builder world-builder
}
EOF

# Install CloudWatch Agent
echo "Installing CloudWatch Agent..."
sudo dnf install -y amazon-cloudwatch-agent
if [ $? -eq 0 ]; then
    echo "CloudWatch Agent installed successfully"
else
    echo "Error installing CloudWatch Agent"
    # We don't exit here, as the main application might still function
fi

# Copy CloudWatch Agent config from repo example
echo "Copying CloudWatch Agent config from repo example..."
CLOUDWATCH_CONFIG_SRC="$APP_DIR/data-worldgen/examples/world_builder/wb_cloudwatch_agent.json"
CLOUDWATCH_CONFIG_DEST="/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json"
sudo mkdir -p /opt/aws/amazon-cloudwatch-agent/etc
sudo cp "$CLOUDWATCH_CONFIG_SRC" "$CLOUDWATCH_CONFIG_DEST"

# Start and enable CloudWatch Agent
echo "Starting CloudWatch Agent..."
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:$CLOUDWATCH_CONFIG_DEST -s
sudo systemctl enable amazon-cloudwatch-agent

# Start service
echo "Configuring and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable world-builder
sudo systemctl start world-builder

# Verify service status
echo "Checking service status..."
sudo systemctl status world-builder

echo "Setup completed at $(date)"
echo "Final system status:"
echo "- Service status: $(sudo systemctl is-active world-builder)"
echo "- Python version: $(python3.11 --version)"