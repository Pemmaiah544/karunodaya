#!/bin/bash
# Deployment script for Karunodaya Platform on Hetzner

set -e  # Exit on error

echo "🚀 Starting Karunodaya deployment..."

# Navigate to app directory
cd /home/karunodaya/app

# Pull latest changes from git
echo "📥 Pulling latest code from git..."
git pull origin main

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt --no-cache-dir

# Run database migrations
echo "🗄️ Running database migrations..."
python manage.py migrate --noinput --settings=karunodaya_project.settings_production

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear --settings=karunodaya_project.settings_production

# Create necessary directories
echo "📂 Creating log and media directories..."
mkdir -p /var/log/karunodaya
mkdir -p mediafiles/book_covers
mkdir -p mediafiles/generated_reports
mkdir -p logs

# Set proper permissions
echo "🔐 Setting file permissions..."
chown -R karunodaya:www-data /home/karunodaya/app
chmod -R 755 /home/karunodaya/app
chmod -R 775 mediafiles
chmod -R 775 logs

# Restart Gunicorn service
echo "🔄 Restarting Gunicorn..."
sudo systemctl restart karunodaya

# Restart Nginx
echo "🔄 Restarting Nginx..."
sudo systemctl reload nginx

# Check service status
echo "✅ Checking service status..."
sudo systemctl status karunodaya --no-pager

echo "✅ Deployment complete!"
echo "📊 View logs: sudo journalctl -u karunodaya -f"
