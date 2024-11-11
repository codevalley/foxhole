# Foxhole Deployment Documentation

The deployment script (`deploy.sh`) automates the setup and maintenance of your Foxhole application deployment, handling everything from Docker installation to SSL certificate management.

## Prerequisites

- Root access on the deployment server
- Git installed
- Domain name pointing to your server
- Valid email address for SSL certificates

## Usage

```bash
./deploy.sh [domain] [email] [options]
```

### Arguments

- `domain`: Your domain name (e.g., example.com)
- `email`: Email address for SSL certificate notifications

### Options

- `--help, -h`: Show help message
- `--docker`: Install Docker and Docker Compose
- `--fetch-code`: Pull latest code from git repository, update git repository before deployment (restores and pulls)
- `--setup-ssl`: Setup/renew SSL certificates
- `--force-ssl`: Force SSL certificate renewal

### Common Use Cases

1. First-time deployment:
```bash
sudo ./deploy.sh example.com admin@example.com --docker --setup-ssl
```

2. Update deployment with latest code:
```bash
sudo ./deploy.sh example.com admin@example.com --fetch-code
```

3. Renew SSL certificates:
```bash
sudo ./deploy.sh example.com admin@example.com --setup-ssl --force-ssl
```

### Components Set Up by the Script

1. **Docker Environment**
   - Installs Docker and Docker Compose if needed
   - Sets up proper permissions

2. **Application**
   - Creates necessary directories
   - Sets up environment variables
   - Builds and starts application containers

3. **SSL Certificates**
   - Generates SSL certificates using Let's Encrypt
   - Configures automatic renewal
   - Sets up Nginx with SSL

4. **Data Persistence**
   - Creates data directories for DB, MinIO, and Redis
   - Sets appropriate permissions
   - Ensures proper volume mounting

### Directory Structure Created

```
/
├── data/
│   ├── db/
│   ├── minio/
│   └── redis/
├── certbot/
│   ├── conf/
│   └── www/
└── nginx.conf
```

### Monitoring and Maintenance

- View logs: `docker-compose logs -f`
- Restart services: `docker-compose restart`
- Stop services: `docker-compose down`
- Start services: `docker-compose up -d`

### Troubleshooting

1. **SSL Certificate Issues**
   - Check certbot logs: `docker-compose logs certbot`
   - Force renew: Use `--force-ssl` option

2. **Application Issues**
   - Check application logs: `docker-compose logs app`
   - Verify `.env` configuration
   - Check data directory permissions

3. **Nginx Issues**
   - Check nginx logs: `docker-compose logs nginx`
   - Verify nginx.conf configuration

## Notes

- Always backup data before major updates
- Keep track of SSL certificate expiration dates
- Monitor disk space usage in data directories
- Regular updates recommended for security
