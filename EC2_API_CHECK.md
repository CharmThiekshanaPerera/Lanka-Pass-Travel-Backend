# EC2 API Check Guide

Use this guide to verify your backend APIs are running on EC2 and to list all endpoints.

## 1) Check Containers on EC2
```bash
docker ps
```

If you use the production compose:
```bash
docker compose -f docker-compose.prod.yml ps
```

## 2) Test Locally on EC2
```bash
curl http://localhost/docs
curl http://localhost/openapi.json
```

If you use Nginx on port 80 (recommended), the API is behind Nginx and docs are at `/docs`.

## 3) Test From Your Local Machine
```bash
curl http://13.212.50.145/docs
curl http://13.212.50.145/openapi.json
```

## 4) List All Endpoints (from OpenAPI)
```bash
curl -s http://13.212.50.145/openapi.json > openapi.json
```
Open `openapi.json` to see all endpoints.  
If you want a quick list of paths:
```bash
python - <<'PY'
import json
with open("openapi.json", "r", encoding="utf-8") as f:
    data = json.load(f)
for path in sorted(data.get("paths", {})):
    print(path)
PY
```

## 5) Troubleshooting
- **Connection refused**: Check EC2 security group allows `TCP 80`.
- **No response**: Check logs:
  ```bash
  docker compose -f docker-compose.prod.yml logs -f
  ```
- **404 on /docs**: Ensure the API is running and Nginx is proxying to `api:8000`.
