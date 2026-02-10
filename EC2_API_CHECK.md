# EC2 API Check Guide

Use this guide to verify your backend APIs are running on EC2 with HTTPS and to list all endpoints.
Default configuration assumes Let's Encrypt with `api.lankapasstravel.com`.

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

## 2) Test Locally on EC2 (HTTPS with Let's Encrypt - Default)
```bash
# Test HTTPS endpoint
curl https://api.lankapasstravel.com/docs
curl https://api.lankapasstravel.com/openapi.json

# Test HTTP redirect (should redirect to HTTPS)
curl -L http://api.lankapasstravel.com/docs
```

## 3) Test From Your Local Machine (HTTPS)

### With Valid Let's Encrypt Certificate (Default)
```bash
# No -k flag needed
curl https://api.lankapasstravel.com/docs
curl https://api.lankapasstravel.com/openapi.json
curl https://api.lankapasstravel.com/api/v1/health
```

### With Self-Signed Certificate (Optional Testing)
```bash
# Ignore certificate warning
curl -k https://13.212.50.145/docs
curl -k https://13.212.50.145/openapi.json
curl -k https://13.212.50.145/api/v1/health
```

## 4) Test API Endpoints

### Health Check
```bash
curl https://api.lankapasstravel.com/api/v1/health
```

### Vendor Registration
```bash
curl -X POST https://api.lankapasstravel.com/api/v1/vendors \
  -H "Content-Type: application/json" \
  -d '{"email":"vendor@example.com","password":"password123"}'
```

### Admin Login
```bash
curl -X POST https://api.lankapasstravel.com/api/v1/admin/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password123"}'
```

### List All Endpoints (from OpenAPI)
```bash
# Download OpenAPI spec
curl -s https://api.lankapasstravel.com/openapi.json > openapi.json

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

### View Let's Encrypt Certificate Details (Default)
```bash
# Check certificate path
sudo certbot certificates

# View certificate info
sudo openssl x509 -in /etc/letsencrypt/live/api.lankapasstravel.com/fullchain.pem -text -noout

# Check auto-renewal status
sudo systemctl status certbot.timer
```

### View Self-Signed Certificate Details (Optional Testing)
```bash
# Check certificate paths
sudo ls -la /etc/ssl/certs/self-signed.crt
sudo ls -la /etc/ssl/private/self-signed.key

# View certificate info
sudo openssl x509 -in /etc/ssl/certs/self-signed.crt -text -noout

# Check certificate expiry
sudo openssl x509 -in /etc/ssl/certs/self-signed.crt -noout -dates
```

## 6) Test SSL/TLS Connection
```bash
# View SSL handshake details
echo | openssl s_client -connect api.lankapasstravel.com:443 -servername api.lankapasstravel.com

# Or using curl with verbose output
curl -kv https://api.lankapasstravel.com/docs 2>&1 | grep -E "SSL|TLS|certificate"
```

## 7) View Nginx Logs
```bash
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
# Verify Let's Encrypt cert location
sudo ls -la /etc/letsencrypt/live/api.lankapasstravel.com/

# Re-run Certbot if missing
sudo certbot certonly --standalone -d api.lankapasstravel.com

# Restart nginx
docker compose -f docker-compose.prod.yml restart nginx
```

### HTTP not redirecting to HTTPS
```bash
# Test redirect
curl -L http://api.lankapasstravel.com/docs -w "\nStatus: %{http_code}\n"

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
