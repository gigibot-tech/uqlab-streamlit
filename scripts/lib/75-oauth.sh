#!/usr/bin/env bash
#
# OAuth2 Proxy Deployment Library
#
# This library provides:
# - OAuth2 Proxy deployment (optional feature)
# - OAuth configuration validation
# - OAuth secret management
# - OAuth service and route creation
#
#############################################
# OAuth Detection Functions
#############################################

# Function to check if OAuth is enabled
is_oauth_enabled() {
    # Check if any OAuth variable is set
    if [[ -n "${OAUTH2_PROXY_COOKIE_DOMAIN:-}" ]] || \
       [[ -n "${OAUTH2_PROXY_COOKIE_SECRET:-}" ]] || \
       [[ -n "${OAUTH2_PROXY_CLIENT_ID:-}" ]] || \
       [[ -n "${OAUTH2_PROXY_CLIENT_SECRET:-}" ]] || \
       [[ -n "${OAUTH2_PROXY_OIDC_ISSUER_URL:-}" ]] || \
       [[ -n "${OAUTH2_PROXY_REDIRECT_URL:-}" ]]; then
        return 0
    fi
    return 1
}

#############################################
# OAuth Secret Management
#############################################

# Function to create OAuth2 Proxy secret
create_oauth_proxy_secret() {
    local secret_name="$APP_NAME-oauth-proxy-secret"
    
    print_status "Creating OAuth2 Proxy secret..." "oauth"
    
    # Check if secret exists
    if resource_exists "secret" "$secret_name"; then
        print_status "OAuth2 Proxy secret exists, updating..." "oauth"
        oc delete secret "$secret_name"
    fi
    
    # Create secret with OAuth variables
    oc create secret generic "$secret_name" \
        --from-literal=cookiedomain="$OAUTH2_PROXY_COOKIE_DOMAIN" \
        --from-literal=cookiesecret="$OAUTH2_PROXY_COOKIE_SECRET" \
        --from-literal=clientid="$OAUTH2_PROXY_CLIENT_ID" \
        --from-literal=clientsecret="$OAUTH2_PROXY_CLIENT_SECRET" \
        --from-literal=oidc-issuer-url="$OAUTH2_PROXY_OIDC_ISSUER_URL" \
        --from-literal=redirect-url="$OAUTH2_PROXY_REDIRECT_URL"
    
    print_success "OAuth2 Proxy secret created: $secret_name" "oauth"
    return 0
}

#############################################
# OAuth Deployment Functions
#############################################

# Function to deploy OAuth2 Proxy
deploy_oauth_proxy() {
    print_status "Deploying OAuth2 Proxy..." "oauth"
    
    # Check if deployment already exists
    if resource_exists "deployment" "oauth-proxy"; then
        print_status "OAuth2 Proxy deployment already exists, triggering rollout restart..." "oauth"
        oc rollout restart deployment/oauth-proxy
        oc rollout status deployment/oauth-proxy --timeout=300s
        return 0
    fi
    
    print_status "Creating new OAuth2 Proxy deployment..." "oauth"
    
    # Create deployment
    cat << EOF | oc apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: oauth-proxy
  labels:
    app: oauth-proxy
    app.kubernetes.io/part-of: ${APP_NAME}
spec:
  replicas: 1
  selector:
    matchLabels:
      deployment: oauth-proxy
  template:
    metadata:
      labels:
        deployment: oauth-proxy
        app: oauth-proxy
    spec:
      containers:
        - name: oauth-proxy
          image: quay.io/oauth2-proxy/oauth2-proxy:latest
          env:
            - name: OAUTH2_PROXY_COOKIE_DOMAIN
              valueFrom:
                secretKeyRef:
                  name: ${APP_NAME}-oauth-proxy-secret
                  key: cookiedomain
            - name: OAUTH2_PROXY_COOKIE_SECRET
              valueFrom:
                secretKeyRef:
                  name: ${APP_NAME}-oauth-proxy-secret
                  key: cookiesecret
            - name: OAUTH2_PROXY_CLIENT_ID
              valueFrom:
                secretKeyRef:
                  name: ${APP_NAME}-oauth-proxy-secret
                  key: clientid
            - name: OAUTH2_PROXY_CLIENT_SECRET
              valueFrom:
                secretKeyRef:
                  name: ${APP_NAME}-oauth-proxy-secret
                  key: clientsecret
            - name: OAUTH2_PROXY_OIDC_ISSUER_URL
              valueFrom:
                secretKeyRef:
                  name: ${APP_NAME}-oauth-proxy-secret
                  key: oidc-issuer-url
            - name: OAUTH2_PROXY_REDIRECT_URL
              valueFrom:
                secretKeyRef:
                  name: ${APP_NAME}-oauth-proxy-secret
                  key: redirect-url
          ports:
            - containerPort: 4180
              protocol: TCP
          args:
            - "--provider=oidc"
            - "--pass-authorization-header"
            - "--insecure-oidc-allow-unverified-email"
            - "--upstream=http://backend:8000/api/"
            - "--upstream=http://frontend:8080/"
            - "--email-domain=*"
            - "--http-address=:4180"
            - "--skip-provider-button"
          readinessProbe:
            httpGet:
              path: /ping
              port: 4180
            initialDelaySeconds: 2
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /ping
              port: 4180
            initialDelaySeconds: 2
            periodSeconds: 30
EOF
    
    print_success "OAuth2 Proxy deployment created" "oauth"
    return 0
}

