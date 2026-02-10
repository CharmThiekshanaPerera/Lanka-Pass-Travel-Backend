# Docker Instructions

## Build Image
```bash
docker build -t lanka-travel-backend .
```

## Run Container (Development - HTTP)
```bash
docker run --env-file .env -p 8000:8000 lanka-travel-backend
```

## Stop Container
```bash
docker ps
docker stop <container_id>
```

## Remove Container
```bash
docker rm <container_id>
```

## Docker Compose
### Development Mode (HTTP on Port 8000)
```bash
# Build and Start
docker compose up --build

# Start (No Rebuild)
docker compose up

# Stop and Remove
docker compose down

# Rebuild Only
docker compose build

# View Logs
docker compose logs -f

# View Specific Service Logs
docker compose logs -f api
docker compose logs -f nginx
```

## Production Mode (HTTPS on Port 443)
Use this when you want a public API behind Nginx with HTTPS.

### Default (Let's Encrypt in Docker)
The default configuration expects Let's Encrypt certificates on the host:
- `/etc/letsencrypt/live/api.lankapasstravel.com/fullchain.pem`
- `/etc/letsencrypt/live/api.lankapasstravel.com/privkey.pem`

Make sure `docker-compose.prod.yml` mounts `/etc/letsencrypt` and `nginx/nginx.conf` uses those paths.

### Setup SSL Certificates First
```bash
# Get Let's Encrypt certificate (requires domain)
# Stop Docker to free port 80
docker compose -f docker-compose.prod.yml down
sudo certbot certonly --standalone -d api.lankapasstravel.com
```

### Optional Fallback (Self-Signed on IP)
Use this only for temporary testing without a domain. You must switch the mounts
in `docker-compose.prod.yml` back to `/etc/ssl` and update `nginx/nginx.conf`.

```bash
# Create SSL directories
sudo mkdir -p ./ssl/certs ./ssl/private

# Generate self-signed certificate (for testing)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ./ssl/private/self-signed.key \
  -out ./ssl/certs/self-signed.crt \
  -subj "/C=LK/ST=Western/L=Colombo/O=TravelApp/CN=13.212.50.145"
```

### Switching Between Let's Encrypt and Self-Signed
Use this quick toggle when you need to switch certificate sources.

```text
Switch to Let's Encrypt (default)
1) nginx/nginx.conf:
   - ssl_certificate /etc/letsencrypt/live/api.lankapasstravel.com/fullchain.pem
   - ssl_certificate_key /etc/letsencrypt/live/api.lankapasstravel.com/privkey.pem
2) docker-compose.prod.yml:
   - enable: /etc/letsencrypt:/etc/letsencrypt:ro
   - disable: /etc/ssl/certs and /etc/ssl/private mounts

Switch to Self-Signed (temporary)
1) nginx/nginx.conf:
   - ssl_certificate /etc/ssl/certs/self-signed.crt
   - ssl_certificate_key /etc/ssl/private/self-signed.key
2) docker-compose.prod.yml:
   - enable: /etc/ssl/certs:/etc/ssl/certs:ro
   - enable: /etc/ssl/private:/etc/ssl/private:ro
   - disable: /etc/letsencrypt:/etc/letsencrypt:ro

Then restart:
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

### Build and Start
```bash
docker compose -f docker-compose.prod.yml up --build -d
```

### Start (No Rebuild)
```bash
docker compose -f docker-compose.prod.yml up -d
```

### Stop and Remove
```bash
docker compose -f docker-compose.prod.yml down
```

### View Logs
```bash
docker compose -f docker-compose.prod.yml logs -f
```

### Check Container Status
```bash
docker compose -f docker-compose.prod.yml ps
```

### Rebuild Only
```bash
docker compose -f docker-compose.prod.yml build
```

## HTTPS Testing

### Test with Valid Certificate (Default)
```bash
# No -k flag needed for Let's Encrypt certificates
curl https://api.lankapasstravel.com/docs
curl https://api.lankapasstravel.com/api/v1/health
```

### Test with Self-Signed Certificate (Optional)
```bash
# From local machine (ignore certificate warning)
curl -k https://13.212.50.145/docs
curl -k https://13.212.50.145/api/v1/health

# View certificate details
echo | openssl s_client -connect 13.212.50.145:443 -servername 13.212.50.145
```

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 80 or 443
sudo lsof -ti:80 | xargs kill -9
sudo lsof -ti:443 | xargs kill -9
```

### Certificate Not Found
```bash
# Verify Let's Encrypt certs on host
ls -la /etc/letsencrypt/live/api.lankapasstravel.com/

# Re-issue if missing
sudo certbot certonly --standalone -d api.lankapasstravel.com
```

### Nginx Configuration Error
```bash
# Test nginx config inside container
docker compose -f docker-compose.prod.yml exec nginx nginx -t
```

### API Not Responding
```bash
# Check if api container is running
docker compose -f docker-compose.prod.yml ps

# Check api logs
docker compose -f docker-compose.prod.yml logs api

# Check if port 8000 is open
docker compose -f docker-compose.prod.yml exec nginx netstat -tlnp | grep 8000
```
