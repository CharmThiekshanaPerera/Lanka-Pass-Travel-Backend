# GitHub CI/CD to AWS EC2 (Simple SSH)

This uses GitHub Actions to SSH into EC2 and run Docker Compose on every push to `main`.

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
Make sure EC2 has Docker + Compose and git:
```bash
sudo apt update
sudo apt install -y git
```
Then follow `AWS_EC2_SETUP.md` for Docker installation.

## 6) Deploy
Push to `main` and GitHub Actions will:
- SSH into EC2
- Clone or update the repo
- Run:
```bash
docker compose -f docker-compose.prod.yml up --build -d
```

## 7) Access API
- `http://13.212.50.145/docs`

## Troubleshooting
- Check GitHub Actions logs for SSH errors.
- On EC2, run:
  ```bash
  docker ps
  docker compose -f docker-compose.prod.yml logs -f
  ```
