#!/bin/bash

# Exit on error
set -e

# Configuration
DOMAIN=${1:-"example.com"}  # Pass domain as first argument or use default
EMAIL=${2:-"admin@example.com"}  # Pass email as second argument or use default
REPO_URL="https://github.com/yourusername/foxhole.git"
APP_DIR="/opt/foxhole"
COMPOSE_FILE="docker-compose.yml"

# Default flags for optional steps
INSTALL_DOCKER=false
FETCH_CODE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Help message
show_help() {
    echo "Usage: $0 [domain] [email] [options]"
    echo
    echo "Arguments:"
    echo "  domain         Domain name (default: example.com)"
    echo "  email          Email address for SSL certificates (default: admin@example.com)"
    echo
    echo "Options:"
    echo "  --help, -h     Show this help message"
    echo "  --docker       Install Docker and Docker Compose"
    echo "  --fetch-code   Fetch/update code from repository"
    echo
    echo "Example:"
    echo "  $0 mydomain.com admin@mydomain.com --docker --fetch-code"
    exit 0
}

# Parse command line arguments
parse_args() {
    local skip=0
    for i in "$@"; do
        if [ $skip -eq 1 ]; then
            skip=0
            continue
        fi
        case $i in
            --help|-h)
                show_help
                ;;
            --docker)
                INSTALL_DOCKER=true
                ;;
            --fetch-code)
                FETCH_CODE=true
                ;;
        esac
    done
}

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%dT%H:%M:%S%z')] $1${NC}"
}

info() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%dT%H:%M:%S%z')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%dT%H:%M:%S%z')] ERROR: $1${NC}"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root"
   exit 1
fi

# Validate domain
if [[ ! $DOMAIN =~ ^([a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$ ]]; then
    error "Invalid domain format: $DOMAIN"
    error "Domain should be in format: domain.com or subdomain.domain.com"
    exit 1
fi

# Install dependencies
install_dependencies() {
    log "Installing basic dependencies..."
    apt-get update
    apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
}

# Install Docker
install_docker() {
    if [ "$INSTALL_DOCKER" = true ]; then
        log "Installing Docker..."
        if ! command -v docker &> /dev/null; then
            curl -fsSL https://get.docker.com -o get-docker.sh
            sh get-docker.sh
            usermod -aG docker $SUDO_USER
            log "Docker installed successfully"
        else
            info "Docker already installed, skipping..."
        fi

        log "Installing Docker Compose..."
        if ! command -v docker-compose &> /dev/null; then
            curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
            chmod +x /usr/local/bin/docker-compose
            log "Docker Compose installed successfully"
        else
            info "Docker Compose already installed, skipping..."
        fi
    else
        info "Skipping Docker installation (use --docker flag to install)"
    fi
}

# Setup application
setup_application() {
    log "Setting up application..."
    
    # Create application directory if it doesn't exist
    mkdir -p $APP_DIR
    cd $APP_DIR

    # Clone or pull repository if --fetch-code flag is set
    if [ "$FETCH_CODE" = true ]; then
        if [ -d ".git" ]; then
            log "Updating existing repository..."
            git pull origin main
        else
            log "Cloning repository..."
            git clone $REPO_URL .
        fi
    else
        info "Skipping code fetch (use --fetch-code flag to fetch/update code)"
        # Check if the directory is empty
        if [ ! -f "docker-compose.yml" ]; then
            error "Application files not found. Please run with --fetch-code flag first."
            exit 1
        fi
    fi

    # Create necessary directories
    mkdir -p data/{db,minio,redis} certbot/{conf,www}

    # Copy environment file if it doesn't exist
    if [ ! -f ".env" ]; then
        cp .env.example .env
        # Update environment variables
        sed -i "s/your-domain.com/$DOMAIN/g" .env
        sed -i "s/your-email@example.com/$EMAIL/g" .env
        log "Created and configured .env file"
    else
        info "Environment file already exists, skipping..."
    fi
}

# Configure Nginx
configure_nginx() {
    log "Configuring Nginx..."
    
    # Create Nginx configuration
    cat > nginx.conf <<EOL
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    upstream app {
        server app:8000;
    }

    server {
        listen 80;
        server_name $DOMAIN;
        
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        location / {
            return 301 https://\$host\$request_uri;
        }
    }

    server {
        listen 443 ssl;
        server_name $DOMAIN;

        ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

        location / {
            proxy_pass http://app;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            
            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_read_timeout 86400;
        }
    }
}
EOL
    log "Nginx configured successfully"
}

# Start services
start_services() {
    log "Starting services..."
    
    # Verify Docker is running
    if ! docker info > /dev/null 2>&1; then
        error "Docker is not running. Please start Docker first."
        exit 1
    }

    # Stop any existing containers
    docker-compose down --remove-orphans

    # Start Nginx for initial certificate acquisition
    log "Starting Nginx..."
    docker-compose up -d nginx

    # Get SSL certificate
    log "Obtaining SSL certificate..."
    docker-compose run --rm certbot certonly \
        --webroot \
        --webroot-path /var/www/certbot \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        --force-renewal \
        -d $DOMAIN

    # Start all services
    log "Starting all services..."
    docker-compose up -d

    # Verify services are running
    log "Verifying services..."
    docker-compose ps
}

# Check ports
check_ports() {
    log "Checking required ports..."
    if lsof -i:80 >/dev/null 2>&1; then
        error "Port 80 is already in use. Please free this port before continuing."
        exit 1
    fi
    if lsof -i:443 >/dev/null 2>&1; then
        error "Port 443 is already in use. Please free this port before continuing."
        exit 1
    fi
    log "Ports 80 and 443 are available"
}

# Main execution
main() {
    # Parse command line arguments
    parse_args "$@"

    log "Starting deployment for $DOMAIN..."
    
    check_ports
    install_dependencies
    install_docker
    setup_application
    configure_nginx
    start_services
    
    log "Deployment completed successfully!"
    log "Please check your application at https://$DOMAIN"
    
    # Print useful information
    info "Useful commands:"
    info "  - View logs: docker-compose logs -f"
    info "  - Restart services: docker-compose restart"
    info "  - Stop services: docker-compose down"
    info "  - Start services: docker-compose up -d"
}

# Run main function with all arguments
main "$@"

# Add cron job for certificate renewal if it doesn't exist
if ! crontab -l | grep -q "certbot renew"; then
    (crontab -l 2>/dev/null; echo "0 12 * * * cd $APP_DIR && docker-compose run --rm certbot renew --quiet") | crontab -
    log "Added certificate renewal cron job"
fi