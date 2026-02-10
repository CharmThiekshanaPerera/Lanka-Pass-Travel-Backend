# GitHub CI/CD to AWS EC2 with HTTPS (Simple SSH)

This uses GitHub Actions to SSH into EC2 and run Docker Compose on every push to `main`.
The backend is served over HTTPS for secure API communication.

## 1) Choose Project Path on EC2
Recommended:
```
/home/ubuntu/lanka-pass-travel-backend
```

## 2) Create SSH Key for GitHub Actions
On your local machine:
```bash
ssh-keygen -t ed25519 -C "github-actions-ec2" -f github_ec2
```
This creates:
- `github_ec2` (private key)
- `github_ec2.pub` (public key)

## 3) Add Public Key to EC2
On your EC2 instance:
```bash
mkdir -p ~/.ssh
echo "<contents of github_ec2.pub>" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

## 4) Add GitHub Secrets
In your GitHub repo → **Settings → Secrets and variables → Actions**:
- `EC2_HOST` = `13.212.50.145`
- `EC2_USER` = `ubuntu`
- `EC2_SSH_KEY` = (contents of `github_ec2` private key)

You can also use DNS for `EC2_HOST`:
- `ec2-13-212-50-145.ap-southeast-1.compute.amazonaws.com`

## 5) First-Time Server Setup
Make sure EC2 has Docker + Compose and git, plus SSL certificates:

```bash
# Update and install git
sudo apt update
sudo apt install -y git

# Create SSL directories
sudo mkdir -p /home/ubuntu/lanka-pass-travel-backend/ssl/certs \
               /home/ubuntu/lanka-pass-travel-backend/ssl/private

# Generate self-signed certificate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /home/ubuntu/lanka-pass-travel-backend/ssl/private/self-signed.key \
  -out /home/ubuntu/lanka-pass-travel-backend/ssl/certs/self-signed.crt \
  -subj "/C=LK/ST=Western/L=Colombo/O=TravelApp/CN=13.212.50.145"

# Fix permissions
sudo chmod 644 /home/ubuntu/lanka-pass-travel-backend/ssl/certs/self-signed.crt
sudo chmod 644 /home/ubuntu/lanka-pass-travel-backend/ssl/private/self-signed.key
sudo chown ubuntu:ubuntu -R /home/ubuntu/lanka-pass-travel-backend/ssl
```

Then follow `AWS_EC2_SETUP.md` sections 5-10 for Docker installation.

## 6) Create GitHub Actions Workflow
Create `.github/workflows/deploy.yml` in your repository:

```yaml
name: Deploy to EC2

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Deploy to EC2
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ${{ secrets.EC2_USER }}
          key: ${{ secrets.EC2_SSH_KEY }}
          port: 22
          script: |
            cd /home/ubuntu/lanka-pass-travel-backend
            
            # Pull latest changes
            git pull origin main
            
            # Update environment if .env changed
            if [ ! -f .env ]; then
              cp .env.example .env
              echo "WARNING: .env created from .env.example. Please configure it!"
            fi
            
            # Stop old containers
            docker compose -f docker-compose.prod.yml down
            sleep 3
            
            # Build and start new containers with HTTPS
            docker compose -f docker-compose.prod.yml up --build -d
            sleep 10
            
            # Check containers are running
            docker compose -f docker-compose.prod.yml ps
            
            # Test HTTPS
            curl -k https://localhost/docs || echo "HTTPS health check pending"
```

## 7) Security Group - Allow HTTPS
In your AWS Security Group, ensure you allow:
- Port 80 (HTTP) → for redirect to HTTPS
- Port 443 (HTTPS) → for secure API access
- Port 22 (SSH) → for GitHub Actions deployment

## 8) Deploy
Push to `main` and GitHub Actions will:
- SSH into EC2
- Clone or update the repo
- Stop old containers
- Build and run new containers with HTTPS
- Run health checks

```bash
git add .
git commit -m "feature: update API"
git push origin main
```

## 9) Monitor Deployment
In your GitHub repo:
1. Go to **Actions** tab
2. Click the workflow run
3. View logs to see deployment progress
4. If successful, your API is live at HTTPS!

## 10) Access API

### Testing (Self-Signed Certificate)
```bash
# Browser (will show certificate warning)
https://13.212.50.145/docs

# API calls (ignore cert warning)
curl -k https://13.212.50.145/api/v1/health
```

### Production (Let's Encrypt)
```bash
# Browser (no warnings)
https://api.lankapasstravel.com/docs

# API calls
curl https://api.lankapasstravel.com/api/v1/health
```

## 11) Rollback (If Something Goes Wrong)
SSH into EC2 and revert:

```bash
cd /home/ubuntu/lanka-pass-travel-backend

# Stop current containers
docker compose -f docker-compose.prod.yml down

# Revert to previous commit
git reset --hard HEAD~1

# Restart
docker compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

### GitHub Actions Fails
1. Check GitHub Actions logs for error messages
2. Verify EC2_HOST, EC2_USER, and EC2_SSH_KEY are correct
3. Test SSH manually:
   ```bash
   ssh -i github_ec2 ubuntu@13.212.50.145
   ```

### Containers Don't Start
```bash
# SSH into EC2
ssh -i your-key.pem ubuntu@13.212.50.145

# Check logs
docker compose -f docker-compose.prod.yml logs -f

# Check .env is configured
cat .env | grep -E "SUPABASE|SECRET"
```

### SSL Certificate Errors
```bash
# Verify certificates exist
ls -la ~/lanka-pass-travel-backend/ssl/certs/
ls -la ~/lanka-pass-travel-backend/ssl/private/

# Regenerate if missing
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ~/lanka-pass-travel-backend/ssl/private/self-signed.key \
  -out ~/lanka-pass-travel-backend/ssl/certs/self-signed.crt \
  -subj "/C=LK/ST=Western/L=Colombo/O=TravelApp/CN=13.212.50.145"
```

### HTTPS Not Working
```bash
# Check security group
echo "Go to AWS Console → EC2 → Security Groups"
echo "Verify ports 80, 443, and 22 are open"

# Check nginx is running
docker ps | grep nginx

# Check nginx config
docker compose -f docker-compose.prod.yml exec nginx nginx -t
```
