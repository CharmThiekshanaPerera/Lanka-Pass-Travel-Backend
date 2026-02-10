# EC2 API Check Guide

Use this guide to verify your backend APIs are running on EC2 with HTTPS and to list all endpoints.

## 1) Check Containers on EC2
```bash
docker ps
```

If you use the production compose:
```bash
docker compose -f docker-compose.prod.yml ps
```

Expected output (both should be "Up"):
```
CONTAINER ID   IMAGE                 STATUS
xxxxxxxx       api:latest            Up (healthy)
xxxxxxxx       nginx:1.25-alpine     Up (healthy)
```

## 2) Test Locally on EC2 (HTTPS with Self-Signed Certificate)
```bash
# Test HTTPS endpoint (ignore self-signed cert warning)
curl -k https://localhost/docs
curl -k https://localhost/openapi.json

# Test HTTP redirect (should redirect to HTTPS)
curl -L http://localhost/docs
```

## 3) Test From Your Local Machine (HTTPS)

### With Self-Signed Certificate (Testing)
```bash
# Ignore certificate warning
curl -k https://13.212.50.145/docs
curl -k https://13.212.50.145/openapi.json
curl -k https://13.212.50.145/api/v1/health
```

### With Valid Let's Encrypt Certificate (Production)
```bash
# No -k flag needed
curl https://api.lankapasstravel.com/docs
curl https://api.lankapasstravel.com/openapi.json
curl https://api.lankapasstravel.com/api/v1/health
```

## 4) Test API Endpoints

### Health Check
```bash
curl -k https://13.212.50.145/api/v1/health
```

### Vendor Registration
```bash
curl -k -X POST https://13.212.50.145/api/v1/vendors \
  -H "Content-Type: application/json" \
  -d '{"email":"vendor@example.com","password":"password123"}'
```

### Admin Login
```bash
curl -k -X POST https://13.212.50.145/api/v1/admin/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password123"}'
```

### List All Endpoints (from OpenAPI)
```bash
# Download OpenAPI spec
curl -sk https://13.212.50.145/openapi.json > openapi.json

# Parse and display all endpoints
python3 - <<'PY'
import json
with open("openapi.json", "r", encoding="utf-8") as f:
    data = json.load(f)
for path in sorted(data.get("paths", {})):
    methods = list(data["paths"][path].keys())
    print(f"{path}: {', '.join(methods)}")
PY
```

## 5) Test Certificate Installation

### View Self-Signed Certificate Details
```bash
# Check certificate paths
sudo ls -la /etc/ssl/certs/self-signed.crt
sudo ls -la /etc/ssl/private/self-signed.key

# View certificate info
sudo openssl x509 -in /etc/ssl/certs/self-signed.crt -text -noout

# Check certificate expiry
sudo openssl x509 -in /etc/ssl/certs/self-signed.crt -noout -dates
```

### View Let's Encrypt Certificate Details (Production)
```bash
# Check certificate path
sudo certbot certificates

# View certificate info
sudo openssl x509 -in /etc/letsencrypt/live/api.lankapasstravel.com/fullchain.pem -text -noout

# Check auto-renewal status
sudo systemctl status certbot.timer
```

## 6) Test SSL/TLS Connection
```bash
# View SSL handshake details
echo | openssl s_client -connect 13.212.50.145:443 -servername 13.212.50.145

# Or using curl with verbose output
curl -kv https://13.212.50.145/docs 2>&1 | grep -E "SSL|TLS|certificate"
```

## 7) View Nginx Logs
```bash
# Access logs (requests)
sudo tail -f /var/log/nginx/access.log

# Error logs (debugging)
sudo tail -f /var/log/nginx/error.log

# Docker logs
docker compose -f docker-compose.prod.yml logs -f nginx
```

## 8) Troubleshooting

### Connection refused on port 443
```bash
# Check if nginx container is running
docker compose -f docker-compose.prod.yml ps

# Check if port 443 is listening
sudo netstat -tlnp | grep 443

# Check security group allows port 443
echo "Check AWS Security Group for TCP 443"
```

### SSL Certificate not found
```bash
# Verify certificate location
sudo ls -la /etc/ssl/certs/self-signed.crt

# Regenerate if missing
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/self-signed.key \
  -out /etc/ssl/certs/self-signed.crt \
  -subj "/C=LK/ST=Western/L=Colombo/O=TravelApp/CN=13.212.50.145"

# Restart nginx
docker compose -f docker-compose.prod.yml restart nginx
```

### HTTP not redirecting to HTTPS
```bash
# Test redirect
curl -L http://13.212.50.145/docs -w "\nStatus: %{http_code}\n"

# Check nginx config for redirect rule
docker compose -f docker-compose.prod.yml exec nginx nginx -t

# View nginx config
cat ./nginx/nginx.conf
```

### API responding but receiving 502 Bad Gateway
```bash
# Check if api container is healthy
docker compose -f docker-compose.prod.yml ps

# Check api logs
docker compose -f docker-compose.prod.yml logs api

# Verify api is running on port 8000
docker compose -f docker-compose.prod.yml exec api netstat -tlnp | grep 8000
```

### No response from HTTPS endpoint
```bash
# Verify all ports are open
sudo netstat -tlnp | grep -E ':80|:443|:8000'

# Reset all containers
docker compose -f docker-compose.prod.yml down
sleep 3
docker compose -f docker-compose.prod.yml up -d

# Wait for containers to be healthy
sleep 10
docker compose -f docker-compose.prod.yml ps
```
