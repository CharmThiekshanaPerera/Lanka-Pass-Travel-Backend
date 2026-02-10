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

### Setup SSL Certificates First
```bash
# Create SSL directories
sudo mkdir -p ./ssl/certs ./ssl/private

# Generate self-signed certificate (for testing)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ./ssl/private/self-signed.key \
  -out ./ssl/certs/self-signed.crt \
  -subj "/C=LK/ST=Western/L=Colombo/O=TravelApp/CN=13.212.50.145"

# For Let's Encrypt (production with domain)
# sudo certbot certonly --standalone -d api.lankapasstravel.com
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

### Test with Self-Signed Certificate
```bash
# From local machine (ignore certificate warning)
curl -k https://13.212.50.145/docs
curl -k https://13.212.50.145/api/v1/health

# View certificate details
echo | openssl s_client -connect 13.212.50.145:443 -servername 13.212.50.145
```

### Test with Valid Certificate (After Domain Setup)
```bash
# No -k flag needed for Let's Encrypt certificates
curl https://api.lankapasstravel.com/docs
curl https://api.lankapasstravel.com/api/v1/health
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
# Verify SSL directory structure
ls -la ./ssl/
ls -la ./ssl/certs/
ls -la ./ssl/private/

# Regenerate certificates if missing
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ./ssl/private/self-signed.key \
  -out ./ssl/certs/self-signed.crt \
  -subj "/C=LK/ST=Western/L=Colombo/O=TravelApp/CN=13.212.50.145"
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
