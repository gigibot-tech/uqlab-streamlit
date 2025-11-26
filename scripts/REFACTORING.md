# OpenShift Deployment Script - Refactoring Guide

## Overview

The monolithic 1514-line script has been refactored into a modular structure following shell scripting best practices.

## Structure

```
scripts/
├── oc-deploy-new.sh          # Main script (171 lines)
└── lib/
    ├── 00-common.sh          # Utilities & output collection
    ├── 10-validation.sh      # Input validation
    ├── 20-environment.sh     # Environment management
    ├── 30-openshift.sh       # OpenShift operations
    ├── 40-ssh.sh             # SSH key management
    ├── 50-secrets.sh         # Secret management
    ├── 60-database.sh        # Database operations
    ├── 70-deployment.sh      # App deployment
    └── 80-webhooks.sh        # Webhook management
```

## Key Features

### 1. Output Collection
Functions collect deployment info in a global array, displayed at the end:
```bash
add_deployment_output "frontend_url" "https://..."
print_deployment_summary  # Shows all collected info
```

### 2. Error Handling
- Library functions **return error codes** (0=success, 1=failure)
- Main script **handles exits**
- Better testability and cleanup

### 3. Modularity
- Each library has a single responsibility
- Numbered prefixes ensure correct load order
- Easy to maintain and extend

## Usage

```bash
# Normal deployment
./scripts/oc-deploy-new.sh

# Custom env file
./scripts/oc-deploy-new.sh --env-file /path/to/.env

# Reset database
./scripts/oc-deploy-new.sh --reset-prod-db

# Regenerate SSH keys
./scripts/oc-deploy-new.sh --regenerate-ssh-key
```

## Migration

**Test and replace:**
```bash
# Test new script
./scripts/oc-deploy-new.sh

# If successful, replace original
mv scripts/oc-deploy.sh scripts/oc-deploy-old.sh
mv scripts/oc-deploy-new.sh scripts/oc-deploy.sh
```

## Library Reference

| Library | Purpose | Key Functions |
|---------|---------|---------------|
| **00-common.sh** | Core utilities | `print_status()`, `print_success()`, `print_error()`, `add_deployment_output()`, `print_deployment_summary()` |
| **10-validation.sh** | Input validation | `validate_name()`, `validate_email()`, `validate_git_url()`, `validate_api_key()` |
| **20-environment.sh** | Env management | `load_env_file()`, `validate_required_vars()` |
| **30-openshift.sh** | OC operations | `resource_exists()`, `apply_resource()`, `check_oc_version()`, `setup_project()` |
| **40-ssh.sh** | SSH keys | `setup_ssh_keys()`, `add_github_deploy_key()`, `delete_ssh_keys()` |
| **50-secrets.sh** | Secrets | `create_initial_app_env_secret()`, `update_app_env_secret_with_urls()` |
| **60-database.sh** | Database | `deploy_database()`, `reset_production_database()` |
| **70-deployment.sh** | App deployment | `deploy_frontend()`, `deploy_backend()`, `configure_frontend()`, `configure_backend()` |
| **80-webhooks.sh** | Webhooks | `setup_webhooks()`, `create_github_webhook()` |

## Benefits

✅ **88% smaller main script** (1514 → 171 lines)  
✅ **Modular & maintainable** - Easy to find and update code  
✅ **Better output** - Clean summary at the end  
✅ **100% backward compatible** - Same CLI interface  
✅ **Professional** - Follows best practices  

## Contributing

When adding functionality:
1. Choose appropriate library based on responsibility
2. Use `return` codes, not `exit`
3. Add user-facing info to `DEPLOYMENT_OUTPUT`
4. Test thoroughly

---
**Version**: 1.0.0 | **Created**: 2025-11-26