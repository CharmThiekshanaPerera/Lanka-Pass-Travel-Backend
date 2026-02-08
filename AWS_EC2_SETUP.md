# AWS EC2 Setup Guide (Beginner Friendly)

This guide shows how to deploy this API on an AWS EC2 instance using Docker.
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
   - Optional: allow `Custom TCP` port `8000` from `0.0.0.0/0` for direct access.
7. Click `Launch instance`.

## 4) Connect to Your Instance
From your local machine:
```bash
ssh -i /path/to/key.pem ubuntu@<EC2_PUBLIC_IP>
```

## 5) Install Docker on EC2
```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker
```

## 6) Upload or Clone Your Project
Option A: Clone (recommended if you have a repo)
```bash
git clone <your-repo-url>
cd <repo-folder>
```

Option B: Upload your project folder
```bash
scp -i /path/to/key.pem -r "d:\Phyxle Web Projects\Travel App\Lanka Travel Pass Backend" ubuntu@<EC2_PUBLIC_IP>:/home/ubuntu/
```
Then on EC2:
```bash
cd "/home/ubuntu/Lanka Travel Pass Backend"
```

## 7) Create the .env File
```bash
cp .env.example .env
nano .env
```
Fill in all required values (Supabase keys, etc.).

## 8) Build and Run (Production with Nginx)
```bash
docker compose -f docker-compose.prod.yml up --build -d
```

## 9) Check It Works
```bash
docker ps
curl http://<EC2_PUBLIC_IP>/docs
```

## Common Issues
- **Connection refused**: Check security group ports.
- **Invalid .env**: Make sure all required values are set.
- **Container not running**: Use logs to see errors:
  ```bash
  docker compose -f docker-compose.prod.yml logs -f
  ```

## Stop and Remove
```bash
docker compose -f docker-compose.prod.yml down
```
