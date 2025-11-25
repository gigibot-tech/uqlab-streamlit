# OpenShift Deployment Script Documentation

## Overview

The `oc-deploy.sh` script automates the deployment of a full-stack application (Frontend, Backend, PostgreSQL) to OpenShift. It provides a robust, idempotent deployment process with comprehensive validation, dynamic configuration, and advanced features like automatic webhook creation and database management.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [Command-Line Options](#command-line-options)
- [Environment Variables](#environment-variables)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Features

### Core Features
- ✅ **Idempotent Operations**: Safe to run multiple times without side effects
- ✅ **Dynamic Configuration**: All settings loaded from `.env.production` file
- ✅ **Comprehensive Validation**: Validates all required variables with specific rules
- ✅ **Automatic Secret Management**: Dynamically creates OpenShift secrets from env file
- ✅ **VITE_ Variable Injection**: Automatically injects all VITE_ prefixed variables to frontend
- ✅ **SSH Key Management**: Intelligent SSH key handling with GitHub integration
- ✅ **Database Management**: Built-in database reset functionality
- ✅ **Webhook Automation**: Automatic GitHub webhook creation (when token provided)
- ✅ **Colored Output**: Clear, color-coded status messages
- ✅ **Error Handling**: Robust error handling with meaningful messages

### Security Features
- 🔒 Sensitive values masked in output
- 🔒 Secure secret key generation
- 🔒 Password length validation (minimum 8 characters)
- 🔒 API key validation (16, 32, or 64 characters)
- 🔒 SSH key-based Git authentication

## Prerequisites

### Required Tools
- **OpenShift CLI (oc)**: Version 4.14 or higher
  ```bash
  oc version
  ```
- **curl**: For GitHub API interactions
- **jq**: For JSON parsing (optional, for GitHub webhook management)
- **ssh-keygen**: For SSH key generation

### Required Access
- OpenShift cluster access with login credentials
- GitHub repository with admin access (for deploy keys and webhooks)
- GitHub Personal Access Token (optional, for automatic webhook creation)

### Required Files
- `.env.production` file with all required environment variables
- Git repository accessible via SSH

## Quick Start

### 1. Create Environment File

Copy the example file and fill in your values:

```bash
cp scripts/.env.production.example scripts/.env.production
```

Edit `scripts/.env.production` with your configuration:

```bash
# Required Variables
APP_NAME=my-app
PROJECT_NAME=my-project
GIT_SSH_URL=git@github.com:username/repository.git
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=securepassword123
API_KEY=your-32-character-api-key-here
ENVIRONMENT=production

# Database Configuration
POSTGRES_SERVER=postgresql
POSTGRES_PORT=5432
POSTGRES_DB=app
POSTGRES_USER=postgres
POSTGRES_PASSWORD=securedbpassword

# Optional: GitHub Token for webhook automation
GITHUB_TOKEN=ghp_your_github_token_here

# Optional: Frontend environment variables
VITE_API_URL=auto-generated
VITE_CUSTOM_VAR=your-value
```

### 2. Login to OpenShift

```bash
oc login --token=<your-token> --server=<server-url>
```

### 3. Run Deployment

```bash
cd scripts
./oc-deploy.sh
```

## Configuration

### Environment File Structure

The script loads all variables from `.env.production`. The file format is:

```bash
# Comments are supported
VARIABLE_NAME=value
ANOTHER_VAR="value with spaces"
```

### Variable Types

#### 1. Required Main Variables

These variables MUST be present in your `.env.production` file:

| Variable | Description | Validation |
|----------|-------------|------------|
| `APP_NAME` | Application name | Lowercase, alphanumeric, hyphens only |
| `PROJECT_NAME` | OpenShift project name | Lowercase, alphanumeric, hyphens only |
| `GIT_SSH_URL` | Git repository SSH URL | Must start with `git@` or `ssh://` and end with `.git` |
| `FIRST_SUPERUSER` | Admin email address | Valid email format |
| `FIRST_SUPERUSER_PASSWORD` | Admin password | Minimum 8 characters |
| `SIGNUP_ACCESS_PASSWORD` | Signup password | Minimum 8 characters (can be empty) |
| `API_KEY` | Backend API key | 16, 32, or 64 characters |
| `ENVIRONMENT` | Environment name | Any string (e.g., production) |
| `SECRET_KEY` | Backend secret key | Minimum 8 characters (auto-generated if missing) |
| `POSTGRES_SERVER` | PostgreSQL hostname | Any string |
| `POSTGRES_PORT` | PostgreSQL port | Any string |
| `POSTGRES_DB` | Database name | Any string |
| `POSTGRES_USER` | Database user | Any string |
| `POSTGRES_PASSWORD` | Database password | Minimum 8 characters |

#### 2. Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | None (webhooks created manually) |
| `BACKEND_CORS_ORIGINS` | CORS origins | Auto-generated from frontend URL |
| `VITE_*` | Frontend environment variables | Automatically injected |

#### 3. Dynamic Variables

These are automatically set by the script:

- `DOMAIN`: Backend URL (set after route creation)
- `BACKEND_CORS_ORIGINS`: Frontend URL (if not provided)

### Validation Rules

#### Name Validation (APP_NAME, PROJECT_NAME)
- Must contain only lowercase letters, numbers, and hyphens
- No spaces or special characters
- Examples:
  - ✅ `my-app`
  - ✅ `app123`
  - ❌ `My-App` (uppercase)
  - ❌ `my_app` (underscore)

#### Email Validation (FIRST_SUPERUSER)
- Must be a valid email format
- Examples:
  - ✅ `admin@example.com`
  - ✅ `user.name+tag@domain.co.uk`
  - ❌ `invalid-email`
  - ❌ `@example.com`

#### Git URL Validation (GIT_SSH_URL)
- Must start with `git@` or `ssh://`
- Must end with `.git`
- Examples:
  - ✅ `git@github.com:user/repo.git`
  - ✅ `ssh://git@gitlab.com/user/repo.git`
  - ❌ `https://github.com/user/repo.git`
  - ❌ `git@github.com:user/repo`

#### API Key Validation (API_KEY)
- Minimum length: 16 characters
- Length must be a power of 2: 16, 32, 64, 128, or 256
- Examples:
  - ✅ `1234567890123456` (16 chars)
  - ✅ `12345678901234567890123456789012` (32 chars)
  - ❌ `123456789012345` (15 chars - too short)
  - ❌ `12345678901234567890` (20 chars - not power of 2)

#### Password Validation
- All variables containing "PASSWORD" in the name
- Minimum length: 8 characters
- Applies to:
  - `FIRST_SUPERUSER_PASSWORD`
  - `POSTGRES_PASSWORD`
  - `SECRET_KEY`
  - Any other `*PASSWORD*` variables

## Usage

### Basic Deployment

```bash
./oc-deploy.sh
```

This will:
1. Load variables from `.env.production`
2. Validate all required variables
3. Check OpenShift login status
4. Create/select OpenShift project
5. Setup SSH keys for Git access
6. Deploy PostgreSQL database
7. Deploy frontend and backend applications
8. Configure environment variables
9. Setup webhooks (automatically if `GITHUB_TOKEN` is set)

### Custom Environment File

```bash
./oc-deploy.sh --env-file /path/to/custom.env
```

### Show Help

```bash
./oc-deploy.sh --help
```

### Reset Production Database

⚠️ **WARNING**: This will delete all data in the database!

```bash
./oc-deploy.sh --reset-prod-db
```

This will:
1. Prompt for confirmation
2. Delete PostgreSQL deployment, service, and PVC
3. Recreate the database from scratch
4. Restart backend to apply migrations

### Regenerate SSH Keys

```bash
./oc-deploy.sh --regenerate-ssh-key
```

This will:
1. Delete local SSH keys
2. Delete deploy key from GitHub (if `GITHUB_TOKEN` is set)
3. Delete git-secret from OpenShift
4. Generate new SSH keys
5. Add new deploy key to GitHub (if `GITHUB_TOKEN` is set)

### Combine Options

```bash
./oc-deploy.sh --env-file production.env --reset-prod-db
```

## Command-Line Options

| Option | Description |
|--------|-------------|
| `-h, --help` | Show help message and exit |
| `--env-file PATH` | Specify custom environment file (default: `scripts/.env.production`) |
| `--reset-prod-db` | Reset production database (deletes and recreates storage) |
| `--regenerate-ssh-key` | Delete and regenerate SSH keys for GitHub access |

## Environment Variables

### Core Application Variables

```bash
# Application Identity
APP_NAME=my-app                    # Used for resource naming
PROJECT_NAME=my-openshift-project  # OpenShift project/namespace name
ENVIRONMENT=production             # Environment identifier

# Git Configuration
GIT_SSH_URL=git@github.com:user/repo.git  # SSH URL for repository
```

### Authentication & Security

```bash
# Admin User
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=secure_password_min_8_chars

# API Security
API_KEY=your_32_character_api_key_here  # 16, 32, or 64 chars
SECRET_KEY=your_secret_key_min_8_chars  # Auto-generated if missing

# User Signup (optional)
SIGNUP_ACCESS_PASSWORD=signup_password  # Can be empty to disable signup
```

### Database Configuration

```bash
POSTGRES_SERVER=postgresql  # Service name in OpenShift
POSTGRES_PORT=5432
POSTGRES_DB=app
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secure_db_password_min_8_chars
```

### Frontend Variables (VITE_)

All variables prefixed with `VITE_` are automatically injected into the frontend build:

```bash
# Automatically set by script
VITE_API_URL=https://backend-route-url

# Custom frontend variables
VITE_CUSTOM_FEATURE=enabled
VITE_ANALYTICS_ID=UA-123456-1
VITE_APP_VERSION=1.0.0
```

### GitHub Integration (Optional)

```bash
# For automatic webhook creation and deploy key management
GITHUB_TOKEN=ghp_your_personal_access_token_here
```

**Required GitHub Token Permissions:**
- `repo` - Full control of private repositories
- `admin:repo_hook` - Full control of repository hooks

### Backend CORS (Optional)

```bash
# Auto-generated from frontend URL if not provided
BACKEND_CORS_ORIGINS=https://frontend-url,https://another-domain
```

## Advanced Features

### 1. Dynamic Secret Creation

The script automatically creates OpenShift secrets with ALL variables from your `.env.production` file:

```bash
# All these variables are automatically added to the secret
CUSTOM_VAR_1=value1
CUSTOM_VAR_2=value2
ANY_OTHER_VAR=value3
```

No need to manually update the script when adding new environment variables!

### 2. Automatic VITE_ Variable Injection

Any variable starting with `VITE_` is automatically injected into the frontend build:

```bash
# In .env.production
VITE_FEATURE_FLAG=enabled
VITE_API_TIMEOUT=5000
VITE_DEBUG_MODE=false
```

These become available in your frontend code:

```typescript
// In your React/Vue/etc. code
const featureEnabled = import.meta.env.VITE_FEATURE_FLAG;
const apiTimeout = import.meta.env.VITE_API_TIMEOUT;
```

### 3. SSH Key Management

#### Automatic Deploy Key Setup

If `GITHUB_TOKEN` is provided:
- Script checks if deploy key exists on GitHub
- Automatically adds deploy key if missing
- No manual intervention required

#### Manual Deploy Key Setup

If `GITHUB_TOKEN` is not provided:
- Script displays the public key
- Prompts you to add it to GitHub
- Waits for confirmation

#### Key Regeneration

Use `--regenerate-ssh-key` to:
- Delete existing keys (local, GitHub, OpenShift)
- Generate new keys
- Setup new deploy key

### 4. GitHub Webhook Automation

When `GITHUB_TOKEN` is provided, the script automatically:
- Creates webhooks for frontend and backend
- Configures them to trigger on push events
- Skips creation if webhooks already exist

Without `GITHUB_TOKEN`:
- Displays webhook URLs
- Prompts you to add them manually to GitHub

### 5. Database Reset

The `--reset-prod-db` flag provides a safe way to reset the database:

```bash
./oc-deploy.sh --reset-prod-db
```

**Process:**
1. Prompts for confirmation (requires typing "yes")
2. Deletes PostgreSQL deployment
3. Deletes PostgreSQL service
4. Deletes PVC (all data is lost)
5. Recreates database from scratch
6. Restarts backend to apply migrations

**Use Cases:**
- Development/staging environment resets
- Corrupted database recovery
- Schema migration issues
- Testing fresh deployments

### 6. Idempotent Operations

The script can be run multiple times safely:

- **Resources**: Only created if they don't exist
- **Secrets**: Updated if they exist, created if they don't
- **Deployments**: Updated if they exist, created if they don't
- **Routes**: Reused if they exist
- **SSH Keys**: Reused if valid, regenerated if missing

### 7. Validation and Error Handling

**Pre-flight Checks:**
- OpenShift CLI version (4.14+)
- OpenShift login status
- Environment file existence
- All required variables present
- Variable format validation

**Runtime Checks:**
- Resource creation success
- Deployment rollout status
- Pod readiness
- Route availability

**Error Messages:**
- Clear, actionable error messages
- Colored output for visibility
- Sensitive values masked in logs

## Troubleshooting

### Common Issues

#### 1. Missing Environment Variables

**Error:**
```
==> The following required environment variables are missing:
  - APP_NAME
  - POSTGRES_PASSWORD
```

**Solution:**
Add the missing variables to your `.env.production` file.

#### 2. Invalid Variable Format

**Error:**
```
==> Invalid name: 'My-App'. Must contain only lowercase letters, numbers, and hyphens.
```

**Solution:**
Fix the variable format according to validation rules (e.g., use `my-app` instead of `My-App`).

#### 3. OpenShift Login Required

**Error:**
```
==> Not logged into OpenShift. Please login first using:
oc login --token=<token> --server=<server-url>
```

**Solution:**
Login to OpenShift before running the script:
```bash
oc login --token=your-token --server=https://api.cluster.example.com:6443
```

#### 4. SSH Key Not Added to GitHub

**Error:**
Build fails with authentication error.

**Solution:**
1. Check if deploy key is added to GitHub repository
2. Go to: Repository → Settings → Deploy keys
3. Add the public key displayed by the script
4. Enable "Allow write access" if needed

#### 5. Database Connection Issues

**Error:**
Backend can't connect to database.

**Solution:**
1. Check PostgreSQL pod status:
   ```bash
   oc get pods -l app=postgresql
   ```
2. Check PostgreSQL logs:
   ```bash
   oc logs deployment/postgresql
   ```
3. Verify database credentials in secret:
   ```bash
   oc get secret <app-name>-env -o yaml
   ```

#### 6. Frontend Build Fails

**Error:**
Frontend build fails with missing environment variables.

**Solution:**
1. Ensure all `VITE_` variables are in `.env.production`
2. Check build logs:
   ```bash
   oc logs -f bc/frontend
   ```
3. Verify build config:
   ```bash
   oc get bc/frontend -o yaml
   ```

#### 7. Webhook Creation Fails

**Error:**
```
==> Failed to create GitHub webhook for frontend
```

**Solution:**
1. Verify `GITHUB_TOKEN` has correct permissions
2. Check token scopes: `repo`, `admin:repo_hook`
3. Manually add webhooks if automatic creation fails

### Debug Mode

To see detailed output, you can modify the script temporarily:

```bash
# Add at the top of the script (after set -euo pipefail)
set -x  # Enable debug mode
```

Or run with bash debug:

```bash
bash -x ./oc-deploy.sh
```

### Checking Deployment Status

```bash
# Check all resources
oc get all

# Check specific deployment
oc get deployment/backend
oc get deployment/frontend
oc get deployment/postgresql

# Check pod status
oc get pods

# Check pod logs
oc logs deployment/backend
oc logs deployment/frontend
oc logs deployment/postgresql

# Check routes
oc get routes

# Check secrets
oc get secrets
```

### Manual Cleanup

If you need to start fresh:

```bash
# Delete entire project (⚠️ WARNING: Deletes everything!)
oc delete project <project-name>

# Or delete specific resources
oc delete deployment/backend deployment/frontend deployment/postgresql
oc delete service/backend service/frontend service/postgresql
oc delete route/backend route/frontend
oc delete pvc/postgresql-data
oc delete secret/<app-name>-env git-secret
```

## Best Practices

### 1. Environment File Management

✅ **DO:**
- Keep `.env.production` in a secure location
- Use different env files for different environments
- Version control `.env.production.example` (without secrets)
- Use strong, unique passwords

❌ **DON'T:**
- Commit `.env.production` to Git
- Share production credentials
- Use default/weak passwords
- Reuse passwords across environments

### 2. GitHub Token Security

✅ **DO:**
- Use fine-grained personal access tokens
- Limit token scope to specific repositories
- Rotate tokens regularly
- Store tokens securely (password manager)

❌ **DON'T:**
- Use tokens with excessive permissions
- Share tokens
- Commit tokens to Git
- Use the same token for multiple purposes

### 3. Database Management

✅ **DO:**
- Backup database before using `--reset-prod-db`
- Use strong database passwords
- Monitor database storage usage
- Test migrations in staging first

❌ **DON'T:**
- Use `--reset-prod-db` in production without backups
- Use default database credentials
- Ignore database logs
- Skip migration testing

### 4. Deployment Strategy

✅ **DO:**
- Test in staging environment first
- Review changes before deploying
- Monitor deployment logs
- Keep deployment scripts updated
- Document custom configurations

❌ **DON'T:**
- Deploy directly to production without testing
- Ignore error messages
- Skip validation steps
- Modify deployed resources manually

### 5. SSH Key Management

✅ **DO:**
- Use separate SSH keys per project
- Rotate keys periodically
- Use `--regenerate-ssh-key` when compromised
- Keep private keys secure

❌ **DON'T:**
- Reuse SSH keys across projects
- Share private keys
- Commit keys to Git
- Ignore key rotation

### 6. Monitoring and Maintenance

✅ **DO:**
- Monitor application logs regularly
- Check resource usage (CPU, memory, storage)
- Update dependencies regularly
- Review and update environment variables
- Test disaster recovery procedures

❌ **DON'T:**
- Ignore warning messages
- Let storage fill up
- Use outdated dependencies
- Skip regular maintenance

## Script Architecture

### Function Organization

The script is organized into logical sections:

1. **Helper Functions**: Color output, status messages
2. **Validation Functions**: Input validation (name, email, URL, API key, password)
3. **Environment Loading**: Load and validate environment variables
4. **OpenShift Helpers**: Resource management, version checks
5. **Project Setup**: Project creation and selection
6. **SSH Key Management**: Key generation, GitHub integration
7. **Secret Management**: Dynamic secret creation
8. **Database Management**: PostgreSQL deployment and reset
9. **Application Deployment**: Frontend and backend deployment
10. **Webhook Management**: GitHub webhook automation
11. **Main Execution**: Argument parsing and orchestration

### Key Design Principles

- **Idempotency**: All operations can be safely repeated
- **Modularity**: Functions are small and focused
- **Error Handling**: Comprehensive error checking and reporting
- **Security**: Sensitive values masked, secure defaults
- **Flexibility**: Dynamic configuration from environment file
- **Automation**: Minimal manual intervention required

## Contributing

When modifying the script:

1. Maintain idempotency
2. Add validation for new variables
3. Update documentation
4. Test in staging environment
5. Follow existing code style
6. Add error handling
7. Update help text

## Support

For issues or questions:

1. Check this documentation
2. Review error messages carefully
3. Check OpenShift logs
4. Verify environment variables
5. Test in staging environment first

## License

This script is part of the full-stack application template and follows the same license as the main project.

---

**Last Updated**: 2025-01-25
**Script Version**: 2.0 (Optimized)