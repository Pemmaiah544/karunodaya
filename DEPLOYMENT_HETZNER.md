# Karunodaya Platform - Hetzner Deployment Guide

Complete guide for deploying the Karunodaya Digital Platform on a Hetzner server.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Application Deployment](#application-deployment)
4. [SSL Certificate Setup](#ssl-certificate-setup)
5. [Service Configuration](#service-configuration)
6. [Post-Deployment Tasks](#post-deployment-tasks)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Hetzner Server Requirements
- **Server**: Cloud Server (CX11 or higher recommended)
- **OS**: Ubuntu 22.04 LTS (recommended)
- **RAM**: Minimum 2GB (4GB recommended)
- **Storage**: Minimum 20GB
- **Domain**: Registered domain pointing to server IP

### Before Starting
- [ ] Hetzner server provisioned
- [ ] SSH access configured
- [ ] Domain DNS configured (A record pointing to server IP)
- [ ] Razorpay account setup (production keys)
- [ ] Email SMTP credentials (optional but recommended)

---

## Server Setup

### Step 1: Initial Server Configuration

```bash
# SSH into your Hetzner server
ssh root@your-server-ip

# Update system packages
apt update && apt upgrade -y

# Set hostname
hostnamectl set-hostname karunodaya

# Create deployment user
adduser karunodaya
usermod -aG sudo karunodaya

# Setup SSH key for karunodaya user (optional but recommended)
su - karunodaya
mkdir -p ~/.ssh
chmod 700 ~/.ssh
# Copy your public key to ~/.ssh/authorized_keys
```

### Step 2: Install Required Software

```bash
# Install Python and dependencies
sudo apt install -y python3.10 python3.10-venv python3-pip python3-dev

# Install Nginx
sudo apt install -y nginx

# Install Git
sudo apt install -y git

# Install certbot for SSL
sudo apt install -y certbot python3-certbot-nginx

# Install build essentials for compiling Python packages
sudo apt install -y build-essential libssl-dev libffi-dev

# Install SQLite (already included in Ubuntu)
sudo apt install -y sqlite3
```

### Step 3: Configure Firewall

```bash
# Allow OpenSSH
sudo ufw allow OpenSSH

# Allow HTTP and HTTPS
sudo ufw allow 'Nginx Full'

# Enable firewall
sudo ufw enable
sudo ufw status
```

---

## Application Deployment

### Step 1: Clone Repository

```bash
# Switch to karunodaya user
su - karunodaya

# Create app directory
mkdir -p /home/karunodaya/app
cd /home/karunodaya/app

# Clone your repository
git clone https://github.com/yourusername/karunodaya.git .

# Or use your Hetzner server's IP to pull
# git clone git@your-git-server:karunodaya.git .
```

### Step 2: Setup Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

```bash
# Create .env file
nano .env

# Add the following (replace with your actual values):
```

```env
# Django Settings - PRODUCTION
SECRET_KEY=your-long-random-secret-key-min-50-characters
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,your-server-ip

# Security Settings
SECURE_SSL_REDIRECT=True
CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Razorpay Configuration (Live Mode)
RAZORPAY_KEY_ID=rzp_live_your_key_id
RAZORPAY_KEY_SECRET=your_live_secret_key
RAZORPAY_WEBHOOK_SECRET=your_live_webhook_secret

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@your-domain.com
ADMIN_EMAIL=admin@your-domain.com
```

**Generate SECRET_KEY:**
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### Step 4: Database Setup

```bash
# Run migrations
python manage.py migrate --settings=karunodaya_project.settings_production

# Create superuser
python manage.py createsuperuser --settings=karunodaya_project.settings_production

# Seed initial data (optional)
python manage.py seed_data --settings=karunodaya_project.settings_production
```

### Step 5: Collect Static Files

```bash
# Create directories
mkdir -p /home/karunodaya/app/staticfiles
mkdir -p /home/karunodaya/app/mediafiles
mkdir -p /home/karunodaya/app/logs
mkdir -p /var/log/karunodaya

# Collect static files
python manage.py collectstatic --noinput --settings=karunodaya_project.settings_production

# Set permissions
chmod -R 775 /home/karunodaya/app/mediafiles
chmod -R 775 /home/karunodaya/app/logs
sudo chown -R karunodaya:www-data /home/karunodaya/app
```

---

## SSL Certificate Setup

### Using Let's Encrypt (Free SSL)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Follow the prompts:
# - Enter your email
# - Agree to terms
# - Choose redirect (option 2)

# Test auto-renewal
sudo certbot renew --dry-run

# Auto-renewal is configured automatically via systemd timer
```

---

## Service Configuration

### Step 1: Configure Gunicorn

```bash
# Edit gunicorn_config.py and update paths if needed
nano /home/karunodaya/app/gunicorn_config.py

# Test Gunicorn
cd /home/karunodaya/app
source venv/bin/activate
gunicorn --config gunicorn_config.py karunodaya_project.wsgi:application

# If successful, press Ctrl+C to stop
```

### Step 2: Setup Systemd Service

```bash
# Copy service file
sudo cp /home/karunodaya/app/deployment/karunodaya.service /etc/systemd/system/

# Create run directory
sudo mkdir -p /var/run/karunodaya
sudo chown karunodaya:www-data /var/run/karunodaya

# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable karunodaya

# Start service
sudo systemctl start karunodaya

# Check status
sudo systemctl status karunodaya

# View logs
sudo journalctl -u karunodaya -f
```

### Step 3: Configure Nginx

```bash
# Copy nginx configuration
sudo cp /home/karunodaya/app/deployment/nginx_karunodaya.conf /etc/nginx/sites-available/karunodaya

# Edit configuration and replace placeholders
sudo nano /etc/nginx/sites-available/karunodaya
# Replace: your-domain.com with your actual domain

# Create symbolic link
sudo ln -s /etc/nginx/sites-available/karunodaya /etc/nginx/sites-enabled/

# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### Step 4: Setup Cron Jobs

```bash
# Edit crontab
crontab -e

# Add the following lines:
# Check for overdue subscriptions daily at 2 AM
0 2 * * * cd /home/karunodaya/app && /home/karunodaya/app/venv/bin/python manage.py check_overdue_subscriptions >> /var/log/karunodaya/cron.log 2>&1

# Cleanup old sessions weekly on Sunday at 3 AM
0 3 * * 0 cd /home/karunodaya/app && /home/karunodaya/app/venv/bin/python manage.py clearsessions >> /var/log/karunodaya/cron.log 2>&1

# Backup database daily at 1 AM
0 1 * * * /home/karunodaya/app/deployment/backup_database.sh >> /var/log/karunodaya/backup.log 2>&1
```

### Step 5: Setup Backup Script

```bash
# Make backup script executable
chmod +x /home/karunodaya/app/deployment/backup_database.sh

# Create backup directory
mkdir -p /home/karunodaya/backups

# Test backup script
/home/karunodaya/app/deployment/backup_database.sh
```

---

## Post-Deployment Tasks

### 1. Test the Application

```bash
# Check if services are running
sudo systemctl status karunodaya
sudo systemctl status nginx

# Test URLs
curl http://your-domain.com  # Should redirect to HTTPS
curl https://your-domain.com  # Should return HTML

# Test admin
# Visit: https://your-domain.com/admin/
```

### 2. Configure Razorpay Webhooks

1. Login to Razorpay Dashboard
2. Go to Settings → Webhooks
3. Add webhook URL: `https://your-domain.com/payments/webhook/`
4. Select events: `payment.captured`, `payment.failed`
5. Copy webhook secret and update in `.env`

### 3. Initial Data Setup

```bash
# Create subscription plans via admin
# Visit: https://your-domain.com/admin/orders/subscriptionplan/

# Add publishers
# Visit: https://your-domain.com/admin/catalog/publisher/

# Add books
# Visit: https://your-domain.com/admin/catalog/book/

# Or use seed data command (for testing)
python manage.py seed_data --settings=karunodaya_project.settings_production
```

### 4. Security Checklist

- [ ] SECRET_KEY is 50+ random characters
- [ ] DEBUG=False in production
- [ ] ALLOWED_HOSTS configured correctly
- [ ] SSL certificate installed and working
- [ ] Firewall configured (UFW)
- [ ] Database file permissions correct (640)
- [ ] Nginx security headers configured
- [ ] Razorpay webhook secret configured
- [ ] Admin password is strong
- [ ] Regular backups configured

---

## Monitoring & Maintenance

### Log Files

```bash
# Application logs
sudo journalctl -u karunodaya -f

# Nginx access logs
sudo tail -f /var/log/nginx/karunodaya_access.log

# Nginx error logs
sudo tail -f /var/log/nginx/karunodaya_error.log

# Gunicorn logs
sudo tail -f /var/log/karunodaya/gunicorn_error.log

# Cron logs
tail -f /var/log/karunodaya/cron.log

# Backup logs
tail -f /var/log/karunodaya/backup.log
```

### Deployment Script

For future deployments, use the deployment script:

```bash
# Make script executable (first time)
chmod +x /home/karunodaya/app/deployment/deploy.sh

# Run deployment
sudo /home/karunodaya/app/deployment/deploy.sh
```

### Database Backups

```bash
# Manual backup
/home/karunodaya/app/deployment/backup_database.sh

# View backups
ls -lh /home/karunodaya/backups/

# Restore from backup
cd /home/karunodaya/app
sudo systemctl stop karunodaya
cp /home/karunodaya/backups/karunodaya_backup_YYYYMMDD_HHMMSS.sqlite3.gz .
gunzip karunodaya_backup_YYYYMMDD_HHMMSS.sqlite3.gz
mv production_db.sqlite3 production_db.sqlite3.old
mv karunodaya_backup_YYYYMMDD_HHMMSS.sqlite3 production_db.sqlite3
sudo systemctl start karunodaya
```

### Server Monitoring

```bash
# Check disk space
df -h

# Check memory usage
free -h

# Check CPU usage
top

# Check running processes
ps aux | grep gunicorn

# Check open files
lsof -i :8000
lsof -i :443
```

---

## Troubleshooting

### Issue: Service won't start

```bash
# Check service status
sudo systemctl status karunodaya

# Check logs
sudo journalctl -u karunodaya -n 50

# Common fixes:
# 1. Check .env file exists and has correct values
# 2. Check virtual environment path in service file
# 3. Check file permissions
# 4. Check gunicorn is installed in venv
```

### Issue: 502 Bad Gateway

```bash
# Check Gunicorn is running
sudo systemctl status karunodaya

# Check Gunicorn port
sudo lsof -i :8000

# Check nginx error logs
sudo tail -f /var/log/nginx/karunodaya_error.log

# Restart services
sudo systemctl restart karunodaya
sudo systemctl reload nginx
```

### Issue: Static files not loading

```bash
# Collect static files again
cd /home/karunodaya/app
source venv/bin/activate
python manage.py collectstatic --noinput --settings=karunodaya_project.settings_production

# Check permissions
ls -la /home/karunodaya/app/staticfiles/

# Check nginx configuration
sudo nginx -t
```

### Issue: Database locked

```bash
# Stop service
sudo systemctl stop karunodaya

# Check for lingering processes
ps aux | grep gunicorn
kill -9 <PID>  # if needed

# Start service
sudo systemctl start karunodaya
```

### Issue: SSL certificate issues

```bash
# Renew certificate manually
sudo certbot renew

# Check certificate status
sudo certbot certificates

# Test SSL
curl -I https://your-domain.com
```

---

## Performance Optimization

### 1. Enable Gzip Compression (Nginx)

Add to nginx configuration:

```nginx
gzip on;
gzip_vary on;
gzip_proxied any;
gzip_comp_level 6;
gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss;
```

### 2. Enable Caching (Optional - Redis)

```bash
# Install Redis
sudo apt install redis-server

# Uncomment cache settings in settings_production.py
# pip install django-redis
```

### 3. Database Optimization

```bash
# Run Django check for optimization suggestions
python manage.py check --deploy --settings=karunodaya_project.settings_production
```

---

## Useful Commands

```bash
# Restart application
sudo systemctl restart karunodaya

# View application logs
sudo journalctl -u karunodaya -f

# Check Django migrations
python manage.py showmigrations --settings=karunodaya_project.settings_production

# Create new superuser
python manage.py createsuperuser --settings=karunodaya_project.settings_production

# Django shell (production)
python manage.py shell --settings=karunodaya_project.settings_production

# Run management command
python manage.py check_overdue_subscriptions --settings=karunodaya_project.settings_production

# Update code and deploy
cd /home/karunodaya/app
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --settings=karunodaya_project.settings_production
python manage.py collectstatic --noinput --settings=karunodaya_project.settings_production
sudo systemctl restart karunodaya
```

---

## Security Best Practices

1. **Regular Updates**: Keep system packages updated
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Fail2Ban**: Install fail2ban to prevent brute force attacks
   ```bash
   sudo apt install fail2ban
   ```

3. **SSH Key Authentication**: Disable password authentication
   ```bash
   sudo nano /etc/ssh/sshd_config
   # Set: PasswordAuthentication no
   sudo systemctl restart ssh
   ```

4. **Regular Backups**: Automate database backups to external storage

5. **Monitoring**: Setup monitoring tools like Uptime Robot or Sentry

---

## Support & Additional Resources

- **Django Documentation**: https://docs.djangoproject.com/
- **Nginx Documentation**: https://nginx.org/en/docs/
- **Let's Encrypt**: https://letsencrypt.org/docs/
- **Hetzner Docs**: https://docs.hetzner.com/

---

**Deployment Checklist**: Use `TESTING_CHECKLIST.md` for pre-deployment testing

**Last Updated**: Phase 9 - Deployment Prep
