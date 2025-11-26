#!/usr/bin/env bash
#
# Common Utilities Library
#
# This library provides:
# - Color codes for output formatting
# - Print functions for status, success, error, and warning messages
# - Help documentation
# - Global output collector for deployment information
# - Utility functions
#

# Color codes for pretty output
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly RED='\033[0;31m'
readonly TEAL='\033[0;36m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

# Global output collector for deployment information
declare -A DEPLOYMENT_OUTPUT=(
    [frontend_url]=""
    [backend_url]=""
    [frontend_webhook]=""
    [backend_webhook]=""
    [secret_key_generated]=""
    [backend_cors_origins]=""
    [domain]=""
    [vite_api_url]=""
    [github_webhooks_configured]=""
)

#############################################
# Print Functions
#############################################

# Function to print colored status messages
print_status() {
    echo -e "${TEAL}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}==>${NC} $1"
}

print_error() {
    echo -e "${RED}==>${NC} $1" >&2
}

print_warning() {
    echo -e "${YELLOW}==>${NC} $1"
}

#############################################
# Output Collection Functions
#############################################

# Function to add deployment output
add_deployment_output() {
    local key=$1
    local value=$2
    DEPLOYMENT_OUTPUT[$key]="$value"
}

# Function to print deployment summary
print_deployment_summary() {
    echo
    print_success "Deployment completed successfully!"
    echo
    echo -e "${TEAL}═══════════════════════════════════════════════════${NC}"
    echo -e "${TEAL}           DEPLOYMENT SUMMARY${NC}"
    echo -e "${TEAL}═══════════════════════════════════════════════════${NC}"
    echo
    
    # Application URLs
    if [[ -n "${DEPLOYMENT_OUTPUT[frontend_url]}" ]]; then
        echo -e "${GREEN}Frontend URL:${NC}"
        echo "  https://${DEPLOYMENT_OUTPUT[frontend_url]}"
        echo
    fi
    
    if [[ -n "${DEPLOYMENT_OUTPUT[backend_url]}" ]]; then
        echo -e "${GREEN}Backend URL:${NC}"
        echo "  https://${DEPLOYMENT_OUTPUT[backend_url]}"
        echo
    fi
    
    # Webhooks
    if [[ "${DEPLOYMENT_OUTPUT[github_webhooks_configured]}" == "true" ]]; then
        print_success "GitHub webhooks have been configured automatically!"
        echo
    else
        if [[ -n "${DEPLOYMENT_OUTPUT[frontend_webhook]}" ]]; then
            echo -e "${GREEN}Frontend Webhook URL:${NC}"
            echo "  ${DEPLOYMENT_OUTPUT[frontend_webhook]}"
            echo
        fi
        
        if [[ -n "${DEPLOYMENT_OUTPUT[backend_webhook]}" ]]; then
            echo -e "${GREEN}Backend Webhook URL:${NC}"
            echo "  ${DEPLOYMENT_OUTPUT[backend_webhook]}"
            echo
        fi
        
        if [[ -n "${DEPLOYMENT_OUTPUT[frontend_webhook]}" || -n "${DEPLOYMENT_OUTPUT[backend_webhook]}" ]]; then
            print_status "Please add these webhook URLs to your GitHub repository"
            echo
        fi
    fi
    
    # Generated secrets
    if [[ -n "${DEPLOYMENT_OUTPUT[secret_key_generated]}" ]]; then
        echo -e "${YELLOW}⚠️  IMPORTANT: Save this SECRET_KEY for future reference:${NC}"
        echo -e "${GREEN}SECRET_KEY=${DEPLOYMENT_OUTPUT[secret_key_generated]}${NC}"
        echo
    fi
    
    # Build status note
    if [[ -n "${DEPLOYMENT_OUTPUT[frontend_url]}" && -n "${DEPLOYMENT_OUTPUT[backend_url]}" ]]; then
        echo -e "${BLUE}Note: Builds may take a few minutes to complete.${NC}"
        echo "Once builds are finished, your application will be accessible at the URLs above."
        echo
    fi
    
    echo -e "${TEAL}═══════════════════════════════════════════════════${NC}"
    echo
}

#############################################
# Utility Functions
#############################################

# Function to determine if a variable is sensitive
is_sensitive_var() {
    local var_name=$1
    local sensitive_vars=("PASSWORD" "SECRET" "KEY" "TOKEN" "SID")
    
    for sensitive in "${sensitive_vars[@]}"; do
        if [[ "$var_name" == *"$sensitive"* ]]; then
            return 0
        fi
    done
    
    return 1
}

# Function to show help
show_help() {
    echo -e "
${TEAL}OpenShift Deployment Script${NC}

${GREEN}DESCRIPTION:${NC}
    Deploys a full-stack application (Frontend, Backend, PostgreSQL) to OpenShift.
    All configuration is loaded from the .env.production file.

${GREEN}USAGE:${NC}
    $0 [OPTIONS]

${GREEN}OPTIONS:${NC}
    -h, --help              Show this help message and exit
    --env-file PATH         Specify custom environment file (default: scripts/.env.production)
    --reset-prod-db         Reset production database (deletes and recreates PostgreSQL storage)
    --regenerate-ssh-key    Delete and regenerate SSH keys for GitHub access

${GREEN}REQUIRED ENVIRONMENT VARIABLES:${NC}
    Main Variables:
        APP_NAME                    Application name (lowercase, alphanumeric, hyphens)
        PROJECT_NAME                OpenShift project name (lowercase, alphanumeric, hyphens)
        GIT_SSH_URL                 Git repository SSH URL (e.g., git@github.com:user/repo.git)
        FIRST_SUPERUSER             Admin email address
        FIRST_SUPERUSER_PASSWORD    Admin password (min 8 characters)
        SIGNUP_ACCESS_PASSWORD      Signup password (min 8 characters, can be empty)
        API_KEY                     Backend API key (16, 32, or 64 characters)
        ENVIRONMENT                 Environment name (e.g., production)
        SECRET_KEY                  Backend secret key (min 8 characters)
        
    Database Variables:
        POSTGRES_SERVER             PostgreSQL server hostname
        POSTGRES_PORT               PostgreSQL port
        POSTGRES_DB                 Database name
        POSTGRES_USER               Database user
        POSTGRES_PASSWORD           Database password (min 8 characters)

${GREEN}OPTIONAL ENVIRONMENT VARIABLES:${NC}
    GITHUB_TOKEN                GitHub Personal Access Token (for webhook automation)
    BACKEND_CORS_ORIGINS        CORS origins (auto-generated if not provided)
    VITE_*                      Any variable prefixed with VITE_ is injected into frontend

${GREEN}EXAMPLES:${NC}
    # Normal deployment
    $0

    # Use custom env file
    $0 --env-file /path/to/.env.custom

    # Reset database and deploy
    $0 --reset-prod-db

    # Regenerate SSH keys
    $0 --regenerate-ssh-key

${GREEN}PREREQUISITES:${NC}
    - OpenShift CLI (oc) version 4.14 or higher
    - Logged into OpenShift cluster (oc login)
    - .env.production file with all required variables
    - GitHub deploy key configured (or will be prompted)

${GREEN}DOCUMENTATION:${NC}
    For detailed documentation, see scripts/README.md
"
}

# Made with Bob
