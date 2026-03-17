#!/usr/bin/env bash
set -euo pipefail

# ClassGen production deploy script
# Usage: ./deploy.sh [setup|update|logs|status|stop]
#
# First-time setup:
#   1. Copy .env.prod.example to .env.prod and fill in values
#   2. Run: ./deploy.sh setup
#
# Subsequent deploys:
#   Run: ./deploy.sh update

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE="docker compose -f $SCRIPT_DIR/docker-compose.prod.yml"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[deploy]${NC} $*"; }
warn() { echo -e "${YELLOW}[deploy]${NC} $*"; }
err() { echo -e "${RED}[deploy]${NC} $*" >&2; }

check_env() {
    if [ ! -f "$SCRIPT_DIR/.env.prod" ]; then
        err ".env.prod not found. Copy .env.prod.example and fill in values:"
        err "  cp $SCRIPT_DIR/.env.prod.example $SCRIPT_DIR/.env.prod"
        exit 1
    fi

    # Check required vars
    local missing=0
    for var in DOMAIN OPENROUTER_API_KEY SUPABASE_URL SUPABASE_KEY; do
        if ! grep -q "^${var}=.\+" "$SCRIPT_DIR/.env.prod"; then
            err "Missing required: $var"
            missing=1
        fi
    done
    if [ $missing -eq 1 ]; then
        exit 1
    fi

    # Load DOMAIN for display
    export $(grep '^DOMAIN=' "$SCRIPT_DIR/.env.prod" | head -1)
    log "Domain: $DOMAIN"
}

cmd_setup() {
    log "First-time setup..."
    check_env

    log "Building and starting services..."
    $COMPOSE up -d --build

    log "Waiting for health check..."
    sleep 5

    if $COMPOSE exec -T app python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" 2>/dev/null; then
        log "App is healthy!"
    else
        warn "App may still be starting. Check: $0 logs"
    fi

    echo ""
    log "Setup complete!"
    log "  App:   https://$DOMAIN"
    log "  Health: https://$DOMAIN/health"
    log "  Logs:  $0 logs"
    echo ""
    warn "Next steps:"
    warn "  1. Set Twilio webhook URL to: https://$DOMAIN/webhook/twilio"
    warn "  2. Run Supabase migrations (init.sql) on your Supabase project"
}

cmd_update() {
    log "Updating..."
    check_env

    log "Pulling latest code and rebuilding..."
    cd "$SCRIPT_DIR/.."
    git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || true
    cd "$SCRIPT_DIR"

    $COMPOSE up -d --build

    log "Waiting for health check..."
    sleep 5
    $COMPOSE ps

    log "Update complete. Check: $0 logs"
}

cmd_logs() {
    $COMPOSE logs -f --tail=100 "${2:-}"
}

cmd_status() {
    $COMPOSE ps
    echo ""
    # Health check
    if $COMPOSE exec -T app python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').read().decode())" 2>/dev/null; then
        log "App is healthy"
    else
        err "App health check failed"
    fi
}

cmd_stop() {
    warn "Stopping all services..."
    $COMPOSE down
    log "Stopped."
}

case "${1:-help}" in
    setup)  cmd_setup ;;
    update) cmd_update ;;
    logs)   cmd_logs "$@" ;;
    status) cmd_status ;;
    stop)   cmd_stop ;;
    *)
        echo "Usage: $0 {setup|update|logs|status|stop}"
        echo ""
        echo "  setup   First-time deploy (build + start + health check)"
        echo "  update  Pull latest code, rebuild, restart"
        echo "  logs    Tail container logs (optional: logs app|caddy|redis)"
        echo "  status  Show running containers + health"
        echo "  stop    Stop all services"
        ;;
esac
