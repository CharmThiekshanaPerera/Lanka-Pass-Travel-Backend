# EC2 Working Check (api.lankapasstravel.com)

Use this checklist to verify your EC2 backend is live, HTTPS is valid, and Docker services are healthy.

## 1) DNS Resolution (Local Machine)
```bash
nslookup api.lankapasstravel.com
```
Expected: `13.212.50.145`

## 2) HTTP → HTTPS Redirect (Local Machine)
```bash
curl -I http://api.lankapasstravel.com
```
Expected: `301` redirect to HTTPS.

## 3) HTTPS Reachability (Local Machine)
```bash
curl -I https://api.lankapasstravel.com
```
Expected: `200` or `307` (depending on app).

## 4) TLS Certificate Validity (Local Machine)
```bash
echo | openssl s_client -connect api.lankapasstravel.com:443 -servername api.lankapasstravel.com | openssl x509 -noout -subject -issuer -dates
```
Expected:
- Issuer: Let’s Encrypt
- Valid date range (not expired)

## 5) API Endpoints (Local Machine)
```bash
curl https://api.lankapasstravel.com/docs
curl https://api.lankapasstravel.com/api/v1/health
```

## 6) Containers Healthy (EC2)
```bash
docker compose -f docker-compose.prod.yml ps
```
Expected: both `api` and `nginx` are `Up (healthy)`.

## 7) Nginx Config Valid (EC2)
```bash
docker compose -f docker-compose.prod.yml exec nginx nginx -t
```
Expected: `syntax is ok` and `test is successful`.

## 8) Nginx Logs (EC2)
```bash
docker compose -f docker-compose.prod.yml logs -f nginx
```

## 9) API Logs (EC2)
```bash
docker compose -f docker-compose.prod.yml logs -f api
```

## 10) Quick Failure Checklist

- DNS mismatch: verify `api.lankapasstravel.com` points to `13.212.50.145`.
- Port blocked: ensure EC2 security group allows `80` and `443`.
- Cert missing: confirm `/etc/letsencrypt/live/api.lankapasstravel.com/` exists on EC2.
- Container down: restart with:
```bash
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```
