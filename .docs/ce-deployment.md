# Code Engine Deployment Guide

This guide covers deploying the application to production environments. The application supports two deployment strategies:

1. **IBM Code Engine** - Serverless container platform with 1Password integration
2. **OpenShift** - Enterprise Kubernetes platform with optional OAuth2 Proxy

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Deployment Method 1: IBM Code Engine](#deployment-method-1-ibm-code-engine)
- [Deployment Method 2: OpenShift](#deployment-method-2-openshift)
- [OAuth2 Proxy Configuration](#oauth2-proxy-configuration)
- [Post-Deployment](#post-deployment)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### General Requirements

- Docker installed and running
- Access to your deployment platform (IBM Cloud or OpenShift)
- Git repository with SSH access
- PostgreSQL database (managed or self-hosted)

### Platform-Specific Requirements

#### IBM Code Engine

- IBM Cloud account with appropriate permissions
- IBM Cloud CLI installed
- 1Password CLI installed (for secrets management)
- Container Registry namespace created

#### OpenShift

- OpenShift CLI (`oc`) installed
- Active OpenShift cluster login
- GitHub Personal Access Token (optional but recommended)

---

## Environment Configuration

### Step 1: Create Production Environment File

Copy the example file to create your production configuration:

```bash
cp .env.production.merged.example .env.production
```

### Step 2: Configure Required Variables

Edit `.env.production` and set the following required variables:

#### Common Configuration (Required for All Deployments)

```bash
# Application Identity
PROJECT_NAME=my-app
APP_NAME=my-app

# Admin User
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=your-secure-password

# Backend Security
SECRET_KEY=your-secret-key-min-8-chars

# Database
POSTGRES_SERVER=your-db-host
POSTGRES_PORT=5432
POSTGRES_DB=app
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-db-password
```

**Important:** Replace all `changethis` values with secure, production-ready values.

---

## Deployment Method 1: IBM Code Engine

IBM Code Engine provides a serverless container platform with automatic scaling and 1Password integration for secure secrets management.

### Prerequisites

1. Install IBM Cloud CLI:

   ```bash
   curl -fsSL https://clis.cloud.ibm.com/install/linux | sh
   ```

2. Install required plugins:

   ```bash
   ibmcloud plugin install container-registry
   ibmcloud plugin install code-engine
   ```

3. Install 1Password CLI:
   ```bash
   # See: https://developer.1password.com/docs/cli/get-started/
   ```

### Configuration

#### 1. Set Up 1Password Vault

Create a vault in 1Password for your project and store all secrets with the structure:

```
op://<YOUR_VAULT>/.env.production/VARIABLE_NAME
```

#### 2. Configure IBM Cloud Variables

In `.env.production`, uncomment and configure the Code Engine section:

```bash
# IBM Cloud Authentication
_IBM_API_KEY=op://<YOUR_VAULT>/.env.production/IBM_API_KEY
_IBM_CLOUD_URL=op://<YOUR_VAULT>/.env.production/IBM_CLOUD_URL

# IBM Cloud Configuration
_IBM_CLOUD_RESOURCE_GROUP=Default
_IBM_CLOUD_REGION=eu-de
_IBM_CLOUD_ACCOUNT_NAME=Your Account Name

# Code Engine Project
_CE_PROJECT_NAME=my-project
_CR_NAMESPACE=my-namespace
_CR_REGISTRY=private.de.icr.io
_CR_REGISTRY_SECRET_NAME=my-registry-secret

# Application Names
_CE_FRONTEND_IMAGE_NAME=frontend
_CE_FRONTEND_APPLICATION_NAME=my-app-frontend
_CE_BACKEND_IMAGE_NAME=backend
_CE_BACKEND_ENV_SECRET_NAME=my-app-backend-config
_CE_BACKEND_APPLICATION_NAME=my-app-backend
```

#### 3. Configure Application Secrets with 1Password

Replace direct values with 1Password references:

```bash
PROJECT_NAME=op://<YOUR_VAULT>/.env.production/PROJECT_NAME
SECRET_KEY=op://<YOUR_VAULT>/.env.production/SECRET_KEY
FIRST_SUPERUSER=op://<YOUR_VAULT>/.env.production/FIRST_SUPERUSER
FIRST_SUPERUSER_PASSWORD=op://<YOUR_VAULT>/.env.production/FIRST_SUPERUSER_PASSWORD
POSTGRES_SERVER=op://<YOUR_VAULT>/.env.production/POSTGRES_SERVER
POSTGRES_PASSWORD=op://<YOUR_VAULT>/.env.production/POSTGRES_PASSWORD
VITE_API_URL=op://<YOUR_VAULT>/.env.production/VITE_API_URL
```

### Deployment

#### Standard Deployment (Without OAuth)

```bash
./scripts/ce-deploy.sh
```

#### Deployment with OAuth2 Proxy

```bash
./scripts/ce-deploy-oauth.sh
```

The OAuth deployment script will:

1. Deploy OAuth2 Proxy first to obtain the cluster URL
2. Extract the cluster identifier
3. Update `.env.production` with correct URLs
4. Deploy frontend and backend with proper configuration

### Post-Deployment

After successful deployment, the script will display:

- Application URLs
- Infrastructure details
- Direct access URLs (for debugging)

---

## Deployment Method 2: OpenShift

OpenShift provides an enterprise Kubernetes platform with built-in CI/CD capabilities.

### Prerequisites

1. Install OpenShift CLI:

   ```bash
   # Download from: https://mirror.openshift.com/pub/openshift-v4/clients/ocp/
   ```

2. Login to your OpenShift cluster:
   ```bash
   oc login --server=https://your-cluster-url:6443
   ```

### Configuration

#### 1. Configure Git Repository

In `.env.production`, set your Git repository:

```bash
# Git Repository (SSH format required)
GIT_SSH_URL=git@github.com:username/repository.git

# GitHub Host (default: github.ibm.com)
GITHUB_HOST=github.ibm.com
```

#### 2. Configure GitHub Token (Optional but Recommended)

A GitHub Personal Access Token enables automatic webhook and deploy key management.

**Creating a GitHub Token:**

For IBM GitHub Enterprise:

1. Go to https://github.ibm.com/settings/tokens

For Public GitHub:

1. Go to https://github.com/settings/tokens

Then: 2. Click "Generate new token (classic)" 3. Give it a descriptive name (e.g., "OpenShift Deployment") 4. Select scopes:

- `repo` (Full control of private repositories)
- `admin:repo_hook` (Full control of repository hooks)

5. Generate and copy the token

Add to `.env.production`:

```bash
GITHUB_TOKEN=ghp_your_token_here
```

#### 3. Configure OpenShift Project

```bash
PROJECT_NAME=my-openshift-project
```

#### 4. Optional: Branch Filter

Deploy only from specific branches:

```bash
DEPLOYMENT_BRANCH_FILTER=main
```

### Deployment

#### Full Deployment (Frontend + Backend + Database)

```bash
./scripts/oc-deploy.sh
```

#### Backend-Only Deployment

```bash
./scripts/oc-deploy.sh --backend-only
```

#### Backend-Only Without Database

```bash
./scripts/oc-deploy.sh --backend-only --no-db
```

### Deployment Options

| Option                 | Description                                           |
| ---------------------- | ----------------------------------------------------- |
| `--help`               | Show help message                                     |
| `--env-file <path>`    | Use custom environment file                           |
| `--backend-only`       | Deploy only backend (skip frontend)                   |
| `--no-db`              | Skip database deployment (requires --backend-only)    |
| `--reset-prod-db`      | Reset production database (DESTRUCTIVE)               |
| `--regenerate-ssh-key` | Regenerate SSH deploy keys                            |
| `--show-env-values`    | Display environment variable values during deployment |

### Database Management

#### Reset Production Database

**WARNING:** This will delete all data!

```bash
./scripts/oc-deploy.sh --reset-prod-db
```

This will:

1. Delete the existing database pod
2. Delete the persistent volume claim
3. Redeploy a fresh database
4. Run migrations

### SSH Key Management

The deployment script automatically manages SSH keys for Git access:

- Creates SSH key pair if not exists
- Adds public key to OpenShift secret
- Automatically adds deploy key to GitHub (if token provided)
- Verifies deploy key access

To regenerate SSH keys:

```bash
./scripts/oc-deploy.sh --regenerate-ssh-key
```

---

## OAuth2 Proxy Configuration

OAuth2 Proxy provides authentication for your application using OIDC providers (e.g., IBM App ID, Keycloak, Auth0).

### Prerequisites

- OIDC provider configured (e.g., IBM App ID)
- Client ID and Client Secret from your OIDC provider
- OIDC Issuer URL

### Configuration

In `.env.production`, configure OAuth2 Proxy variables:

```bash
# OAuth2 Proxy Cookie Secret (32 characters recommended)
# Generate with: openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
OAUTH2_PROXY_COOKIE_SECRET=your-32-char-secret

# OIDC Provider Configuration
OAUTH2_PROXY_CLIENT_ID=your-client-id
OAUTH2_PROXY_CLIENT_SECRET=your-client-secret
OAUTH2_PROXY_OIDC_ISSUER_URL=https://your-oidc-provider.com

# Optional: Well-Known URL (auto-discovered if not provided)
OAUTH2_PROXY_WELL_KNOWN_URL=https://your-oidc-provider.com/.well-known/openid-configuration
```

### Deployment

#### Code Engine with OAuth

```bash
./scripts/ce-deploy-oauth.sh
```

#### OpenShift with OAuth

OAuth is automatically deployed if OAuth variables are configured:

```bash
./scripts/oc-deploy.sh
```

### OAuth Behavior

- **All variables set:** OAuth2 Proxy is deployed and protects the application
- **Any variable missing:** OAuth2 Proxy is skipped, application is publicly accessible

---

## Post-Deployment

### Verify Deployment

#### Code Engine

Check application status:

```bash
ibmcloud ce application list
```

View logs:

```bash
ibmcloud ce application logs --name my-app-backend
```

#### OpenShift

Check pods:

```bash
oc get pods
```

View logs:

```bash
oc logs deployment/backend
```

### Access Your Application

The deployment script will display the application URL at the end. Access it in your browser.

### Initial Login

Use the admin credentials configured in `.env.production`:

- Email: Value of `FIRST_SUPERUSER`
- Password: Value of `FIRST_SUPERUSER_PASSWORD`

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

**Symptoms:** Backend fails to start, logs show database connection errors

**Solutions:**

- Verify `POSTGRES_SERVER`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD` are correct
- Ensure database is accessible from the deployment platform
- Check database is running: `oc get pods` (OpenShift) or check Code Engine logs

#### 2. Frontend Cannot Reach Backend

**Symptoms:** Frontend loads but API calls fail

**Solutions:**

- Verify `VITE_API_URL` is set correctly
- Check `BACKEND_CORS_ORIGINS` includes the frontend URL
- For OpenShift: Ensure routes are created (`oc get routes`)
- For Code Engine: Check application URLs match configuration

#### 3. OAuth2 Proxy Redirect Loop

**Symptoms:** Continuous redirects when accessing the application

**Solutions:**

- Verify `OAUTH2_PROXY_REDIRECT_URL` matches the configured callback URL in your OIDC provider
- Check `OAUTH2_PROXY_COOKIE_SECRET` is at least 16 characters
- Ensure `OAUTH2_PROXY_OIDC_ISSUER_URL` is correct

#### 4. Build Failures

**Symptoms:** Docker build fails during deployment

**Solutions:**

- Ensure Docker is running
- Check available disk space
- Verify Dockerfile syntax
- For Code Engine: Check IBM Cloud CLI is logged in

#### 5. SSH Key Issues (OpenShift)

**Symptoms:** Build fails with Git authentication errors

**Solutions:**

- Verify `GIT_SSH_URL` is in SSH format (git@github.com:user/repo.git)
- Check GitHub token has correct permissions
- Regenerate SSH keys: `./scripts/oc-deploy.sh --regenerate-ssh-key`
- Manually verify deploy key in GitHub repository settings

### Getting Help

1. Check deployment logs for specific error messages
2. Verify all required environment variables are set
3. Ensure prerequisites are installed and configured
4. Review the deployment script output for warnings

### Debug Mode

Enable verbose output:

```bash
# OpenShift
./scripts/oc-deploy.sh --show-env-values

# Code Engine
# Check logs after deployment
ibmcloud ce application logs --name my-app-backend --follow
```

---

## Security Best Practices

1. **Never commit `.env.production`** - It contains sensitive credentials
2. **Use strong passwords** - Minimum 16 characters for production
3. **Rotate secrets regularly** - Update `SECRET_KEY`, database passwords periodically
4. **Use OAuth2 Proxy** - Protect production deployments with authentication
5. **Limit database access** - Use firewall rules to restrict database connections
6. **Monitor logs** - Regularly review application and security logs
7. **Keep dependencies updated** - Regularly update base images and dependencies

---

## Additional Resources

- [IBM Code Engine Documentation](https://cloud.ibm.com/docs/codeengine)
- [OpenShift Documentation](https://docs.openshift.com/)
- [OAuth2 Proxy Documentation](https://oauth2-proxy.github.io/oauth2-proxy/)
- [1Password CLI Documentation](https://developer.1password.com/docs/cli/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
