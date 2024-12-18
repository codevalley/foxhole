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
    echo "  # Update deployment with code rebuild:"
    echo "  $0 mydomain.com admin@mydomain.com --fetch-code"
    echo
    echo "  # Just rebuild and redeploy current code:"
    echo "  $0 mydomain.com admin@mydomain.com"
}

# Parse command line arguments
parse_args() {
    local positional_args=()

    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_help
                exit 0
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
            -*|--*)
                error "Unknown option $1"
                show_help
                exit 1
                ;;
            *)
                positional_args+=("$1")
                ;;
        esac
        shift
    done

    # Restore positional arguments
    if [[ ${#positional_args[@]} -ge 1 ]]; then
        DOMAIN=${positional_args[0]}
    fi
    if [[ ${#positional_args[@]} -ge 2 ]]; then
        EMAIL=${positional_args[1]}
    fi
}

# Update code if requested
update_repository() {
    local current_domain="$1"
    local current_email="$2"
    shift 2
    local flags=("$@")

    if [ -d ".git" ]; then
        # Store the script content in memory since we're changing deploy.sh itself
        SCRIPT_CONTENT=$(cat "$0")

        log "Updating repository..."
        info "Restoring any local changes..."
        git restore .

        info "Pulling latest changes..."
        git pull origin main

        # If deploy.sh was updated, rewrite it and make it executable
        echo "$SCRIPT_CONTENT" > "$0"
        chmod +x "$0"

        log "Repository updated, restarting deployment with latest code..."

        # Reconstruct the command without --fetch-code to avoid infinite loop
        NEW_ARGS=()
        for arg in "${flags[@]}"; do
            if [ "$arg" != "--fetch-code" ]; then
                NEW_ARGS+=("$arg")
            fi
        done

        # Execute with original domain and email, plus remaining flags
        exec "$0" "$current_domain" "$current_email" "${NEW_ARGS[@]}"
    else
        warn "Not a git repository. Skipping code update."
    fi
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

    # Create data directories with proper permissions
    log "Setting up data directories..."
    mkdir -p data/db data/minio data/redis data/logs

    # Set proper permissions for data directories
    chown -R 1000:1000 data/  # Use appropriate user:group for your app
    chmod -R 755 data/

    # Ensure db directory is properly mounted and persisted
    if [ ! -d "data/db" ]; then
        error "Database directory not found or not properly mounted!"
        exit 1
    fi

    # Update code if requested
    if [ "$FETCH_CODE" = true ]; then
        update_repository "$DOMAIN" "$EMAIL" "$@"
    fi

    # Setup environment file
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            sed -i "s/your-domain.com/$DOMAIN/g" .env
            sed -i "s/your-email@example.com/$EMAIL/g" .env
            # Ensure DATABASE_URL points to the persistent location
            sed -i "s#sqlite+aiosqlite:///./app.db#sqlite+aiosqlite:///./data/db/app.db#g" .env
            # Configure log path
            sed -i "s#LOG_FILE=logs/app.log#LOG_FILE=/app/data/logs/app.log#g" .env
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

    # Build the application image
    log "Building application image..."
    if ! docker-compose build app; then
        error "Failed to build application image!"
        exit 1
    fi
    log "Application image built successfully"

    # Push to registry if configured
    if [ -n "$DOCKER_REGISTRY" ]; then
        log "Pushing image to registry..."
        if ! docker-compose push app; then
            error "Failed to push image to registry!"
            exit 1
        fi
        log "Image pushed to registry successfully"
    fi

    # Pull other service images
    log "Pulling other service images..."
    if ! docker-compose pull redis minio nginx; then
        warn "Failed to pull some service images, continuing anyway..."
    fi

    # Stop existing containers
    log "Stopping existing containers..."
    docker-compose down --remove-orphans

    # Start services
    log "Starting all services..."
    if ! docker-compose up -d; then
        error "Failed to start services!"
        exit 1
    fi

    # Check services
    log "Verifying services..."
    docker-compose ps

    # Optional: Check application health
    log "Waiting for application to start..."
    sleep 5
    if curl -s -f http://localhost:8000/health > /dev/null; then
        log "Application is healthy!"
    else
        warn "Application health check failed. Please check the logs:"
        docker-compose logs app
    fi
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
