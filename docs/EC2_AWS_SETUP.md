# AWS EC2 Setup (Amazon Linux + Docker + HTTPS)

This guide deploys the Lanka Pass Travel backend on an AWS EC2 instance using Amazon Linux, Docker, Nginx, and Let's Encrypt.

**Assumptions**
- You have a domain name (example: `api.yourdomain.com`) and can edit DNS.
- You will configure required environment variables in a `.env` file.
- You want HTTPS using Let's Encrypt.

---

## 1) Launch EC2

1. Launch an Amazon Linux 2023 (or Amazon Linux 2) instance.
2. Instance size: `t3.small` or higher.
3. Security Group inbound rules:
   - `22` SSH (your IP only)
   - `80` HTTP (0.0.0.0/0)
   - `443` HTTPS (0.0.0.0/0)

---

## 2) SSH into the instance

```bash
ssh -i your-key.pem ec2-user@YOUR_EC2_PUBLIC_IP
```

---

## 3) Install Docker and Compose

### Amazon Linux 2023

```bash
sudo dnf update -y
sudo dnf install -y docker
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user
newgrp docker
```

Install the Docker Compose plugin:

```bash
sudo dnf install -y docker-compose-plugin
docker compose version
```

### Amazon Linux 2

```bash
sudo yum update -y
sudo amazon-linux-extras install docker -y
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user
newgrp docker
```

Install Docker Compose:

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

---

## 4) Upload the backend code

### Option A: Git clone

```bash
git clone YOUR_REPO_URL
cd Lanka-Pass-Travel-Backend
```

### Option B: SCP from local

```bash
scp -i your-key.pem -r ./Lanka-Pass-Travel-Backend ec2-user@YOUR_EC2_PUBLIC_IP:~/
cd Lanka-Pass-Travel-Backend
```

---

## 5) Create the `.env` file

Use `.env.example` as a template:

```bash
cp .env.example .env
nano .env
```

Required environment variables:
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_JWT_SECRET`
- `SECRET_KEY`
- `CORS_ORIGINS`

Optional but recommended (feature-specific):
- `MONGO_URI` (enables chat and update-request features)
- `TEXT_LK_API_KEY`
- `TEXT_LK_SENDER_ID`
- `SENDGRID_API_KEY`
- `SENDGRID_FROM_EMAIL`

---

## 6) Add `Dockerfile`

Create a `Dockerfile` in the repo root:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 7) Add `docker-compose.yml`

Create `docker-compose.yml`:

```yaml
services:
  api:
    build: .
    container_name: lanka-pass-api
    env_file:
      - .env
    ports:
      - "8000:8000"
    restart: unless-stopped
```

---

## 8) Build and run

```bash
docker compose up -d --build
docker ps
```

Test locally:

```bash
curl http://localhost:8000
```

---

## 9) Install Nginx

Amazon Linux 2023:

```bash
sudo dnf install -y nginx
sudo systemctl enable --now nginx
```

Amazon Linux 2:

```bash
sudo yum install -y nginx
sudo systemctl enable --now nginx
```

---

## 10) Configure Nginx reverse proxy

Replace `api.yourdomain.com` with your domain:

```bash
sudo tee /etc/nginx/conf.d/lankapass.conf >/dev/null <<'EOF'
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
```

Validate and reload:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## 11) Point DNS to EC2

Create an `A` record:
- `api.yourdomain.com` -> `YOUR_EC2_PUBLIC_IP`

Wait for DNS propagation.

---

## 12) Install HTTPS (Let's Encrypt)

Amazon Linux 2023:

```bash
sudo dnf install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.yourdomain.com
```

Amazon Linux 2:

```bash
sudo yum install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.yourdomain.com
```

Test auto-renew:

```bash
sudo certbot renew --dry-run
```

---

## 13) Production checks

1. Health check:
   - `https://api.yourdomain.com`
2. Logs:
   - Nginx: `/var/log/nginx/access.log` and `/var/log/nginx/error.log`
   - App container: `docker logs -f lanka-pass-api`

---

## Notes for this repo

1. `run.py` uses `reload=True` for dev. Docker runs Uvicorn without reload (correct for production).
2. If `MONGO_URI` is not set, chat/update-request features are disabled (the app logs a warning).
3. `auth_debug.log` will grow quickly in production. Consider disabling verbose auth logging in `app/main.py` if needed.

