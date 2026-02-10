# AWS EC2 Setup Guide (Beginner Friendly)

This guide shows how to deploy this API on an AWS EC2 instance using Docker with HTTPS.
It assumes you are using Ubuntu 22.04 LTS.

## 1) Create an AWS Account
- Go to the AWS console and sign in.
- Complete billing setup if needed.

## 2) Create a Key Pair (SSH Key)
1. In the EC2 console, go to `Key pairs`.
2. Click `Create key pair`.
3. Name it and download the `.pem` file.
4. Keep the `.pem` file safe.

## 3) Launch an EC2 Instance
1. Go to `Instances` and click `Launch instance`.
2. Name your instance.
3. Choose **Ubuntu Server 22.04 LTS**.
4. Select an instance type like `t3.micro` (free tier).
5. Select the key pair you created.
6. Create or edit the Security Group:
   - Allow `SSH` (port 22) from your IP.
   - Allow `HTTP` (port 80) from `0.0.0.0/0`.
   - **Allow `HTTPS` (port 443) from `0.0.0.0/0`.**
   - Optional: allow `Custom TCP` port `8000` from `0.0.0.0/0` for direct access.
7. Click `Launch instance`.

Current EC2:
- Public IPv4: `13.212.50.145`
- Public DNS: `ec2-13-212-50-145.ap-southeast-1.compute.amazonaws.com`

## 4) Create Elastic IP (Static IP - Recommended)
For a permanent IP that doesn't change on restart:
1. Go to EC2 → Elastic IPs
2. Click "Allocate Elastic IP address"
3. Select your region: ap-southeast-1
4. Click "Allocate"
5. Select the new IP, click "Associate this Elastic IP address"
6. Select your EC2 instance
7. Click "Associate"

Now your EC2 has a permanent static IP.

## 5) Connect to Your Instance
From your local machine:
```bash
ssh -i /path/to/key.pem ubuntu@13.212.50.145
```

## 6) Install Docker on EC2
Option A (recommended): Docker official repo (includes Compose plugin)
```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Option B: Ubuntu repo packages (uses classic docker-compose)
```bash
sudo apt update
sudo apt install -y docker.io docker-compose
```

After install:
```bash
sudo usermod -aG docker $USER
newgrp docker
docker --version
docker compose version   # if you installed the plugin
docker-compose --version # if you installed classic compose
```

## 7) Upload or Clone Your Project
Option A: Clone (recommended)
```bash
git clone https://github.com/CharmThiekshanaPerera/Lanka-Pass-Travel-Backend.git /home/ubuntu/lanka-pass-travel-backend
cd /home/ubuntu/lanka-pass-travel-backend
```

Option B: Upload your project folder
```bash
scp -i /path/to/key.pem -r "d:\Phyxle Web Projects\Travel App\Lanka Travel Pass Backend" ubuntu@13.212.50.145:/home/ubuntu/
```
Then on EC2:
```bash
cd "/home/ubuntu/lanka-pass-travel-backend"
```

## 8) Create the .env File
```bash
cp .env.example .env
sudo nano .env
```
Fill in all required values (Supabase keys, etc.).

## 9a) Setup HTTPS - Self-Signed Certificate (For Testing)
Create SSL directories and certificate:
```bash
# Create SSL directories
sudo mkdir -p ./ssl/certs ./ssl/private

# Generate self-signed certificate (valid for 365 days)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ./ssl/private/self-signed.key \
  -out ./ssl/certs/self-signed.crt \
  -subj "/C=LK/ST=Western/L=Colombo/O=TravelApp/CN=13.212.50.145"

# Fix permissions
sudo chmod 644 ./ssl/certs/self-signed.crt
sudo chmod 644 ./ssl/private/self-signed.key
sudo chown $USER:$USER -R ./ssl
```

Verify certificate was created:
```bash
ls -la ./ssl/certs/
ls -la ./ssl/private/
```

## 9b) Setup HTTPS - Let's Encrypt Certificate (For Production with Domain)
Once you have a domain (api.lankapasstravel.com):

1. Point your domain DNS to the EC2 IP
2. Wait 5-10 minutes for DNS propagation
3. Install Certbot:
```bash
sudo apt install -y certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly --standalone -d api.lankapasstravel.com

# Verify certificate
sudo certbot certificates
```

4. Update `nginx.conf` to use Let's Encrypt certificates:
   - Change `/etc/ssl/certs/self-signed.crt` to `/etc/letsencrypt/live/api.lankapasstravel.com/fullchain.pem`
   - Change `/etc/ssl/private/self-signed.key` to `/etc/letsencrypt/live/api.lankapasstravel.com/privkey.pem`

5. Restart containers:
```bash
docker compose -f docker-compose.prod.yml down
sleep 3
docker compose -f docker-compose.prod.yml up -d
```

## 10) Build and Run (Production with Nginx & HTTPS)
```bash
docker compose -f docker-compose.prod.yml up --build -d
```

Wait 10 seconds for containers to start:
```bash
sleep 10
```

## 11) Check It Works
```bash
# Check containers
docker ps

# Should show both api and nginx containers in "Up" state
```

### Test HTTPS with Self-Signed Certificate
```bash
# From your local machine (ignore certificate warning)
curl -k https://13.212.50.145/docs

# Test API health
curl -k https://13.212.50.145/api/v1/health
```

### Test HTTPS with Valid Certificate (Production)
```bash
# No -k flag needed with Let's Encrypt cert
curl https://api.lankapasstravel.com/docs
curl https://api.lankapasstravel.com/api/v1/health
```

## 12) View Logs
```bash
# View all containers logs
docker compose -f docker-compose.prod.yml logs -f

# View specific service
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml logs -f nginx
```

## Common Issues

### Connection refused / No response
1. Check security group allows ports 80, 443:
   - Go to EC2 → Security Groups → Edit inbound rules
   - Verify HTTP (80) and HTTPS (443) are open
   
2. Check containers are running:
   ```bash
   docker ps
   docker compose -f docker-compose.prod.yml ps
   ```

3. Check Nginx configuration:
   ```bash
   cat ./nginx/nginx.conf
   ```

### SSL Certificate not found
```bash
# Verify certificate location
ls -la ./ssl/

# Regenerate if missing
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ./ssl/private/self-signed.key \
  -out ./ssl/certs/self-signed.crt \
  -subj "/C=LK/ST=Western/L=Colombo/O=TravelApp/CN=13.212.50.145"
```

### Invalid .env
Make sure all required values are set:
```bash
sudo nano .env
# Fill in SUPABASE_URL, SUPABASE_KEY, etc.
```

### Container stuck or not responding
```bash
# View detailed logs
docker compose -f docker-compose.prod.yml logs -f

# Restart containers
docker compose -f docker-compose.prod.yml restart

# Full restart
docker compose -f docker-compose.prod.yml down
sleep 3
docker compose -f docker-compose.prod.yml up -d
```

## Stop and Remove
```bash
docker compose -f docker-compose.prod.yml down
```

## Update & Redeploy
When you push to GitHub (CI/CD):
```bash
# Manual update/redeploy:
cd /home/ubuntu/lanka-pass-travel-backend
git pull origin main
docker compose -f docker-compose.prod.yml down
sleep 3
docker compose -f docker-compose.prod.yml up --build -d
```

## API Documentation
Once running with HTTPS:
- **Testing (Self-Signed)**: https://13.212.50.145/docs
- **Production (Let's Encrypt)**: https://api.lankapasstravel.com/docs
