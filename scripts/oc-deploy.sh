#!/bin/bash
#
# OpenShift Deployment Script (Optimized)
#
# This script deploys an application to OpenShift with the following features:
# - Idempotent operations (can be run multiple times without side effects)
# - Variables loaded from production.env file
# - Interactive prompts only for variables not found in the env file
# - Best practices for bash scripting
# - Sensitive values are masked in output
# - Single environment secret for all components
#
# Usage: ./oc-deploy-optimized.sh [--env-file path/to/env/file]
#

set -euo pipefail

# Default environment file location
ENV_FILE="$(dirname "$0")/production.env"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --env-file)
      ENV_FILE="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--env-file path/to/env/file]"
      exit 1
      ;;
  esac
done

# Color codes for pretty output
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly RED='\033[0;31m'
readonly TEAL='\033[0;36m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

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

# Function to validate project name
validate_name() {
    local name=$1
    if [[ ! $name =~ ^[a-z0-9-]+$ ]]; then
        return 1
    fi
    return 0
}

# Function to validate email
validate_email() {
    local email=$1
    if [[ ! $email =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; then
        return 1
    fi
    return 0
}

# Function to validate git SSH URL
validate_git_url() {
    local url=$1
    # Check if URL starts with git@ or ssh:// and ends with .git
    if [[ ! $url =~ ^(git@|ssh://).+\.git$ ]]; then
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

# Function to load environment variables from file
load_env_file() {
    local env_file=$1
    
    if [[ ! -f "$env_file" ]]; then
        print_warning "Environment file $env_file not found. Will prompt for all values."
        return 1
    fi
    
    print_status "Loading environment variables from $env_file"
    
    # Load variables from env file without executing any code
    # This is safer than using source
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
            print_status "Loaded $var_name from environment file"
        fi
    done < "$env_file"
    
    return 0
}

# Function to prompt for a variable if not already set
prompt_var() {
    local var_name=$1
    local prompt_text=$2
    local validation_func=${3:-""}
    local default_value=${4:-""}
    local is_optional=${5:-false}
    local is_sensitive=false
    
    # Check if variable is already set
    if [[ -n "${!var_name:-}" ]]; then
        # Check if variable is sensitive
        if is_sensitive_var "$var_name"; then
            print_status "$var_name is already set [value masked]"
        else
            print_status "$var_name is already set to '${!var_name}'"
        fi
        return 0
    fi
    
    # Add default value to prompt if provided
    local prompt_with_default="$prompt_text"
    if [[ -n "${default_value:-}" ]]; then
        prompt_with_default="$prompt_text (default: $default_value)"
    fi
    
    # Check if variable is sensitive
    if is_sensitive_var "$var_name"; then
        is_sensitive=true
    fi
    
    while true; do
        # Use -s flag for read command if variable is sensitive
        if [[ "$is_sensitive" == "true" ]]; then
            read -s -p "$prompt_with_default: " input_value
            echo # Add a newline after the hidden input
        else
            read -p "$prompt_with_default: " input_value
        fi
        
        # Use default if input is empty
        if [[ -z "$input_value" && -n "${default_value:-}" ]]; then
            input_value="$default_value"
        fi
        
        # Skip validation if the field is optional and input is empty
        if [[ "$is_optional" == "true" && -z "$input_value" ]]; then
            export "$var_name"=""
            return 0
        fi
        
        # Skip validation if no validation function is provided
        if [[ -z "$validation_func" ]]; then
            export "$var_name"="$input_value"
            return 0
        fi
        
        # Validate input
        if "$validation_func" "$input_value"; then
            export "$var_name"="$input_value"
            return 0
        else
            print_error "Invalid input. Please try again."
        fi
    done
}

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

# Function to handle project creation or selection
setup_project() {
    # Project name with validation
    prompt_var "PROJECT_NAME" "Choose an OpenShift project name (lowercase letters, numbers and hyphens only)" validate_name
    
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
        print_status "Creating new project..."
        oc new-project "$PROJECT_NAME" || {
            print_error "Failed to create project"
            return 1
        }
    fi
    
    return 0
}

# Function to create SSH keys for Git access
setup_ssh_keys() {
    mkdir -p "$HOME/.ssh/$PROJECT_NAME"
    local key_path="$HOME/.ssh/$PROJECT_NAME/ocp-key"
    local pub_key_path="$HOME/.ssh/$PROJECT_NAME/ocp-key.pub"
    local need_user_input=false
    
    # Check if both private and public keys already exist and if the env OC_DEPLOY_KEY is set
    if [[ -f "$key_path" && -f "$pub_key_path" && -n "${OC_DEPLOY_KEY:-}" ]]; then
        print_status "SSH key pair already exists in ~/.ssh/$PROJECT_NAME/"
        
    else
            # Generate new keys
            print_status "Generating new SSH key pair"
            ssh-keygen -N '' -f "$key_path" -C "openshift-deploy-key" -q <<< y > /dev/null
            print_success "SSH key pair generated"
            need_user_input=true
    fi
    
    # Display the public key
    print_status "Public SSH key for repository access:"
    echo -e "${TEAL}$(cat "$pub_key_path")${NC}"
    
    # Only prompt for user input if we generated a new key and didn't use OC_DEPLOY_KEY
    if [[ "$need_user_input" == "true" ]]; then
        print_status "${GREEN}Please add this public key to your GitLab/GitHub repository as a deploy key${NC}"
        read -p "Press enter once you've added the deploy key..."
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

# Function to create initial application environment secret without frontend/backend URLs
create_initial_app_env_secret() {
    local secret_name="$APP_NAME-env"
    
    # Generate a secure random secret key if not provided
    if [[ -z "${SECRET_KEY:-}" ]]; then
        SECRET_KEY=$(openssl rand -hex 32)
        print_success "Generated secure secret key for backend"
    fi
    
    # Create or update application environment secret
    if resource_exists "secret" "$secret_name"; then
        print_status "Updating $secret_name secret..."
        oc delete secret "$secret_name"
    fi
    
    print_status "Creating initial application environment secret $secret_name (without frontend/backend URLs)..."
    oc create secret generic "$secret_name" \
        --from-literal=ENVIRONMENT=production \
        --from-literal=PROJECT_NAME="$PROJECT_NAME" \
        --from-literal=SECRET_KEY="$SECRET_KEY" \
        --from-literal=FIRST_SUPERUSER="$FIRST_SUPERUSER" \
        --from-literal=FIRST_SUPERUSER_PASSWORD="$FIRST_SUPERUSER_PASSWORD" \
        --from-literal=SIGNUP_ACCESS_PASSWORD="$SIGNUP_ACCESS_PASSWORD" \
        --from-literal=POSTGRES_SERVER=postgresql \
        --from-literal=POSTGRES_PORT=5432 \
        --from-literal=POSTGRES_DB=app \
        --from-literal=POSTGRES_USER="$POSTGRES_USER" \
        --from-literal=POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
        --from-literal=API_KEY="$API_KEY" \
        --from-literal=TWILIO_ACCOUNT_SID="$TWILIO_ACCOUNT_SID" \
        --from-literal=TWILIO_AUTH_TOKEN="$TWILIO_AUTH_TOKEN" \
        --from-literal=TWILIO_PHONE_NUMBER="$TWILIO_PHONE_NUMBER" \
        --from-literal=ASSISTANT_NUMBER_GERMAN="$ASSISTANT_NUMBER_GERMAN" \
        --from-literal=ASSISTANT_NUMBER_ENGLISH="${ASSISTANT_NUMBER_ENGLISH:-}" \
        --from-literal=SIP_TRUNK="$SIP_TRUNK" \
        --from-literal=WATSONX_URL="$WATSONX_URL" \
        --from-literal=WATSONX_API_KEY="$WATSONX_API_KEY" \
        --from-literal=WATSONX_PROJECT_ID="$WATSONX_PROJECT_ID" \
        --from-literal=DEFAULT_MODEL_ID="$DEFAULT_MODEL_ID" \
        --from-literal=CHAT_CONTACT_SALUTATION="${CHAT_CONTACT_SALUTATION:-}" \
        --from-literal=CHAT_CONTACT_NAME="${CHAT_CONTACT_NAME:-}" \
        --from-literal=CHAT_CONTACT_FAMILY_NAME="${CHAT_CONTACT_FAMILY_NAME:-}" \
        --from-literal=CHAT_CONTACT_PHONE_NUMBER="${CHAT_CONTACT_PHONE_NUMBER:-}" \
        --from-literal=CHAT_CONTACT_EMAIL="${CHAT_CONTACT_EMAIL:-}" \
        --from-literal=CHAT_CONTACT_RESEARCHER_SALUTATION="${CHAT_CONTACT_RESEARCHER_SALUTATION:-}" \
        --from-literal=CHAT_CONTACT_RESEARCHER_NAME="${CHAT_CONTACT_RESEARCHER_NAME:-}"
    
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
    
    # Delete the existing secret
    oc delete secret "$secret_name"
    
    # Recreate the secret with all values including URLs
    print_status "Recreating application environment secret with URLs..."
    oc create secret generic "$secret_name" \
        --from-literal=ENVIRONMENT=production \
        --from-literal=PROJECT_NAME="$PROJECT_NAME" \
        --from-literal=BACKEND_CORS_ORIGINS="https://$frontend_url" \
        --from-literal=SECRET_KEY="$SECRET_KEY" \
        --from-literal=FIRST_SUPERUSER="$FIRST_SUPERUSER" \
        --from-literal=FIRST_SUPERUSER_PASSWORD="$FIRST_SUPERUSER_PASSWORD" \
        --from-literal=SIGNUP_ACCESS_PASSWORD="$SIGNUP_ACCESS_PASSWORD" \
        --from-literal=POSTGRES_SERVER=postgresql \
        --from-literal=POSTGRES_PORT=5432 \
        --from-literal=POSTGRES_DB=app \
        --from-literal=POSTGRES_USER="$POSTGRES_USER" \
        --from-literal=POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
        --from-literal=API_KEY="$API_KEY" \
        --from-literal=TWILIO_ACCOUNT_SID="$TWILIO_ACCOUNT_SID" \
        --from-literal=TWILIO_AUTH_TOKEN="$TWILIO_AUTH_TOKEN" \
        --from-literal=TWILIO_PHONE_NUMBER="$TWILIO_PHONE_NUMBER" \
        --from-literal=ASSISTANT_NUMBER_GERMAN="$ASSISTANT_NUMBER_GERMAN" \
        --from-literal=ASSISTANT_NUMBER_ENGLISH="${ASSISTANT_NUMBER_ENGLISH:-}" \
        --from-literal=SIP_TRUNK="$SIP_TRUNK" \
        --from-literal=WATSONX_URL="$WATSONX_URL" \
        --from-literal=WATSONX_API_KEY="$WATSONX_API_KEY" \
        --from-literal=WATSONX_PROJECT_ID="$WATSONX_PROJECT_ID" \
        --from-literal=DEFAULT_MODEL_ID="$DEFAULT_MODEL_ID" \
        --from-literal=DOMAIN="$backend_url" \
        --from-literal=CHAT_CONTACT_SALUTATION="${CHAT_CONTACT_SALUTATION:-}" \
        --from-literal=CHAT_CONTACT_NAME="${CHAT_CONTACT_NAME:-}" \
        --from-literal=CHAT_CONTACT_FAMILY_NAME="${CHAT_CONTACT_FAMILY_NAME:-}" \
        --from-literal=CHAT_CONTACT_PHONE_NUMBER="${CHAT_CONTACT_PHONE_NUMBER:-}" \
        --from-literal=CHAT_CONTACT_EMAIL="${CHAT_CONTACT_EMAIL:-}" \
        --from-literal=CHAT_CONTACT_RESEARCHER_SALUTATION="${CHAT_CONTACT_RESEARCHER_SALUTATION:-}" \
        --from-literal=CHAT_CONTACT_RESEARCHER_NAME="${CHAT_CONTACT_RESEARCHER_NAME:-}"
    
    print_success "Updated environment secret with frontend URL: https://$frontend_url and backend URL: https://$backend_url"
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

# Function to deploy frontend
deploy_frontend() {
    print_status "Deploying frontend..."
    
    # Check if frontend app already exists
    if resource_exists "buildconfig" "frontend"; then
        print_status "Frontend buildconfig already exists, updating..."
        oc start-build frontend --from-dir=. --follow
    else
        oc new-app --name=frontend --strategy=docker --context-dir=frontend --source-secret=git-secret "$GIT_URL"
    fi
    
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
        print_status "Backend buildconfig already exists, updating..."
        oc start-build backend --from-dir=. --follow
    else
        oc new-app --name=backend --strategy=docker --context-dir=backend --source-secret=git-secret "$GIT_URL"
    fi
    
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
    
    # Configure frontend build with VITE_API_URL and Assistant variables
    print_status "Configuring frontend build with VITE_API_URL=https://$backend_url and Assistant variables..."
    oc patch bc/frontend --type=merge -p "{\"spec\":{\"strategy\":{\"dockerStrategy\":{\"env\":[{\"name\":\"VITE_API_URL\",\"value\":\"https://$backend_url\"},{\"name\":\"VITE_ASSISTANT_INTEGRATION_ID\",\"value\":\"$VITE_ASSISTANT_INTEGRATION_ID\"},{\"name\":\"VITE_ASSISTANT_SERVICE_INSTANCE_ID\",\"value\":\"$VITE_ASSISTANT_SERVICE_INSTANCE_ID\"},{\"name\":\"VITE_ASSISTANT_REGION\",\"value\":\"$VITE_ASSISTANT_REGION\"}]}}}}"
    
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
    
    frontend_base_url=$(oc describe bc/frontend | grep "Webhook Generic" -A 1 | tail -n 1 | tr -d ' ')
    frontend_secret=$(oc get bc frontend -o jsonpath='{.spec.triggers[*].generic.secret}')
    frontend_webhook=${frontend_base_url/<secret>/$frontend_secret}
    
    backend_base_url=$(oc describe bc/backend | grep "Webhook Generic" -A 1 | tail -n 1 | tr -d ' ')
    backend_secret=$(oc get bc backend -o jsonpath='{.spec.triggers[*].generic.secret}')
    backend_webhook=${backend_base_url/<secret>/$backend_secret}
    
    # Store webhook URLs
    FRONTEND_WEBHOOK="$frontend_webhook"
    BACKEND_WEBHOOK="$backend_webhook"
    
    return 0
}

# Main function
main() {
    echo
    echo -e "${TEAL}Welcome to the OpenShift Deployment Script!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo
    
    # Load environment variables from file
    load_env_file "$ENV_FILE"
    
    # Check OpenShift client and login
    check_oc_version || exit 1
    check_oc_login || exit 1
    
    # Collect required inputs that are not in the env file
    echo
    echo -e "${TEAL}Please provide any missing information:${NC}"
    echo -e "${GREEN}----------------------------------------${NC}"
    echo
    
    # App name
    prompt_var "APP_NAME" "Choose an application name (lowercase letters, numbers and hyphens only)" validate_name
    
    # Git URL
    prompt_var "GIT_URL" "Your Git Repository URL (ssh format, e.g. git@github.com:user/repo.git)" validate_git_url
    
    # Postgres configuration
    prompt_var "POSTGRES_USER" "Choose a Postgres username"
    prompt_var "POSTGRES_PASSWORD" "Choose a Postgres password"
    
    # Superuser configuration
    prompt_var "FIRST_SUPERUSER" "Choose a First superuser email" validate_email
    prompt_var "FIRST_SUPERUSER_PASSWORD" "Choose a First superuser password (minimum 8 characters)"
    prompt_var "SIGNUP_ACCESS_PASSWORD" "Choose a Signup access password (leave empty if users should not be able to signup themselves)" "" "" true
    
    # API Key
    prompt_var "API_KEY" "Enter API key for backend security"
    
    # Twilio configuration
    prompt_var "TWILIO_ACCOUNT_SID" "Enter your Twilio Account SID"
    prompt_var "TWILIO_AUTH_TOKEN" "Enter your Twilio Auth Token"
    prompt_var "TWILIO_PHONE_NUMBER" "Enter your Twilio Phone Number (e.g. +1234567890)"
    
    # Watson Assistant configuration
    prompt_var "ASSISTANT_NUMBER_GERMAN" "Enter Assistant Number for German"
    prompt_var "ASSISTANT_NUMBER_ENGLISH" "Enter Assistant Number for English (optional)" "" "" true
    prompt_var "SIP_TRUNK" "Enter SIP Trunk" "public.voip.eu-de.assistant.watson.cloud.ibm.com"
    
    # Watson Assistant Frontend Integration configuration
    prompt_var "VITE_ASSISTANT_INTEGRATION_ID" "Enter Assistant Integration ID (for frontend web chat)"
    prompt_var "VITE_ASSISTANT_SERVICE_INSTANCE_ID" "Enter Assistant Service Instance ID (for frontend web chat)"
    prompt_var "VITE_ASSISTANT_REGION" "Enter Assistant Region" "eu-de"
    
    
    # WatsonX.AI configuration
    prompt_var "WATSONX_URL" "Enter WatsonX URL" "https://eu-de.ml.cloud.ibm.com"
    prompt_var "WATSONX_API_KEY" "Enter WatsonX API Key"
    prompt_var "WATSONX_PROJECT_ID" "Enter WatsonX Project ID"
    prompt_var "DEFAULT_MODEL_ID" "Enter Default Model ID" "meta-llama/llama-4-maverick-17b-128e-instruct-fp8"
    
    # Chat Contact configuration
    prompt_var "CHAT_CONTACT_SALUTATION" "Enter Chat Contact Salutation (e.g. HERR, FRAU)" "HERR"
    prompt_var "CHAT_CONTACT_NAME" "Enter Chat Contact First Name" "Max"
    prompt_var "CHAT_CONTACT_FAMILY_NAME" "Enter Chat Contact Family Name" "Mustermann"
    prompt_var "CHAT_CONTACT_PHONE_NUMBER" "Enter Chat Contact Phone Number" "+491234567890"
    prompt_var "CHAT_CONTACT_EMAIL" "Enter Chat Contact Email" "max.mustermann@example.com" validate_email
    prompt_var "CHAT_CONTACT_RESEARCHER_SALUTATION" "Enter Chat Contact Researcher Salutation (e.g. HERR, FRAU)" "FRAU"
    prompt_var "CHAT_CONTACT_RESEARCHER_NAME" "Enter Chat Contact Researcher Name" "Martha Sample"
    
    # Setup project
    setup_project || exit 1
    
    # Setup SSH keys
    setup_ssh_keys || exit 1

    # Create the initial app environment secret without frontend/backend URLs
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
    echo "Frontend Webhook URL:"
    echo "$FRONTEND_WEBHOOK"
    echo
    echo "Backend Webhook URL:"
    echo "$BACKEND_WEBHOOK"
    echo
    
    # Get URLs
    local frontend_url
    local backend_url
    frontend_url=$(oc get route frontend -o jsonpath='{.spec.host}')
    backend_url=$(oc get route backend -o jsonpath='{.spec.host}')
    
    echo "Once Builds are completed (this can take a few minutes), you can access the application at:"
    echo "https://$frontend_url"
    echo "https://$backend_url"
    echo
    print_status "Please add these webhook URLs to your GitLab/GitHub repository"
    print_status "Put the backend url in your openapi-for-assistant.json file"
    echo
    
    return 0
}

# Execute main function
main

# Made with Bob
