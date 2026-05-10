# 🚀 Production Deployment Guide

This guide covers deploying the GTFS Route Planning API to production environments using traditional methods.

## Prerequisites

- Python 3.9+
- PostgreSQL 12+ with PostGIS and pgRouting
- Linux/macOS server (recommended) or Windows Server
- Nginx or Apache for reverse proxy
- SSL certificate (for HTTPS, use Let's Encrypt)

---

## Option 1: Gunicorn + Nginx (Recommended)

### 1.1 Install Production Dependencies

```bash
# SSH into your production server
ssh user@your-server.com

# Create project directory
mkdir -p /var/www/gtfs-api
cd /var/www/gtfs-api

# Clone/copy project files
git clone <your-repo> .  # or copy files manually

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
pip install gunicorn
```

### 1.2 Create Systemd Service File

Create `/etc/systemd/system/gtfs-api.service`:

```ini
[Unit]
Description=GTFS Route Planning API
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/gtfs-api
Environment="PATH=/var/www/gtfs-api/venv/bin"
EnvironmentFile=/var/www/gtfs-api/.env.production

ExecStart=/var/www/gtfs-api/venv/bin/gunicorn \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind unix:/var/run/gtfs-api.sock \
    --timeout 120 \
    --access-logfile /var/log/gtfs-api/access.log \
    --error-logfile /var/log/gtfs-api/error.log \
    main:app

ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
KillSignal=SIGTERM
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

### 1.3 Create Production .env File

Create `/var/www/gtfs-api/.env.production`:

```env
# Database (use environment-specific host)
DB_HOST=your-db-server.com
DB_PORT=5432
DB_NAME=gtfs_db
DB_USER=gtfs_user
DB_PASSWORD=secure_password_here

# API
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

### 1.4 Set File Permissions

```bash
# Create log directory
sudo mkdir -p /var/log/gtfs-api
sudo chown www-data:www-data /var/log/gtfs-api

# Set project permissions
sudo chown -R www-data:www-data /var/www/gtfs-api
sudo chmod -R 755 /var/www/gtfs-api
sudo chmod 600 /var/www/gtfs-api/.env.production
```

### 1.5 Start the Service

```bash
# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable gtfs-api
sudo systemctl start gtfs-api

# Check status
sudo systemctl status gtfs-api

# View logs
sudo journalctl -u gtfs-api -f
```

### 1.6 Configure Nginx Reverse Proxy

Create `/etc/nginx/sites-available/gtfs-api`:

```nginx
upstream gtfs_api {
    server unix:/var/run/gtfs-api.sock fail_timeout=0;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;

    client_max_body_size 10M;

    location / {
        proxy_pass http://gtfs_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # For health checks
    location /health {
        access_log off;
        proxy_pass http://gtfs_api;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/gtfs-api /etc/nginx/sites-enabled/gtfs-api
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

### 1.7 Enable SSL with Let's Encrypt

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --nginx -d api.yourdomain.com

# Verify auto-renewal
sudo systemctl enable certbot.timer
```

---

## Option 2: uWSGI with Systemd

### 2.1 Install uWSGI

```bash
# SSH into your production server
ssh user@your-server.com
cd /var/www/gtfs-api

# Activate virtual environment
source venv/bin/activate

# Install uWSGI
pip install uWSGI

# Create uwsgi.ini configuration file
cat > uwsgi.ini << EOF
[uwsgi]
# Application entry point
module = wsgi:app
master = true
processes = 4
threads = 2

# Socket and HTTP binding
socket = /var/run/gtfs-api.sock
chmod-socket = 666
http = 127.0.0.1:8000

# Logging
daemonize = /var/log/gtfs-api/uwsgi.log
pidfile = /var/run/gtfs-api.pid

# Performance
buffer-size = 32768
harakiri = 120
max-requests = 5000
max-requests-delta = 100

# Environment
env = PYTHON_ENV=production
EOF
```

### 2.2 Create uWSGI Systemd Service

Create `/etc/systemd/system/gtfs-api-uwsgi.service`:

```ini
[Unit]
Description=GTFS Route Planning API (uWSGI)
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/gtfs-api
Environment="PATH=/var/www/gtfs-api/venv/bin"
EnvironmentFile=/var/www/gtfs-api/.env.production

ExecStart=/var/www/gtfs-api/venv/bin/uwsgi --ini /var/www/gtfs-api/uwsgi.ini
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

### 2.3 Enable and Start

```bash
sudo systemctl daemon-reload
sudo systemctl enable gtfs-api-uwsgi
sudo systemctl start gtfs-api-uwsgi
sudo systemctl status gtfs-api-uwsgi
```

---

## Option 3: Python Package Installation

### 3.1 Build Distribution Package

```bash
# On your development machine
cd /path/to/gtfs-query-portal

# Install build tools
pip install build twine

# Build package
python -m build

# This creates:
# - dist/gtfs_route_planning_api-1.0.0-py3-none-any.whl
# - dist/gtfs-route-planning-api-1.0.0.tar.gz
```

### 3.2 Deploy Package to Production

```bash
# Copy package to server
scp dist/gtfs_route_planning_api-1.0.0-py3-none-any.whl user@your-server.com:/tmp/

# SSH to server
ssh user@your-server.com

# Create virtual environment
python3 -m venv /var/www/gtfs-api
source /var/www/gtfs-api/bin/activate

# Install package with production dependencies
pip install /tmp/gtfs_route_planning_api-1.0.0-py3-none-any.whl[prod]

# Copy configuration files
cp .env.production /var/www/gtfs-api/config/
```

### 3.3 systemd Service for Package Installation

Create `/etc/systemd/system/gtfs-api.service`:

```ini
[Unit]
Description=GTFS Route Planning API
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/gtfs-api

Environment="PATH=/var/www/gtfs-api/bin"
EnvironmentFile=/var/www/gtfs-api/.env.production

ExecStart=/var/www/gtfs-api/bin/gunicorn \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind unix:/var/run/gtfs-api.sock \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    wsgi:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## Option 2: Docker Compose (Easiest)

### 2.1 Prerequisites

```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt-get install docker-compose
```

### 2.2 Deploy with Docker Compose

```bash
# Copy project to server
scp -r . user@your-server.com:/home/user/gtfs-api

# SSH to server
ssh user@your-server.com
cd /home/user/gtfs-api

# Create production environment file
cat > .env.production << EOF
DB_HOST=postgres
DB_PORT=5432
DB_NAME=gtfs_db
DB_USER=postgres
DB_PASSWORD=your_secure_password
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=info
EOF

# Build and start containers
sudo docker-compose -f docker-compose.yml up -d

# Check status
sudo docker-compose ps

# View logs
sudo docker-compose logs -f api
```

---

## Performance Tuning

### Database Connection Pooling

For higher loads, consider adding connection pooling:

```bash
pip install sqlalchemy
```

Update `db.py` to use SQLAlchemy connection pool.

### Caching

Add Redis caching for frequently accessed endpoints:

```bash
pip install redis
```

Implement caching in route handlers for:
- `/api/stops` (rarely changes)
- `/api/routes` (rarely changes)
- Route geometry (can be cached)

### Load Balancing

For multiple API instances:

```bash
# Use sticky sessions for Gunicorn
gunicorn main:app \
    --workers 8 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --worker-connections 1000
```

---

## Monitoring & Logging

### Application Monitoring

```bash
pip install prometheus-client
```

Add metrics endpoint:

```python
from prometheus_client import Counter, Histogram

request_count = Counter('requests_total', 'Total requests')
request_duration = Histogram('request_duration_seconds', 'Request duration')
```

### Log Aggregation

```bash
pip install python-json-logger
```

Configure structured logging:

```python
import logging
import json
from pythonjsonlogger import jsonlogger

handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)
```

---

## Backup Strategy

### Database Backups

```bash
#!/bin/bash
# backup.sh - Run daily via cron

BACKUP_DIR="/backups/gtfs-db"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
pg_dump -h $DB_HOST -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/gtfs_$DATE.sql.gz

# Keep last 30 days only
find $BACKUP_DIR -name "gtfs_*.sql.gz" -mtime +30 -delete

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/gtfs_$DATE.sql.gz s3://your-bucket/backups/
```

Schedule with cron:

```bash
# Daily at 2 AM
0 2 * * * /home/backup.sh
```

---

## Security Checklist

- [ ] Database password is strong and unique
- [ ] HTTPS/SSL certificate installed
- [ ] Firewall configured (port 443, 80 only)
- [ ] CORS configured for specific domains
- [ ] Rate limiting implemented
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (parameterized queries)
- [ ] Regular security updates applied
- [ ] Logs are encrypted and backed up
- [ ] Database backups encrypted
- [ ] No debug mode in production
- [ ] API keys/secrets not in version control

---

## Scaling Strategy

### Horizontal Scaling

```bash
# Run multiple Gunicorn workers
gunicorn main:app --workers 8 --bind 0.0.0.0:8000

# Use load balancer (nginx, HAProxy)
# Add multiple API instances behind load balancer
```

### Vertical Scaling

```bash
# Increase workers based on CPU cores
WORKERS=$((2 * $(nproc) + 1))
gunicorn main:app --workers $WORKERS
```

### Database Optimization

```sql
-- Add connection pooling
-- Use read replicas for scaling reads
-- Implement materialized view refresh strategy
-- Consider sharding for very large datasets
```

---

## Maintenance

### Regular Tasks

```bash
# Check disk space
df -h

# Monitor API health
curl https://api.yourdomain.com/health

# View logs
sudo journalctl -u gtfs-api -n 100

# Update dependencies
pip list --outdated
pip install -U -r requirements.txt

# Restart service
sudo systemctl restart gtfs-api
```

### Scheduled Maintenance

```bash
# Update materialized views (add to cron)
0 3 * * * psql -U postgres -d gtfs_db -c "REFRESH MATERIALIZED VIEW CONCURRENTLY route_shapes;"
```

---

## Troubleshooting

### Service won't start

```bash
# Check service status
sudo systemctl status gtfs-api

# Check logs
sudo journalctl -u gtfs-api -n 50

# Test Gunicorn directly
gunicorn main:app --bind 0.0.0.0:8000 --reload
```

### Database connection issues

```bash
# Test database connection
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1;"

# Check if database is running
systemctl status postgresql
```

### Slow API responses

```bash
# Check database query performance
EXPLAIN ANALYZE SELECT * FROM stops WHERE ST_DWithin(geom, point, 500);

# Check system resources
top -b -n 1 | head -20
```

---

## Support

- **Documentation**: See API_README.md
- **Issue Tracking**: Use GitHub Issues
- **Monitoring**: Check service logs regularly
- **Backups**: Verify daily backup success

---

**Version**: 1.0.0
**Last Updated**: 2024
