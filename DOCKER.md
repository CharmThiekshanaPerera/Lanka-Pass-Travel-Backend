# Docker Instructions

## Build Image
```bash
docker build -t lanka-travel-backend .
```

## Run Container
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
### Build and Start
```bash
docker compose up --build
```

### Start (No Rebuild)
```bash
docker compose up
```

### Stop and Remove
```bash
docker compose down
```

### Rebuild Only
```bash
docker compose build
```

## Production (Nginx on Port 80)
Use this when you want a public API behind Nginx.

### Build and Start
```bash
docker compose -f docker-compose.prod.yml up --build -d
```

### Stop and Remove
```bash
docker compose -f docker-compose.prod.yml down
```

### Logs
```bash
docker compose -f docker-compose.prod.yml logs -f
```
