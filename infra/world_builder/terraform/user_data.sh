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
sudo dnf install -y python3-pip git
if [ $? -eq 0 ]; then
    echo "Required packages installed successfully"
else
    echo "Error installing required packages"
    exit 1
fi

# Create app directory
APP_DIR="/opt/world-builder"
echo "Creating application directory: $APP_DIR"
sudo mkdir -p $APP_DIR
sudo chown ec2-user:ec2-user $APP_DIR
cd $APP_DIR
echo "Changed to directory: $(pwd)"

# Set up Python environment
echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
echo "Python version: $(python3 --version)"
echo "Pip version: $(pip --version)"

# Install dependencies
echo "Installing pip and poetry..."
pip install --upgrade pip
pip install poetry
echo "Poetry version: $(poetry --version)"


echo "Fresh clone of repository..."
git clone https://github.com/BenjaminHelyer/data-worldgen
echo "Repository cloned successfully"

echo "Going into the repository..."
cd data-worldgen
echo "Changed to directory: $(pwd)"

echo "Installing project dependencies with poetry..."
poetry install

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
ExecStart=$APP_DIR/venv/bin/python custom_wb.py
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
echo "- Poetry version: $(poetry --version)"
echo "- Service status: $(sudo systemctl is-active world-builder)"
echo "- Python version: $(python3 --version)"