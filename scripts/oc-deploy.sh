#!/bin/bash
#
# OpenShift Deployment Script (Optimized)
#
# This script deploys an application to OpenShift with the following features:
# - Idempotent operations (can be run multiple times without side effects)
# - Variables loaded dynamically from .env.production file
# - Comprehensive validation for all required variables
# - Best practices for bash scripting
# - Sensitive values are masked in output
# - Dynamic secret creation from environment variables
# - Automatic VITE_ prefix injection for frontend
# - SSH key management with GitHub deploy key verification
# - Database reset functionality
# - GitHub webhook automation
#
# Usage: ./oc-deploy.sh [OPTIONS]
#
# For detailed documentation, see scripts/README.md
#

set -eo pipefail

# Default environment file location
ENV_FILE="$(dirname "$0")/.env.production"

# Default GitHub host (can be overridden in .env.production)
# Set to github.ibm.com for IBM GitHub Enterprise
# Set to github.com for public GitHub
DEFAULT_GITHUB_HOST="github.ibm.com"

# Flags
RESET_PROD_DB=false
REGENERATE_SSH_KEY=false
SHOW_HELP=false

# Color codes for pretty output
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly RED='\033[0;31m'
readonly TEAL='\033[0;36m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

# Required main environment variables
declare -a REQUIRED_VARS=(
    "APP_NAME"
    "PROJECT_NAME"
    "GIT_SSH_URL"
    "FIRST_SUPERUSER"
    "FIRST_SUPERUSER_PASSWORD"
    "SIGNUP_ACCESS_PASSWORD"
    "API_KEY"
    "ENVIRONMENT"
    "SECRET_KEY"
    "POSTGRES_SERVER"
    "POSTGRES_PORT"
    "POSTGRES_DB"
    "POSTGRES_USER"
    "POSTGRES_PASSWORD"
)

# Function to get validation function for a variable
get_validation_function() {
    local var_name=$1
    case "$var_name" in
        APP_NAME|PROJECT_NAME)
            echo "validate_name"
            ;;
        GIT_SSH_URL)
            echo "validate_git_url"
            ;;
        FIRST_SUPERUSER)
            echo "validate_email"
            ;;
        API_KEY)
            echo "validate_api_key"
            ;;
        *)
            echo ""
            ;;
    esac
}

# Variables that need password length validation (min 8 chars)
declare -a PASSWORD_VARS=(
    "FIRST_SUPERUSER_PASSWORD"
    "POSTGRES_PASSWORD"
    "SECRET_KEY"
)

#############################################
# Helper Functions
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

#############################################
# Validation Functions
#############################################

# Function to validate project/app name
validate_name() {
    local name=$1
    if [[ ! $name =~ ^[a-z0-9-]+$ ]]; then
        print_error "Invalid name: '$name'. Must contain only lowercase letters, numbers, and hyphens."
        return 1
    fi
    return 0
}