# Function to create OAuth2 Proxy service
create_oauth_proxy_service() {
    print_status "Creating OAuth2 Proxy service..." "oauth"
    
    # Check if service already exists
    if resource_exists "service" "oauth-proxy"; then
        print_status "OAuth2 Proxy service already exists, skipping creation" "oauth"
        return 0
    fi
    
    # Create service
    cat << EOF | oc apply -f -
apiVersion: v1
kind: Service
metadata:
  name: oauth-proxy
  labels:
    app: oauth-proxy
    app.kubernetes.io/part-of: ${APP_NAME}
spec:
  ports:
    - name: external
      port: 4180
      protocol: TCP
      targetPort: 4180
  selector:
    deployment: oauth-proxy
EOF
    
    print_success "OAuth2 Proxy service created" "oauth"
    return 0
}

# Function to create OAuth2 Proxy route
create_oauth_proxy_route() {
    print_status "Creating OAuth2 Proxy route..." "oauth"
    
    # Check if route already exists
    if resource_exists "route" "oauth-proxy"; then
        print_status "OAuth2 Proxy route already exists, skipping creation" "oauth"
    else
        oc create route edge oauth-proxy --service=oauth-proxy --port=4180
        print_success "OAuth2 Proxy route created" "oauth"
    fi
    
    # Get the OAuth proxy URL
    local oauth_url
    oauth_url=$(oc get route oauth-proxy -o jsonpath='{.spec.host}' 2>/dev/null || echo "")
    
    if [[ -n "$oauth_url" ]]; then
        # Store in output collector
        add_deployment_output "oauth_proxy_url" "$oauth_url"
        print_success "OAuth2 Proxy URL: https://$oauth_url" "oauth"
    else
        print_warning "Could not retrieve OAuth2 Proxy URL" "oauth"
    fi
    
    return 0
}

# Function to update backend environment with OAuth proxy URL
update_backend_with_oauth_url() {
    local oauth_url
    oauth_url=$(oc get route oauth-proxy -o jsonpath='{.spec.host}' 2>/dev/null || echo "")
    
    if [[ -z "$oauth_url" ]]; then
        print_error "Could not get OAuth proxy URL. Make sure the route is created." "oauth"
        return 1
    fi
    
    print_status "Updating backend environment with OAuth proxy URL..." "oauth"
    
    # Update FRONTEND_URL to point to OAuth proxy
    export FRONTEND_URL="https://$oauth_url"
    
    # Update BACKEND_CORS_ORIGINS to include OAuth proxy
    if [[ -z "${BACKEND_CORS_ORIGINS:-}" ]]; then
        export BACKEND_CORS_ORIGINS="https://$oauth_url"
    else
        # Add OAuth URL to existing BACKEND_CORS_ORIGINS if not already present
        if [[ ! "$BACKEND_CORS_ORIGINS" =~ "https://$oauth_url" ]]; then
            export BACKEND_CORS_ORIGINS="$BACKEND_CORS_ORIGINS,https://$oauth_url"
            print_status "Added OAuth proxy URL to BACKEND_CORS_ORIGINS" "oauth"
        fi
    fi
    
    # Recreate the app environment secret with updated values
    local secret_name="$APP_NAME-env"
    print_status "Updating $secret_name secret with OAuth proxy URL..." "oauth"
    
    # Delete the existing secret
    oc delete secret "$secret_name"
    
    # Recreate the secret with all values including OAuth URL
    local secret_cmd="oc create secret generic $secret_name"
    secret_cmd+=$(build_secret_literals)
    
    # Execute the command
    eval "$secret_cmd"
    
    print_success "Backend environment updated with OAuth proxy URL: https://$oauth_url" "oauth"
    
    # Restart backend to pick up new environment
    if resource_exists "deployment" "backend"; then
        print_status "Restarting backend to apply OAuth configuration..." "oauth"
        oc rollout restart deployment/backend
        oc rollout status deployment/backend --timeout=300s
    fi
    
    return 0
}

# Made with Bob