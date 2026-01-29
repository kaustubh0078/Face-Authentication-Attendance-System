# Deployment Guide

## Prerequisites

- **Server:** Ubuntu 20.04+ / Windows Server
- **Python:** 3.8+
- **Node.js:** 18+
- **Domain:** (optional) for production
- **SSL Certificate:** (recommended) for HTTPS

---

## Local Development

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/face-auth-attendance.git
cd face-auth-attendance
```

### 2. Set Up Backend

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Create data directory
mkdir -p data/face_images
```

### 3. Set Up Frontend

```bash
cd frontend
npm install

# Create environment file
cp .env.example .env
cd ..
```

### 4. Run Development Servers

**Option A: Use START.bat (Windows)**
```bash
START.bat
```

**Option B: Manual Start**
```bash
# Terminal 1 - Backend
python api.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Access at: http://localhost:3000

---

## Production Deployment

### Option 1: Docker Deployment

#### 1. Create Dockerfile for Backend

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "api:app"]
```

#### 2. Create docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
    environment:
      - FLASK_ENV=production
      - DATABASE_PATH=/app/data/faces.db
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    environment:
      - VITE_API_URL=http://your-domain.com:5000
    depends_on:
      - backend
    restart: unless-stopped
```

#### 3. Deploy

```bash
docker-compose up -d
```

---

### Option 2: Traditional Server Deployment

#### Backend (Flask API)

**1. Install on Server**

```bash
# Clone repository
git clone https://github.com/yourusername/face-auth-attendance.git
cd face-auth-attendance

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn  # Production server
```

**2. Configure Environment**

```bash
cp .env.example .env
nano .env
```

Update for production:
```env
FLASK_ENV=production
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

**3. Create Systemd Service**

Create `/etc/systemd/system/faceauth-api.service`:

```ini
[Unit]
Description=Face Auth API
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/face-auth-attendance
Environment="PATH=/var/www/face-auth-attendance/venv/bin"
ExecStart=/var/www/face-auth-attendance/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 api:app

[Install]
WantedBy=multi-user.target
```

**4. Start Service**

```bash
sudo systemctl daemon-reload
sudo systemctl enable faceauth-api
sudo systemctl start faceauth-api
```

#### Frontend (React)

**1. Build for Production**

```bash
cd frontend
npm install
npm run build
```

**2. Serve with Nginx**

Install Nginx:
```bash
sudo apt install nginx
```

Create `/etc/nginx/sites-available/faceauth`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    root /var/www/face-auth-attendance/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # API Proxy
    location /api {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

**3. Enable Site**

```bash
sudo ln -s /etc/nginx/sites-available/faceauth /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

**4. Add SSL (Let's Encrypt)**

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## Vercel Deployment (Frontend Only)

### 1. Build Configuration

Create `frontend/vercel.json`:

```json
{
  "rewrites": [
    { "source": "/api/(.*)", "destination": "https://your-backend-api.com/api/$1" },
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

### 2. Deploy

```bash
cd frontend
npm install -g vercel
vercel deploy --prod
```

### 3. Environment Variables

In Vercel dashboard, add:
```
VITE_API_URL=https://your-backend-api.com
```

---

## Render Deployment

### Backend (Web Service)

1. Connect GitHub repository
2. Select "Web Service"
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `gunicorn -w 4 -b 0.0.0.0:$PORT api:app`
5. Add environment variables from `.env.example`

### Frontend (Static Site)

1. Connect GitHub repository
2. Select "Static Site"
3. Build Command: `cd frontend && npm install && npm run build`
4. Publish Directory: `frontend/dist`
5. Add environment variable: `VITE_API_URL=<backend-url>`

---

## Railway Deployment

### 1. Backend

Create `railway.toml`:

```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "gunicorn -w 4 -b 0.0.0.0:$PORT api:app"
restartPolicyType = "ON_FAILURE"
```

### 2. Frontend

```toml
[build]
builder = "NIXPACKS"
buildCommand = "cd frontend && npm install && npm run build"

[deploy]
startCommand = "cd frontend && npm install -g serve && serve -s dist -l $PORT"
```

---

## Environment Variables Reference

### Backend (.env)

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | development/production | development |
| `FLASK_DEBUG` | Enable debug mode | True |
| `FLASK_HOST` | Host to bind | 0.0.0.0 |
| `FLASK_PORT` | Port to bind | 5000 |
| `DATABASE_PATH` | SQLite database path | data/faces.db |
| `RECOGNITION_THRESHOLD` | Face match threshold | 0.25 |

### Frontend (.env)

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | http://localhost:5000 |

---

## Post-Deployment Checklist

- [ ] Create admin user
- [ ] Test face registration
- [ ] Test face recognition
- [ ] Test attendance logging
- [ ] Check database backups
- [ ] Monitor logs
- [ ] Set up SSL certificate
- [ ] Configure CORS for production domain
- [ ] Test on mobile devices
- [ ] Set up monitoring (optional)

---

## Backup & Maintenance

### Database Backup

```bash
# Backup
cp data/faces.db backups/faces_$(date +%Y%m%d).db

# Restore
cp backups/faces_20260130.db data/faces.db
```

### Auto-backup Script

Create `backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/faceauth"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
cp data/faces.db $BACKUP_DIR/faces_$DATE.db

# Keep only last 30 days
find $BACKUP_DIR -name "faces_*.db" -mtime +30 -delete
```

Add to crontab:
```
0 2 * * * /var/www/face-auth-attendance/backup.sh
```

---

## Troubleshooting

### Backend won't start
```bash
# Check logs
sudo journalctl -u faceauth-api -f

# Common issues:
# - Port 5000 already in use
# - Missing dependencies
# - Database permissions
```

### Frontend 404 errors
```bash
# Check Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### Camera not working (HTTPS required)
- Must use HTTPS in production
- Get SSL certificate with Let's Encrypt
- Update CORS settings in Flask

### Performance issues
- Increase Gunicorn workers: `-w 8`
- Add Redis caching
- Use PostgreSQL instead of SQLite for >100 users

---

## Security Recommendations

1. **Use HTTPS** - Always use SSL in production
2. **Environment Variables** - Never commit `.env` files
3. **Database Backups** - Regular automated backups
4. **Rate Limiting** - Add Flask-Limiter for API
5. **Authentication** - Add user login for admin features
6. **CORS** - Restrict to your domain only
7. **Updates** - Keep dependencies updated
8. **Monitoring** - Set up error tracking (Sentry)

---

## Support

For issues, check:
- [GitHub Issues](https://github.com/yourusername/face-auth-attendance/issues)
- [Documentation](docs/DOCUMENTATION.md)
- Logs: `sudo journalctl -u faceauth-api -f`