# Function to validate email
validate_email() {
    local email=$1
    if [[ ! $email =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; then
        print_error "Invalid email: '$email'"
        return 1
    fi
    return 0
}

# Function to validate git SSH URL
validate_git_url() {
    local url=$1
    # Check if URL starts with git@ or ssh:// and ends with .git
    if [[ ! $url =~ ^(git@|ssh://).+\.git$ ]]; then
        print_error "Invalid Git SSH URL: '$url'. Must start with 'git@' or 'ssh://' and end with '.git'"
        return 1
    fi
    return 0
}

# Function to validate API key (min length 16, must be power of 2: 16, 32, 64)
validate_api_key() {
    local key=$1
    local length=${#key}
    
    if [[ $length -lt 16 ]]; then
        print_error "API key must be at least 16 characters long (current: $length)"
        return 1
    fi
    
    # Check if length is a power of 2 (16, 32, 64, 128, etc.)
    if [[ $length -ne 16 && $length -ne 32 && $length -ne 64 && $length -ne 128 && $length -ne 256 ]]; then
        print_error "API key length must be a power of 2 (16, 32, 64, 128, 256). Current length: $length"
        return 1
    fi
    
    return 0
}

# Function to validate password length (min 8 characters)
validate_password_length() {
    local password=$1
    local var_name=$2
    
    if [[ ${#password} -lt 8 ]]; then
        print_error "$var_name must be at least 8 characters long (current: ${#password})"
        return 1
    fi
    
    return 0
}

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

#############################################
# Environment Loading Functions
#############################################

# Function to load environment variables from file
load_env_file() {
    local env_file=$1
    
    if [[ ! -f "$env_file" ]]; then
        print_error "Environment file $env_file not found!"
        print_error "Please create $env_file with all required variables."
        print_error "See scripts/.env.production.example for reference."
        return 1
    fi
    
    print_status "Loading environment variables from $env_file"
    
    # Load variables from env file without executing any code
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Skip comments and empty lines
        [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
        
        # Extract variable name and value
        if [[ "$line" =~ ^([A-Za-z0-9_]+)=(.*)$ ]]; then
            var_name="${BASH_REMATCH[1]}"
            var_value="${BASH_REMATCH[2]}"
            
            # Remove quotes if present
            var_value="${var_value#\"}"
            var_value="${var_value%\"}"
            var_value="${var_value#\'}"
            var_value="${var_value%\'}"
            
            # Export the variable
            export "$var_name"="$var_value"
            
            # Mask sensitive values in output
            if is_sensitive_var "$var_name"; then
                print_status "Loaded $var_name [value masked]"
            else
                print_status "Loaded $var_name=$var_value"
            fi
        fi
    done < "$env_file"
    
    return 0
}

# Function to validate all required variables
validate_required_vars() {
    local missing_vars=()
    local invalid_vars=()
    
    print_status "Validating required environment variables..."
    
    # Check if all required variables are set
    for var_name in "${REQUIRED_VARS[@]}"; do
        if [[ -z "${!var_name:-}" ]]; then
            missing_vars+=("$var_name")
        fi
    done
    
    # Report missing variables
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        print_error "The following required environment variables are missing:"
        for var_name in "${missing_vars[@]}"; do
            echo "  - $var_name"
        done
        print_error "Please add these variables to your environment file: $ENV_FILE"
        return 1
    fi
    
    # Validate specific variables
    local vars_to_validate=("APP_NAME" "PROJECT_NAME" "GIT_SSH_URL" "FIRST_SUPERUSER" "API_KEY")
    for var_name in "${vars_to_validate[@]}"; do
        local validation_func=$(get_validation_function "$var_name")
        local var_value="${!var_name:-}"
        
        if [[ -n "$validation_func" && -n "$var_value" ]]; then
            if ! $validation_func "$var_value"; then
                invalid_vars+=("$var_name")
            fi
        fi
    done
    
    # Validate password lengths
    for var_name in "${PASSWORD_VARS[@]}"; do
        local var_value="${!var_name:-}"
        
        # Skip empty optional passwords
        if [[ "$var_name" == "SIGNUP_ACCESS_PASSWORD" && -z "$var_value" ]]; then
            continue
        fi
        
        if [[ -n "$var_value" ]] && ! validate_password_length "$var_value" "$var_name"; then
            invalid_vars+=("$var_name")
        fi
    done
    
    # Report invalid variables
    if [[ ${#invalid_vars[@]} -gt 0 ]]; then
        print_error "The following environment variables have invalid values:"
        for var_name in "${invalid_vars[@]}"; do
            echo "  - $var_name"
        done
        return 1
    fi
    
    print_success "All required environment variables are valid!"
    return 0
}

#############################################
# OpenShift Helper Functions
#############################################

# Function to check if a resource exists
resource_exists() {
    local resource_type=$1
    local resource_name=$2
    
    oc get "$resource_type" "$resource_name" &>/dev/null
    return $?
}

# Function to create or update a resource from a heredoc
apply_resource() {
    local resource_content=$1
    local resource_type
    local resource_name
    
    # Extract resource type and name from the content
    resource_type=$(echo "$resource_content" | grep -E "^kind:" | awk '{print $2}' | tr '[:upper:]' '[:lower:]')
    resource_name=$(echo "$resource_content" | grep -E "^  name:" | head -1 | awk '{print $2}')
    
    if [[ -z "$resource_type" || -z "$resource_name" ]]; then
        print_error "Could not determine resource type or name"
        return 1
    fi
    
    print_status "Applying $resource_type/$resource_name..."
    echo "$resource_content" | oc apply -f -
    return $?
}

# Check OpenShift client version
check_oc_version() {
    print_status "Checking OpenShift client version..."
    local oc_version
    oc_version=$(oc version 2>/dev/null | grep "Client Version:" | awk '{print $3}' | cut -d'.' -f2)
    
    if [ -z "$oc_version" ] || [ "$oc_version" -lt "14" ]; then
        print_error "OpenShift client version 4.14 or higher is required"
        print_error "Current version: $(oc version 2>/dev/null | grep "Client Version:")"
        return 1
    fi
    
    print_success "OpenShift client version is compatible"
    return 0
}

# Check OpenShift login status
check_oc_login() {
    print_status "Checking OpenShift instance and login status..."
    
    if ! oc whoami --show-server &>/dev/null || ! oc whoami &>/dev/null; then
        print_error "Not logged into OpenShift. Please login first using:"
        echo "oc login --token=<token> --server=<server-url>"
        return 1
    fi
    
    OPENSHIFT_SERVER=$(oc whoami --show-server)
    echo -e "${TEAL}You are about to deploy to:${NC}"
    echo -e "${TEAL}$OPENSHIFT_SERVER${NC}"
    read -p "Do you want to continue? (y/n): " CONTINUE
    
    if [[ ! $CONTINUE =~ ^[Yy]$ ]]; then
        print_error "Deployment cancelled"
        return 1
    fi
    
    return 0
}

#############################################
# Project Setup Functions
#############################################

# Function to handle project creation or selection
setup_project() {
    # Check if project exists
    if resource_exists "project" "$PROJECT_NAME"; then
        print_status "Project '$PROJECT_NAME' already exists."
        read -p "Do you want to switch to this project and continue deployment? (y/n): " USE_EXISTING
        if [[ $USE_EXISTING =~ ^[Yy]$ ]]; then
            oc project "$PROJECT_NAME" || {
                print_error "Failed to switch to project"
                return 1
            }
        else
            print_error "Deployment cancelled"
            return 1
        fi
    else
        # Create new project
        print_status "Creating new project '$PROJECT_NAME'..."
        oc new-project "$PROJECT_NAME" || {
            print_error "Failed to create project"
            return 1
        }
    fi
    
    return 0
}

#############################################
# SSH Key Management Functions
#############################################

# Function to check if deploy key exists on GitHub
check_github_deploy_key() {
    local repo_url=$1
    local public_key=$2
    local github_host="${GITHUB_HOST:-$DEFAULT_GITHUB_HOST}"
    
    # Extract owner and repo from SSH URL
    # Format: git@github.com:owner/repo.git or git@github.ibm.com:owner/repo.git
    if [[ $repo_url =~ git@[^:]+:([^/]+)/(.+)\.git ]]; then
        local owner="${BASH_REMATCH[1]}"
        local repo="${BASH_REMATCH[2]}"
        
        # Check if GITHUB_TOKEN is available
        if [[ -z "${GITHUB_TOKEN:-}" ]]; then
            print_warning "GITHUB_TOKEN not set. Cannot verify deploy key automatically."
            return 1
        fi
        
        # Query GitHub API for deploy keys
        local response
        local http_code
        response=$(curl -s -w "\n%{http_code}" -H "Authorization: token $GITHUB_TOKEN" \
            "https://api.$github_host/repos/$owner/$repo/keys")
        
        http_code=$(echo "$response" | tail -n1)
        response=$(echo "$response" | sed '$d')
        
        # Check for API errors
        if [[ "$http_code" != "200" ]]; then
            print_warning "Failed to check deploy keys (HTTP $http_code). API response:"
            echo "$response" | head -n 5
            return 1
        fi
        
        # Check if the public key exists
        if echo "$response" | grep -q "$(echo "$public_key" | awk '{print $2}')"; then
            return 0
        fi
    fi
    
    return 1
}

# Function to add deploy key to GitHub
add_github_deploy_key() {
    local repo_url=$1
    local public_key=$2
    local key_title="OpenShift Deploy Key - $(date +%Y%m%d)"
    local github_host="${GITHUB_HOST:-$DEFAULT_GITHUB_HOST}"
    
    # Extract owner and repo from SSH URL
    if [[ $repo_url =~ git@[^:]+:([^/]+)/(.+)\.git ]]; then
        local owner="${BASH_REMATCH[1]}"
        local repo="${BASH_REMATCH[2]}"
        
        # Check if GITHUB_TOKEN is available
        if [[ -z "${GITHUB_TOKEN:-}" ]]; then
            print_warning "GITHUB_TOKEN not set. Cannot add deploy key automatically."
            return 1
        fi
        
        print_status "Adding deploy key to GitHub repository ($github_host)..."
        
        # Add deploy key via GitHub API
        local response
        local http_code
        response=$(curl -s -w "\n%{http_code}" -X POST \
            -H "Authorization: Bearer $GITHUB_TOKEN" \
            -H "Accept: application/vnd.github+json" \
            -H "X-GitHub-Api-Version: 2022-11-28" \
            "https://api.$github_host/repos/$owner/$repo/keys" \
            -d "{\"title\":\"$key_title\",\"key\":\"$public_key\",\"read_only\":false}")
        
        http_code=$(echo "$response" | tail -n1)
        response=$(echo "$response" | sed '$d')
        
        if [[ "$http_code" == "201" ]] && echo "$response" | grep -q '"id"'; then
            print_success "Deploy key added to GitHub successfully!"
            return 0
        else
            print_error "Failed to add deploy key to GitHub (HTTP $http_code)"
            print_error "API Response:"
            echo "$response" | jq '.' 2>/dev/null || echo "$response"
            
            # Provide helpful error messages
            if echo "$response" | grep -q "key is already in use"; then
                print_warning "This SSH key is already registered. You may need to use --regenerate-ssh-key"
            elif [[ "$http_code" == "401" ]]; then
                print_error "Authentication failed. Check your GITHUB_TOKEN permissions."
            elif [[ "$http_code" == "404" ]]; then
                print_error "Repository not found. Check GIT_SSH_URL and token permissions."
            fi
            return 1
        fi
    fi

    print_error "Invalid GIT_SSH_URL format. Expected: git@$github_host:owner/repo.git"
    
    return 1
}

# Function to delete SSH keys
delete_ssh_keys() {
    local key_path="$HOME/.ssh/$PROJECT_NAME/ocp-key"
    local pub_key_path="$HOME/.ssh/$PROJECT_NAME/ocp-key.pub"
    local github_host="${GITHUB_HOST:-$DEFAULT_GITHUB_HOST}"
    
    print_status "Deleting SSH keys..."
    
    # Delete local keys
    if [[ -f "$key_path" ]]; then
        rm -f "$key_path"
        print_status "Deleted local private key"
    fi
    
    if [[ -f "$pub_key_path" ]]; then
        local public_key
        public_key=$(cat "$pub_key_path")
        rm -f "$pub_key_path"
        print_status "Deleted local public key"
        
        # Delete from GitHub if GITHUB_TOKEN is available
        if [[ -n "${GITHUB_TOKEN:-}" && $GIT_SSH_URL =~ git@[^:]+:([^/]+)/(.+)\.git ]]; then
            local owner="${BASH_REMATCH[1]}"
            local repo="${BASH_REMATCH[2]}"
            
            # Get all deploy keys
            local keys_response
            local http_code
            keys_response=$(curl -s -w "\n%{http_code}" -H "Authorization: token $GITHUB_TOKEN" \
                "https://api.$github_host/repos/$owner/$repo/keys")
            
            http_code=$(echo "$keys_response" | tail -n1)
            keys_response=$(echo "$keys_response" | sed '$d')
            
            if [[ "$http_code" != "200" ]]; then
                print_warning "Failed to retrieve deploy keys from GitHub (HTTP $http_code)"
            else
                # Find and delete matching key
                local key_id
                key_id=$(echo "$keys_response" | jq -r ".[] | select(.key | contains(\"$(echo "$public_key" | awk '{print $2}')\")) | .id" 2>/dev/null)
                
                if [[ -n "$key_id" ]]; then
                    local delete_response
                    delete_response=$(curl -s -w "\n%{http_code}" -X DELETE \
                        -H "Authorization: token $GITHUB_TOKEN" \
                        "https://api.$github_host/repos/$owner/$repo/keys/$key_id")
                    
                    local delete_code=$(echo "$delete_response" | tail -n1)
                    if [[ "$delete_code" == "204" ]]; then
                        print_status "Deleted deploy key from GitHub"
                    else
                        print_warning "Failed to delete deploy key from GitHub (HTTP $delete_code)"
                    fi
                else
                    print_status "Deploy key not found on GitHub (may have been already deleted)"
                fi
            fi
        fi
    fi
    
    # Delete from OpenShift
    if resource_exists "secret" "git-secret"; then
        oc delete secret git-secret
        print_status "Deleted git-secret from OpenShift"
    fi
    
    print_success "SSH keys deleted successfully"
    return 0
}

# Function to create SSH keys for Git access
setup_ssh_keys() {
    mkdir -p "$HOME/.ssh/$PROJECT_NAME"
    local key_path="$HOME/.ssh/$PROJECT_NAME/ocp-key"
    local pub_key_path="$HOME/.ssh/$PROJECT_NAME/ocp-key.pub"
    local need_user_input=false
    
    # Check if keys exist and are valid
    if [[ -f "$key_path" && -f "$pub_key_path" ]]; then
        print_status "SSH key pair already exists in ~/.ssh/$PROJECT_NAME/"
        
        # Check if deploy key exists on GitHub
        local public_key
        public_key=$(cat "$pub_key_path")
        
        if check_github_deploy_key "$GIT_SSH_URL" "$public_key"; then
            print_success "Deploy key is already configured on GitHub"
        else
            print_warning "Deploy key not found on GitHub"
            need_user_input=true
        fi
    else
        # Generate new keys
        print_status "Generating new SSH key pair..."
        ssh-keygen -N '' -f "$key_path" -C "openshift-deploy-key" -q <<< y > /dev/null
        print_success "SSH key pair generated"
        need_user_input=true
    fi
    
    # Display the public key
    local public_key
    public_key=$(cat "$pub_key_path")
    print_status "Public SSH key for repository access:"
    echo -e "${TEAL}$public_key${NC}"
    
    # Try to add deploy key automatically
    if [[ "$need_user_input" == "true" ]]; then
        if add_github_deploy_key "$GIT_SSH_URL" "$public_key"; then
            print_success "Deploy key configured automatically"
        else
            print_warning "Could not add deploy key automatically"
            print_status "${GREEN}Please add this public key to your GitHub repository as a deploy key${NC}"
            read -p "Press enter once you've added the deploy key..."
        fi
    fi
    
    # Create or update OpenShift secret
    if resource_exists "secret" "git-secret"; then
        print_status "Updating git-secret..."
        oc delete secret git-secret
    fi
    
    print_status "Creating OpenShift secret..."
    oc create secret generic git-secret \
        --from-file=ssh-privatekey="$key_path" \
        --type=kubernetes.io/ssh-auth
    
    return 0
}

#############################################
# Secret Management Functions
#############################################

# Function to build dynamic secret creation command
build_secret_literals() {
    local secret_literals=""
    
    # Read all variables from env file
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Skip comments and empty lines
        [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
        
        # Extract variable name and value
        if [[ "$line" =~ ^([A-Za-z0-9_]+)=(.*)$ ]]; then
            local var_name="${BASH_REMATCH[1]}"
            local var_value="${!var_name:-}"
            
            # Add to secret literals
            secret_literals+=" --from-literal=$var_name=\"$var_value\""
        fi
    done < "$ENV_FILE"
    
    echo "$secret_literals"
}

# Function to get all VITE_ prefixed variables
get_vite_variables() {
    local vite_vars=""
    
    # Get all exported variables
    while IFS='=' read -r name value; do
        if [[ $name == VITE_* ]]; then
            vite_vars+=" --from-literal=$name=\"$value\""
        fi
    done < <(env)
    
    echo "$vite_vars"
}

# Function to create initial application environment secret
create_initial_app_env_secret() {
    local secret_name="$APP_NAME-env"
    local secret_key_generated=false
    
    # Generate a secure random secret key if not provided or too short
    if [[ -z "${SECRET_KEY:-}" ]] || [[ ${#SECRET_KEY} -lt 8 ]]; then
        SECRET_KEY=$(openssl rand -hex 32)
        export SECRET_KEY
        secret_key_generated=true
        print_success "Generated secure secret key for backend"
        echo -e "${YELLOW}IMPORTANT: Save this SECRET_KEY for future reference:${NC}"
        echo -e "${GREEN}SECRET_KEY=$SECRET_KEY${NC}"
        echo
    fi
    
    # Create or update application environment secret
    if resource_exists "secret" "$secret_name"; then
        print_status "Updating $secret_name secret..."
        oc delete secret "$secret_name"
    fi
    
    print_status "Creating initial application environment secret $secret_name..."
    
    # Build dynamic secret creation command
    local secret_cmd="oc create secret generic $secret_name"
    secret_cmd+=$(build_secret_literals)
    
    # Execute the command
    eval "$secret_cmd"
    
    return 0
}

# Function to update application environment secret with frontend/backend URLs
update_app_env_secret_with_urls() {
    local secret_name="$APP_NAME-env"
    local frontend_url
    local backend_url
    
    # Get the frontend and backend URLs from the routes
    frontend_url=$(oc get route frontend -o jsonpath='{.spec.host}' 2>/dev/null || echo "")
    backend_url=$(oc get route backend -o jsonpath='{.spec.host}' 2>/dev/null || echo "")
    
    if [[ -z "$frontend_url" || -z "$backend_url" ]]; then
        print_error "Could not get frontend or backend URLs. Make sure the routes are created."
        return 1
    fi
    
    print_status "Updating $secret_name secret with frontend and backend URLs..."
    
    # Set BACKEND_CORS_ORIGINS if not already set, or append backend URL if it exists
    if [[ -z "${BACKEND_CORS_ORIGINS:-}" ]]; then
        export BACKEND_CORS_ORIGINS="https://$frontend_url"
    else
        # Add backend URL to existing BACKEND_CORS_ORIGINS if not already present
        if [[ ! "$BACKEND_CORS_ORIGINS" =~ "https://$frontend_url" ]]; then
            export BACKEND_CORS_ORIGINS="$BACKEND_CORS_ORIGINS,https://$frontend_url"
            print_status "Added frontend URL to existing BACKEND_CORS_ORIGINS"
        fi
    fi
    
    # Set DOMAIN for backend
    export DOMAIN="$backend_url"
    
    # Set VITE_API_URL for frontend (also needed by backend if it serves frontend assets)
    export VITE_API_URL="https://$backend_url"
    
    # Delete the existing secret
    oc delete secret "$secret_name"
    
    # Recreate the secret with all values including URLs
    print_status "Recreating application environment secret with URLs..."
    local secret_cmd="oc create secret generic $secret_name"
    secret_cmd+=$(build_secret_literals)
    
    # Execute the command
    eval "$secret_cmd"
    
    print_success "Updated environment secret with frontend URL: https://$frontend_url and backend URL: https://$backend_url"
    return 0
}

#############################################
# Database Management Functions
#############################################

# Function to reset production database
reset_production_database() {
    print_warning "Resetting production database..."
    print_warning "This will DELETE all data in the PostgreSQL database!"
    read -p "Are you sure you want to continue? (yes/no): " CONFIRM
    
    if [[ "$CONFIRM" != "yes" ]]; then
        print_error "Database reset cancelled"
        return 1
    fi
    
    # Delete PostgreSQL deployment
    if resource_exists "deployment" "postgresql"; then
        print_status "Deleting PostgreSQL deployment..."
        oc delete deployment postgresql
    fi
    
    # Delete PostgreSQL service
    if resource_exists "service" "postgresql"; then
        print_status "Deleting PostgreSQL service..."
        oc delete service postgresql
    fi
    
    # Delete PVC
    if resource_exists "pvc" "postgresql-data"; then
        print_status "Deleting PostgreSQL PVC..."
        oc delete pvc postgresql-data
    fi
    
    print_success "Database storage deleted successfully"
    
    # Recreate database
    print_status "Recreating database..."
    deploy_database || return 1
    
    # Restart backend to apply migrations
    if resource_exists "deployment" "backend"; then
        print_status "Restarting backend to apply migrations..."
        oc rollout restart deployment/backend
        oc rollout status deployment/backend --timeout=300s
    fi
    
    print_success "Database reset completed successfully!"
    return 0
}

# Function to deploy PostgreSQL database
deploy_database() {
    local secret_name="$APP_NAME-env"
    print_status "Deploying PostgreSQL database..."
    
    # Create persistent volume claim for PostgreSQL if it doesn't exist
    if ! resource_exists "pvc" "postgresql-data"; then
        print_status "Creating persistent volume claim for PostgreSQL..."
        apply_resource "$(cat << EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgresql-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
EOF
)"
    else
        print_status "PVC postgresql-data already exists, skipping creation"
    fi
    
    # Check if PostgreSQL deployment exists
    local postgres_exists=false
    if resource_exists "deployment" "postgresql"; then
        postgres_exists=true
        print_status "PostgreSQL deployment already exists"
    fi
    
    # Deploy PostgreSQL using container image with values from secret
    print_status "Deploying PostgreSQL container using values from $secret_name secret..."
    apply_resource "$(cat << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgresql
  labels:
    app: postgresql
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgresql
  template:
    metadata:
      labels:
        app: postgresql
        name: postgresql
    spec:
      containers:
      - name: postgresql
        image: postgres:12
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: $secret_name
              key: POSTGRES_USER
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: $secret_name
              key: POSTGRES_PASSWORD
        - name: POSTGRES_DB
          valueFrom:
            secretKeyRef:
              name: $secret_name
              key: POSTGRES_DB
        - name: PGDATA
          value: "/var/lib/postgresql/data/pgdata"
        volumeMounts:
        - name: postgresql-data
          mountPath: "/var/lib/postgresql/data"
      volumes:
      - name: postgresql-data
        persistentVolumeClaim:
          claimName: postgresql-data
EOF
)"
    
    # Create PostgreSQL service if it doesn't exist
    if ! resource_exists "service" "postgresql"; then
        print_status "Creating PostgreSQL service..."
        apply_resource "$(cat << EOF
apiVersion: v1
kind: Service
metadata:
  name: postgresql
  labels:
    app: postgresql
spec:
  ports:
  - port: 5432
    targetPort: 5432
  selector:
    app: postgresql
EOF
)"
    else
        print_status "Service postgresql already exists, skipping creation"
    fi
    
    # If PostgreSQL deployment already existed, trigger a rollout restart to pick up new env vars
    if [[ "$postgres_exists" == "true" ]]; then
        print_status "Restarting PostgreSQL deployment to apply updated environment variables..."
        oc rollout restart deployment/postgresql
    fi
    
    print_status "Waiting for PostgreSQL to be ready..."
    # Wait for deployment to complete
    sleep 2  # Give OpenShift a moment to create resources
    oc rollout status deployment/postgresql --timeout=300s
    
    # Wait for the pod to be ready
    sleep 2
    local retries=0
    local max_retries=30
    while [[ $(oc get pods -l name=postgresql -o 'jsonpath={..status.conditions[?(@.type=="Ready")].status}') != "True" ]]; do
        print_status "Waiting for PostgreSQL pod to be ready..."
        sleep 5
        ((retries++))
        if [[ $retries -ge $max_retries ]]; then
            print_error "PostgreSQL pod did not become ready in time"
            return 1
        fi
    done
    
    print_success "PostgreSQL deployment completed successfully!"
    return 0
}

#############################################
# Application Deployment Functions
#############################################

# Function to configure buildconfig webhook branch filter
configure_buildconfig_branch_filter() {
    local buildconfig_name=$1
    local branch_filter="${WEBHOOK_BRANCH_FILTER:-}"
    
    if [[ -n "$branch_filter" ]]; then
        print_status "Configuring $buildconfig_name to build only from branch: $branch_filter"
        
        # Update the Git source ref to specify the branch
        if oc patch bc/$buildconfig_name --type=json -p "[
            {
                \"op\": \"add\",
                \"path\": \"/spec/source/git/ref\",
                \"value\": \"$branch_filter\"
            }
        ]" 2>&1; then
            print_success "Branch filter configured for $buildconfig_name (ref: $branch_filter)"
        else
            print_warning "Failed to configure branch filter for $buildconfig_name"
        fi
        
        # Add branch filter to webhook triggers using allowEnv
        # This ensures webhooks only trigger builds for the specified branch
        local trigger_count
        trigger_count=$(oc get bc/$buildconfig_name -o json | jq '.spec.triggers | length')
        
        for ((i=1; i<trigger_count; i++)); do
            local trigger_type
            trigger_type=$(oc get bc/$buildconfig_name -o json | jq -r ".spec.triggers[$i].type")
            
            if [[ "$trigger_type" == "GitHub" ]] || [[ "$trigger_type" == "Generic" ]]; then
                local trigger_key=$(echo "$trigger_type" | tr '[:upper:]' '[:lower:]')
                
                # Add allowEnv and env filter for the trigger
                oc patch bc/$buildconfig_name --type=json -p "[
                    {
                        \"op\": \"add\",
                        \"path\": \"/spec/triggers/$i/$trigger_key/allowEnv\",
                        \"value\": true
                    },
                    {
                        \"op\": \"add\",
                        \"path\": \"/spec/triggers/$i/$trigger_key/env\",
                        \"value\": [{\"name\": \"GIT_REF\", \"value\": \"refs/heads/$branch_filter\"}]
                    }
                ]" 2>/dev/null || print_warning "Could not add env filter to $trigger_type trigger at index $i"
            fi
        done
    fi
}

# Function to deploy frontend
deploy_frontend() {
    print_status "Deploying frontend..."
    
    # Check if frontend app already exists
    if resource_exists "buildconfig" "frontend"; then
        print_status "Frontend buildconfig already exists, triggering rollout restart..."
        # Just restart the deployment to pick up new environment variables
        # Don't rebuild unless explicitly requested
        if resource_exists "deployment" "frontend"; then
            oc rollout restart deployment/frontend
            oc rollout status deployment/frontend --timeout=300s
        else
            print_warning "Frontend deployment not found, skipping restart"
        fi
    else
        print_status "Creating new frontend application..."
        oc new-app --name=frontend --strategy=docker --context-dir=frontend --source-secret=git-secret "$GIT_SSH_URL"
    fi
    
    # Configure branch filter if specified
    configure_buildconfig_branch_filter "frontend"
    
    # Check if route exists
    if ! resource_exists "route" "frontend"; then
        print_status "Exposing frontend service..."
        oc create route edge frontend --service=frontend --port=8080
    else
        print_status "Frontend route already exists, skipping creation"
    fi
    
    return 0
}

# Function to deploy backend
deploy_backend() {
    print_status "Deploying backend..."
    
    # Check if backend app already exists
    if resource_exists "buildconfig" "backend"; then
        print_status "Backend buildconfig already exists, triggering rollout restart..."
        # Just restart the deployment to pick up new environment variables
        # Don't rebuild unless explicitly requested
        if resource_exists "deployment" "backend"; then
            oc rollout restart deployment/backend
            oc rollout status deployment/backend --timeout=300s
        else
            print_warning "Backend deployment not found, skipping restart"
        fi
    else
        print_status "Creating new backend application..."
        oc new-app --name=backend --strategy=docker --context-dir=backend --source-secret=git-secret "$GIT_SSH_URL"
    fi
    
    # Configure branch filter if specified
    configure_buildconfig_branch_filter "backend"
    
    # Check if route exists
    if ! resource_exists "route" "backend"; then
        print_status "Exposing backend service..."
        oc create route edge backend --service=backend --port=8000
    else
        print_status "Backend route already exists, skipping creation"
    fi
    
    return 0
}

# Function to configure frontend build with environment variables
configure_frontend() {
    local frontend_url
    local backend_url
    
    frontend_url=$(oc get route frontend -o jsonpath='{.spec.host}')
    backend_url=$(oc get route backend -o jsonpath='{.spec.host}')
    
    # Build VITE_ build arguments JSON array
    # Note: Vite embeds these at BUILD time, so they must be build args, not runtime env vars
    local vite_buildargs_json="["
    local first=true
    
    # Add VITE_API_URL
    vite_buildargs_json+="{\"name\":\"VITE_API_URL\",\"value\":\"https://$backend_url\"}"
    first=false
    
    # Add all VITE_ prefixed variables from .env.production file
    if [[ -f "$ENV_FILE" ]]; then
        while IFS= read -r line || [[ -n "$line" ]]; do
            # Skip comments and empty lines
            [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
            
            # Extract variable name and value
            if [[ "$line" =~ ^(VITE_[A-Za-z0-9_]+)=(.*)$ ]]; then
                local var_name="${BASH_REMATCH[1]}"
                local var_value="${BASH_REMATCH[2]}"
                
                # Remove quotes if present
                var_value="${var_value#\"}"
                var_value="${var_value%\"}"
                var_value="${var_value#\'}"
                var_value="${var_value%\'}"
                
                # Skip VITE_API_URL as we already added it
                if [[ "$var_name" != "VITE_API_URL" ]]; then
                    if [[ "$first" == "false" ]]; then
                        vite_buildargs_json+=","
                    fi
                    vite_buildargs_json+="{\"name\":\"$var_name\",\"value\":\"$var_value\"}"
                    first=false
                    print_status "Found $var_name in .env.production"
                fi
            fi
        done < "$ENV_FILE"
    fi
    
    vite_buildargs_json+="]"
    
    # Configure frontend build with all VITE_ variables as BUILD ARGS
    print_status "Configuring frontend build with VITE_ build arguments..."
    oc patch bc/frontend --type=merge -p "{\"spec\":{\"strategy\":{\"dockerStrategy\":{\"buildArgs\":$vite_buildargs_json}}}}"
    
    print_status "Restarting frontend build to apply build args..."
    oc cancel-build bc/frontend --state=new --state=pending --state=running 2>/dev/null || true
    oc start-build bc/frontend
    
    return 0
}

# Function to configure backend environment
configure_backend() {
    local secret_name="$APP_NAME-env"
    
    print_status "Applying backend environment from $secret_name secret..."
    oc patch deployment backend --patch "{\"spec\":{\"template\":{\"spec\":{\"containers\":[{\"name\":\"backend\",\"envFrom\":[{\"secretRef\":{\"name\":\"$secret_name\"}}]}]}}}}"
    
    return 0
}

# Function to group resources as one application
group_resources() {
    print_status "Grouping resources as one application..."
    oc label deployment/frontend deployment/backend deployment/postgresql app.kubernetes.io/part-of="$APP_NAME" --overwrite
    
    return 0
}

#############################################
# Webhook Management Functions
#############################################

# Function to create GitHub webhook
create_github_webhook() {
    local repo_url=$1
    local webhook_url=$2
    local webhook_type=$3  # "frontend" or "backend"
    local github_host="${GITHUB_HOST:-$DEFAULT_GITHUB_HOST}"
    
    # Extract owner and repo from SSH URL
    if [[ $repo_url =~ git@[^:]+:([^/]+)/(.+)\.git ]]; then
        local owner="${BASH_REMATCH[1]}"
        local repo="${BASH_REMATCH[2]}"
        
        # Check if GITHUB_TOKEN is available
        if [[ -z "${GITHUB_TOKEN:-}" ]]; then
            print_warning "GITHUB_TOKEN not set. Cannot create webhook automatically."
            return 1
        fi
        
        print_status "Creating GitHub webhook for $webhook_type on $github_host..."
        
        # Check if webhook already exists
        local existing_webhooks
        local http_code
        existing_webhooks=$(curl -s -w "\n%{http_code}" -H "Authorization: token $GITHUB_TOKEN" \
            "https://api.$github_host/repos/$owner/$repo/hooks")
        
        http_code=$(echo "$existing_webhooks" | tail -n1)
        existing_webhooks=$(echo "$existing_webhooks" | sed '$d')
        
        if [[ "$http_code" != "200" ]]; then
            print_error "Failed to check existing webhooks (HTTP $http_code)"
            print_error "API Response:"
            echo "$existing_webhooks" | jq '.' 2>/dev/null || echo "$existing_webhooks"
            
            if [[ "$http_code" == "401" ]]; then
                print_error "Authentication failed. Check your GITHUB_TOKEN."
            elif [[ "$http_code" == "404" ]]; then
                print_error "Repository not found. Check GIT_SSH_URL and token permissions."
            fi
            return 1
        fi
        
        if echo "$existing_webhooks" | grep -q "$webhook_url"; then
            print_status "Webhook for $webhook_type already exists"
            return 0
        fi
        
        # Create webhook
        local response
        local json_payload

        json_payload="{\"name\":\"web\",\"active\":true,\"events\":[\"push\"],\"config\":{\"url\":\"$webhook_url\",\"content_type\":\"json\",\"insecure_ssl\":\"0\"}}"

        response=$(curl -s -w "\n%{http_code}" \
            -X POST \
            -H "Authorization: Bearer $GITHUB_TOKEN" \
            -H "Accept: application/vnd.github+json" \
            -H "X-GitHub-Api-Version: 2022-11-28" \
            "https://api.$github_host/repos/$owner/$repo/hooks" \
            -d $json_payload
        )

        http_code=$(echo "$response" | tail -n1)
        response=$(echo "$response" | sed '$d')
        
        if [[ "$http_code" == "201" ]] && echo "$response" | grep -q '"id"'; then
            print_success "GitHub webhook for $webhook_type created successfully!"
            return 0
        else
            print_error "Failed to create GitHub webhook for $webhook_type (HTTP $http_code)"
            print_error "API Response:"
            echo "$response" | jq '.' 2>/dev/null || echo "$response"
            
            # Provide helpful error messages
            if [[ "$http_code" == "422" ]]; then
                if echo "$response" | grep -q "Hook already exists"; then
                    print_warning "Webhook already exists but wasn't detected in the check."
                else
                    print_error "Validation failed. Check webhook URL format."
                fi
            elif [[ "$http_code" == "401" ]]; then
                print_error "Authentication failed. Check your GITHUB_TOKEN permissions."
            elif [[ "$http_code" == "404" ]]; then
                print_error "Repository not found. Check GIT_SSH_URL and token permissions."
            fi
            return 1
        fi
    fi
    
    print_error "Invalid GIT_SSH_URL format. Expected: git@$github_host:owner/repo.git"
    return 1
}

# Function to setup CI/CD webhooks
setup_webhooks() {
    print_status "Setting up webhooks..."
    
    # Create RoleBinding for webhook access if it doesn't exist
    if ! resource_exists "rolebinding" "webhook-access-unauthenticated"; then
        print_status "Creating RoleBinding for webhook access..."
        apply_resource "$(cat << EOF
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  annotations:
    rbac.authorization.kubernetes.io/autoupdate: "true"
  name: webhook-access-unauthenticated
  namespace: $PROJECT_NAME
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: "system:webhook"
subjects:
  - apiGroup: rbac.authorization.k8s.io
    kind: Group
    name: "system:unauthenticated"
EOF
)"
    else
        print_status "RoleBinding webhook-access-unauthenticated already exists, skipping creation"
    fi
    
    # Get webhook URLs
    print_status "Getting webhook URLs..."
    local frontend_base_url
    local frontend_secret
    local frontend_webhook
    local backend_base_url
    local backend_secret
    local backend_webhook
    
    frontend_base_url=$(oc describe bc/frontend | grep "Webhook Generic" -A 1 | tail -n 1 | sed 's/.*\(https:\/\/[^ ]*\).*/\1/')
    frontend_secret=$(oc get bc frontend -o jsonpath='{.spec.triggers[*].generic.secret}')
    frontend_webhook=${frontend_base_url/<secret>/$frontend_secret}
    
    backend_base_url=$(oc describe bc/backend | grep "Webhook Generic" -A 1 | tail -n 1 | sed 's/.*\(https:\/\/[^ ]*\).*/\1/')
    backend_secret=$(oc get bc backend -o jsonpath='{.spec.triggers[*].generic.secret}')
    backend_webhook=${backend_base_url/<secret>/$backend_secret}
    
    # Store webhook URLs
    FRONTEND_WEBHOOK="$frontend_webhook"
    BACKEND_WEBHOOK="$backend_webhook"
    
    # Try to create GitHub webhooks automatically
    if [[ -n "${GITHUB_TOKEN:-}" ]]; then
        print_status "Attempting to create GitHub webhooks automatically..."
        create_github_webhook "$GIT_SSH_URL" "$frontend_webhook" "frontend"
        create_github_webhook "$GIT_SSH_URL" "$backend_webhook" "backend"
    else
        print_warning "GITHUB_TOKEN not set. Webhooks must be added manually to GitHub."
    fi
    
    return 0
}

#############################################
# Main Execution Functions
#############################################

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                SHOW_HELP=true
                shift
                ;;
            --env-file)
                ENV_FILE="$2"
                shift 2
                ;;
            --reset-prod-db)
                RESET_PROD_DB=true
                shift
                ;;
            --regenerate-ssh-key)
                REGENERATE_SSH_KEY=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
}

# Main function
main() {
    # Parse arguments
    parse_arguments "$@"
    
    # Show help if requested
    if [[ "$SHOW_HELP" == "true" ]]; then
        show_help
        exit 0
    fi
    
    echo
    echo -e "${TEAL}Welcome to the OpenShift Deployment Script!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo
    
    # Load environment variables from file
    load_env_file "$ENV_FILE" || exit 1
    
    # Validate all required variables
    validate_required_vars || exit 1
    
    # Check OpenShift client and login
    check_oc_version || exit 1
    check_oc_login || exit 1
    
    # Setup project
    setup_project || exit 1
    
    # Handle SSH key regeneration flag
    if [[ "$REGENERATE_SSH_KEY" == "true" ]]; then
        delete_ssh_keys || exit 1
    fi
    
    # Setup SSH keys
    setup_ssh_keys || exit 1
    
    # Handle database reset flag
    if [[ "$RESET_PROD_DB" == "true" ]]; then
        reset_production_database || exit 1
        print_success "Database reset completed. Exiting."
        exit 0
    fi
    
    # Create the initial app environment secret
    create_initial_app_env_secret || exit 1
    
    # Deploy database
    deploy_database || exit 1
    
    # Deploy frontend and backend
    deploy_frontend || exit 1
    deploy_backend || exit 1
    
    # Update the app environment secret with frontend/backend URLs
    update_app_env_secret_with_urls || exit 1
    
    # Configure frontend and backend
    configure_frontend || exit 1
    configure_backend || exit 1
    
    # Group resources
    group_resources || exit 1
    
    # Setup webhooks
    setup_webhooks || exit 1
    
    # Print success message
    print_success "Deployment completed successfully!"
    echo
    
    if [[ -n "${GITHUB_TOKEN:-}" ]]; then
        print_success "GitHub webhooks have been configured automatically!"
    else
        echo "Frontend Webhook URL:"
        echo "$FRONTEND_WEBHOOK"
        echo
        echo "Backend Webhook URL:"
        echo "$BACKEND_WEBHOOK"
        echo
        print_status "Please add these webhook URLs to your GitHub repository"
    fi
    
    # Get URLs
    local frontend_url
    local backend_url
    frontend_url=$(oc get route frontend -o jsonpath='{.spec.host}')
    backend_url=$(oc get route backend -o jsonpath='{.spec.host}')
    
    echo
    echo "Once builds are completed (this can take a few minutes), you can access the application at:"
    echo "Frontend: https://$frontend_url"
    echo "Backend:  https://$backend_url"
    echo
    
    return 0
}

# Execute main function with all arguments
main "$@"

# Made with Bob
