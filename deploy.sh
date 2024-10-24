#!/bin/bash

# Exit on error
set -e

# Configuration
DOMAIN=${1:-"example.com"}
EMAIL=${2:-"admin@example.com"}
COMPOSE_FILE="docker-compose.yml"

# Default flags
INSTALL_DOCKER=false
FETCH_CODE=false
SETUP_SSL=false
FORCE_RENEW_SSL=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log() { echo -e "${GREEN}[$(date +'%Y-%m-%dT%H:%M:%S%z')] $1${NC}"; }
info() { echo -e "${BLUE}[$(date +'%Y-%m-%dT%H:%M:%S%z')] $1${NC}"; }
warn() { echo -e "${YELLOW}[$(date +'%Y-%m-%dT%H:%M:%S%z')] WARNING: $1${NC}"; }
error() { echo -e "${RED}[$(date +'%Y-%m-%dT%H:%M:%S%z')] ERROR: $1${NC}"; }

# Help message
show_help() {
    echo "Usage: $0 [domain] [email] [options]"
    echo
    echo "Arguments:"
    echo "  domain         Domain name (required)"
    echo "  email          Email address for SSL certificates (required)"
    echo
    echo "Options:"
    echo "  --help, -h     Show this help message"
    echo "  --docker       Install Docker and Docker Compose"
    echo "  --fetch-code   Fetch/update code from repository"
    echo "  --setup-ssl    Setup/renew SSL certificates"
    echo "  --force-ssl    Force SSL certificate renewal"
    echo
    echo "Examples:"
    echo "  # First time setup with everything:"
    echo "  $0 mydomain.com admin@mydomain.com --docker --setup-ssl"
    echo
    echo "  # Update deployment:"
    echo "  $0 mydomain.com admin@mydomain.com --fetch-code"
    echo
    echo "  # Renew SSL certificate:"
    echo "  $0 mydomain.com admin@mydomain.com --setup-ssl --force-ssl"
    exit 0
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_help
                ;;
            --docker)
                INSTALL_DOCKER=true
                ;;
            --fetch-code)
                FETCH_CODE=true
                ;;
            --setup-ssl)
                SETUP_SSL=true
                ;;
            --force-ssl)
                FORCE_RENEW_SSL=true
                ;;
            *)
                shift
                ;;
        esac
        shift
    done
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
        exit 1
    fi

    # Validate domain format
    if [[ ! $DOMAIN =~ ^([a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$ ]]; then
        error "Invalid domain format: $DOMAIN"
        error "Domain should be in format: domain.com or subdomain.domain.com"
        exit 1
    fi

    # Check required files
    if [ ! -f "docker-compose.yml" ]; then
        error "docker-compose.yml not found. Please run this script from the repository root."
        exit 1
    fi
}

# Install Docker and Docker Compose
install_docker() {
    if [ "$INSTALL_DOCKER" = true ]; then
        log "Installing Docker and Docker Compose..."
        
        # Install Docker if not present
        if ! command -v docker &> /dev/null; then
            info "Installing Docker..."
            curl -fsSL https://get.docker.com -o get-docker.sh
            sh get-docker.sh
            usermod -aG docker $SUDO_USER
        else
            info "Docker already installed"
        fi

        # Install Docker Compose if not present
        if ! command -v docker-compose &> /dev/null; then
            info "Installing Docker Compose..."
            curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
            chmod +x /usr/local/bin/docker-compose
        else
            info "Docker Compose already installed"
        fi
    fi
}

# Setup SSL certificates
setup_ssl() {
    if [ "$SETUP_SSL" = true ] || [ ! -f "certbot/conf/live/$DOMAIN/fullchain.pem" ]; then
        log "Setting up SSL certificates..."
        
        # Create required directories
        mkdir -p certbot/conf certbot/www
        
        # Stop any running containers
        docker-compose down 2>/dev/null || true
        
        # Check if certificate already exists and force renewal is not set
        if [ -f "certbot/conf/live/$DOMAIN/fullchain.pem" ] && [ "$FORCE_RENEW_SSL" = false ]; then
            warn "SSL certificates already exist. Use --force-ssl to force renewal."
            return
        fi
        
        # Generate certificates
        log "Generating SSL certificates..."
        docker run -it --rm \
            -v "$PWD/certbot/conf:/etc/letsencrypt" \
            -v "$PWD/certbot/www:/var/www/certbot" \
            -p 80:80 \
            certbot/certbot certonly --standalone \
            --email "$EMAIL" \
            --agree-tos \
            --no-eff-email \
            --force-renewal \
            -d "$DOMAIN"
        
        # Verify certificates
        if [ -f "certbot/conf/live/$DOMAIN/fullchain.pem" ] && [ -f "certbot/conf/live/$DOMAIN/privkey.pem" ]; then
            log "SSL certificates generated successfully!"
        else
            error "SSL certificate generation failed!"
            exit 1
        fi
    fi
}

# Configure Nginx
configure_nginx() {
    log "Configuring Nginx..."
    
    # Check SSL certificates
    if [ ! -f "certbot/conf/live/$DOMAIN/fullchain.pem" ] || [ ! -f "certbot/conf/live/$DOMAIN/privkey.pem" ]; then
        error "SSL certificates not found! Please run with --setup-ssl first."
        exit 1
    fi
    
    # Create Nginx configuration
    cat > nginx.conf <<EOL
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    client_max_body_size 100M;

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
        
        # SSL configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_prefer_server_ciphers off;
        ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
        ssl_session_timeout 1d;
        ssl_session_cache shared:SSL:50m;
        ssl_session_tickets off;
        
        # HSTS
        add_header Strict-Transport-Security "max-age=31536000" always;

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

# Setup application
setup_application() {
    log "Setting up application..."
    
    # Create data directories
    mkdir -p data/{db,minio,redis}
    
    # Update code if requested
    if [ "$FETCH_CODE" = true ]; then
        if [ -d ".git" ]; then
            log "Updating existing repository..."
            git pull origin main
        else
            warn "Not a git repository. Skipping code update."
        fi
    fi

    # Setup environment file
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            sed -i "s/your-domain.com/$DOMAIN/g" .env
            sed -i "s/your-email@example.com/$EMAIL/g" .env
            log "Created and configured .env file"
        else
            error "No .env.example file found!"
            exit 1
        fi
    fi
}

# Start services
start_services() {
    log "Starting services..."
    
    # Verify Docker is running
    if ! docker info > /dev/null 2>&1; then
        error "Docker is not running!"
        exit 1
    fi

    # Pull latest images
    log "Pulling latest Docker images..."
    docker-compose pull

    # Stop existing containers
    docker-compose down --remove-orphans

    # Start services
    log "Starting all services..."
    docker-compose up -d

    # Check services
    log "Verifying services..."
    docker-compose ps
}

# Setup certificate renewal
setup_cert_renewal() {
    log "Setting up certificate renewal..."
    if ! crontab -l | grep -q "certbot renew"; then
        (crontab -l 2>/dev/null; echo "0 12 * * * cd $(pwd) && docker-compose run --rm certbot renew --quiet && docker-compose restart nginx") | crontab -
        log "Added certificate renewal cron job"
    fi
}

# Main execution
main() {
    parse_args "$@"
    
    log "Starting deployment for $DOMAIN..."
    
    check_prerequisites
    install_docker
    setup_ssl
    setup_application
    configure_nginx
    start_services
    setup_cert_renewal
    
    log "Deployment completed successfully!"
    log "Your application is now available at https://$DOMAIN"
    
    info "Useful commands:"
    info "  - View logs: docker-compose logs -f"
    info "  - Restart services: docker-compose restart"
    info "  - Stop services: docker-compose down"
    info "  - Start services: docker-compose up -d"
    info "  - Force SSL renewal: $0 $DOMAIN $EMAIL --setup-ssl --force-ssl"
}

# Run main function
main "$@"