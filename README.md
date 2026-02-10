# Lanka Pass Travel API

Backend service for Lanka Pass Travel, powered by FastAPI and Supabase.

## Features

- **Vendor Management**: Registration, profiling, and service management.
- **Admin Dashboard**: Vendor approval workflow and system statistics.
- **Authentication**: Secure user authentication via Supabase Auth.
- **Service Catalog**: Management of travel services, categories, and pricing.

## Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Database**: [Supabase](https://supabase.com/) (PostgreSQL)
- **Authentication**: Supabase Auth
- **Validation**: [Pydantic](https://docs.pydantic.dev/)

## Getting Started

### Prerequisites

- Python 3.9 or higher
- A Supabase project and account

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Lanka-Pass-Travel-Backend
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**:
   Create a `.env` file in the root directory by copying `.env.example`:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and fill in your Supabase credentials and other configuration settings.

### Running the Application

Launch the development server using the provided `run.py` script:

```bash
python run.py
```

The server will start at `http://localhost:8000` with auto-reload enabled.

## Docker

Use Docker for local or production runs:
- `DOCKER.md` - Complete Docker setup and HTTPS configuration

## HTTPS Setup

### Testing (Self-Signed Certificate)
For local testing on EC2 IP (13.212.50.145):
- `HTTPS_WITHOUT_DOMAIN_TESTING.txt` - Quick HTTPS testing without domain
- `SELF_SIGNED_CERT_COMMANDS.txt` - Copy-paste commands for EC2

### Production (Let's Encrypt)
With your domain (api.lankapasstravel.com):
- `HTTPS_SETUP_GUIDE.txt` - Complete step-by-step HTTPS setup with Let's Encrypt

## AWS EC2 (Beginner Guide)

Deploy to EC2 with step-by-step instructions including HTTPS:
- `AWS_EC2_SETUP.md` - EC2 instance setup with Docker and HTTPS

## CI/CD (GitHub Actions → EC2)

Automated deploy on every push to `main` with HTTPS support:
- `CI_CD.md` - CI/CD pipeline with HTTPS enabled

### API Documentation

Once the server is running, you can access the interactive API documentation:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Project Structure

```text
├── app/                  # Application source code
│   └── main.py           # FastAPI entry point & API routes
├── .env.example          # Environment variables template
├── requirements.txt       # Python dependencies
├── run.py                # Server entry point script
├── schema.sql            # Database schema definitions
└── demo_vendor.json      # Sample data for testing
```

## Contributing

1. Create a new branch for your feature or bug fix.
2. Ensure your code follows the project's coding standards.
3. Submit a pull request with a clear description of your changes.
