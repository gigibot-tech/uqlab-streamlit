#!/usr/bin/env bash
#
# Environment Management Library
#
# This library provides:
# - Environment variable loading from .env files
# - Required variable validation
# - Password validation
#

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

# Variables that need password length validation (min 8 chars)
declare -a PASSWORD_VARS=(
    "FIRST_SUPERUSER_PASSWORD"
    "POSTGRES_PASSWORD"
    "SECRET_KEY"
)

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

# Made with Bob
