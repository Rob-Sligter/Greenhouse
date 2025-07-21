#!/bin/bash

# Greenhouse Monitoring System - Management Script

set -e

COMPOSE_FILE="docker-compose.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

# Check if docker-compose.yml exists
check_compose_file() {
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "docker-compose.yml not found in current directory."
        exit 1
    fi
}

# Start the greenhouse system
start_system() {
    print_status "Starting Greenhouse Monitoring System..."
    docker compose up -d
    
    print_success "System started successfully!"
    print_status "Services available at:"
    echo "  - Grafana Dashboard: http://$(hostname -I | awk '{print $1}'):3000 (admin/admin)"
    echo "  - InfluxDB: http://$(hostname -I | awk '{print $1}'):8086"
    echo "  - Webhook API: http://$(hostname -I | awk '{print $1}'):5000/receive"
    echo "  - Manual Watering: http://$(hostname -I | awk '{print $1}'):8080"
}

# Stop the greenhouse system
stop_system() {
    print_status "Stopping Greenhouse Monitoring System..."
    docker compose down
    print_success "System stopped successfully!"
}

# Restart the greenhouse system
restart_system() {
    print_status "Restarting Greenhouse Monitoring System..."
    docker compose restart
    print_success "System restarted successfully!"
}

# Show system status
show_status() {
    print_status "Greenhouse Monitoring System Status:"
    docker compose ps
}

# Show logs
show_logs() {
    if [ -n "$2" ]; then
        print_status "Showing logs for service: $2"
        docker compose logs -f "$2"
    else
        print_status "Showing logs for all services:"
        docker compose logs -f
    fi
}

# Update and rebuild system
update_system() {
    print_status "Updating Greenhouse Monitoring System..."
    docker compose down
    docker compose build --no-cache
    docker compose up -d
    print_success "System updated successfully!"
}

# Backup data
backup_data() {
    BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    print_status "Creating backup in $BACKUP_DIR..."
    
    # Backup InfluxDB
    docker exec greenhouse_influxdb influxd backup -portable /tmp/influx_backup 2>/dev/null || true
    docker cp greenhouse_influxdb:/tmp/influx_backup "$BACKUP_DIR/" 2>/dev/null || true
    
    # Backup Grafana
    docker exec greenhouse_grafana tar czf /tmp/grafana_backup.tar.gz /var/lib/grafana 2>/dev/null || true
    docker cp greenhouse_grafana:/tmp/grafana_backup.tar.gz "$BACKUP_DIR/" 2>/dev/null || true
    
    print_success "Backup created in $BACKUP_DIR"
}

# Show help
show_help() {
    echo "Greenhouse Monitoring System - Management Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start the greenhouse monitoring system"
    echo "  stop      Stop the greenhouse monitoring system"
    echo "  restart   Restart the greenhouse monitoring system"
    echo "  status    Show status of all services"
    echo "  logs      Show logs (optional: specify service name)"
    echo "  update    Update and rebuild the system"
    echo "  backup    Create a backup of data"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 logs sensor_collector"
    echo "  $0 status"
}

# Main script logic
main() {
    check_docker
    check_compose_file
    
    case "${1:-help}" in
        start)
            start_system
            ;;
        stop)
            stop_system
            ;;
        restart)
            restart_system
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$@"
            ;;
        update)
            update_system
            ;;
        backup)
            backup_data
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run the main function with all arguments
main "$@"
