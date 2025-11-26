# Print System Documentation

## Overview

The OpenShift deployment script uses a structured print system that provides clear visual feedback during deployment. The system includes:

1. **Library Context Prefixes** - Shows which library module is executing
2. **Phase Headers** - Separates deployment into logical phases
3. **Color-Coded Messages** - Different colors for different message types

## Print Functions

All print functions are defined in `scripts/lib/00-common.sh`.

### Basic Print Functions

All print functions accept an optional second parameter for the library context name.

#### `print_status(message, [library])`
Prints informational status messages in teal.

**Example:**
```bash
print_status "Checking OpenShift version..." "openshift"
```

**Output:**
```
[openshift] ==> Checking OpenShift version...
```

**Without library context:**
```bash
print_status "General message"
```

**Output:**
```
==> General message
```

#### `print_success(message, [library])`
Prints success messages in green.

**Example:**
```bash
print_success "Deployment completed successfully!" "deployment"
```

**Output:**
```
[deployment] ==> Deployment completed successfully!
```

#### `print_error(message, [library])`
Prints error messages in red to stderr.

**Example:**
```bash
print_error "Failed to connect to OpenShift cluster" "openshift"
```

**Output:**
```
[openshift] ==> Failed to connect to OpenShift cluster
```

#### `print_warning(message, [library])`
Prints warning messages in yellow.

**Example:**
```bash
print_warning "GITHUB_TOKEN not set. Cannot verify deploy key automatically." "ssh"
```

**Output:**
```
[ssh] ==> GITHUB_TOKEN not set. Cannot verify deploy key automatically.
```

### Section Headers

#### `print_section_header(title)`
Prints a phase header with box-drawing characters.

**Example:**
```bash
print_section_header "PHASE 1: INITIALIZATION"
```

**Output:**
```
╔═══════════════════════════════════════════════════════════╗
║  PHASE 1: INITIALIZATION                                  ║
╚═══════════════════════════════════════════════════════════╝
```

## Library Context System

Each library file passes its context name as the second parameter to print functions. This prefix appears in all log messages from that library.

### Library Contexts

| Library File | Context Name | Purpose |
|--------------|--------------|---------|
| `00-common.sh` | (none) | Common utilities - no prefix |
| `10-validation.sh` | `validation` | Input validation |
| `20-environment.sh` | `environment` | Environment variable management |
| `30-openshift.sh` | `openshift` | OpenShift operations |
| `40-ssh.sh` | `ssh` | SSH key management |
| `50-secrets.sh` | `secrets` | Secret creation and management |
| `60-database.sh` | `database` | Database deployment |
| `70-deployment.sh` | `deployment` | Application deployment |
| `75-oauth.sh` | `oauth` | OAuth2 Proxy configuration |
| `80-webhooks.sh` | `webhooks` | GitHub webhook automation |

### Using Library Context in Functions

In each function within a library file, pass the library name as the second parameter:

```bash
#!/usr/bin/env bash
#
# Library Description
#

# Example function
my_function() {
    print_status "Starting operation..." "library-name"
    
    # ... function logic ...
    
    if [[ $? -eq 0 ]]; then
        print_success "Operation completed" "library-name"
    else
        print_error "Operation failed" "library-name"
        return 1
    fi
}
```

**Important:** The library name should match the filename pattern (e.g., `30-openshift.sh` uses `"openshift"`).

## Deployment Phases

The main deployment script is organized into 7 phases:

### Phase 1: Initialization
- Load environment variables
- Validate required variables

### Phase 2: Prerequisites Check
- Check OpenShift client version
- Verify OpenShift login status

### Phase 3: Project Setup
- Create/verify OpenShift project
- Setup SSH keys for Git access

### Phase 4: Database Deployment
- Create application secrets
- Deploy PostgreSQL database

### Phase 5: Application Deployment
- Deploy frontend application
- Deploy backend application
- Update secrets with URLs

### Phase 6: Configuration
- Configure frontend environment
- Configure backend environment
- Group application resources

### Phase 7: Post-Deployment
- Setup GitHub webhooks
- Display deployment summary

## Example Output

Here's what a typical deployment looks like:

```
Welcome to the OpenShift Deployment Script!

╔═══════════════════════════════════════════════════════════╗
║  PHASE 1: INITIALIZATION                                  ║
╚═══════════════════════════════════════════════════════════╝
[environment] ==> Loading environment variables from .env.production...
[environment] ==> Environment variables loaded successfully
[validation] ==> Validating required variables...
[validation] ==> Validating project name: my-app
[validation] ==> Validating email: admin@example.com
[validation] ==> All required variables validated successfully

╔═══════════════════════════════════════════════════════════╗
║  PHASE 2: PREREQUISITES CHECK                             ║
╚═══════════════════════════════════════════════════════════╝
[openshift] ==> Checking OpenShift client version...
[openshift] ==> OpenShift client version: 4.14
[openshift] ==> Verifying OpenShift login status...
[openshift] ==> Successfully logged in to OpenShift

╔═══════════════════════════════════════════════════════════╗
║  PHASE 3: PROJECT SETUP                                   ║
╚═══════════════════════════════════════════════════════════╝
[openshift] ==> Setting up OpenShift project: my-app
[openshift] ==> Project 'my-app' already exists
[ssh] ==> Checking SSH keys...
[ssh] ==> SSH key pair already exists
[ssh] ==> Verifying GitHub deploy key...
[ssh] ==> Deploy key verified on GitHub

╔═══════════════════════════════════════════════════════════╗
║  PHASE 4: DATABASE DEPLOYMENT                             ║
╚═══════════════════════════════════════════════════════════╝
[secrets] ==> Creating application environment secret...
[secrets] ==> Secret 'app-env' created successfully
[database] ==> Deploying PostgreSQL database...
[database] ==> Database deployment complete

╔═══════════════════════════════════════════════════════════╗
║  PHASE 5: APPLICATION DEPLOYMENT                          ║
╚═══════════════════════════════════════════════════════════╝
[deployment] ==> Deploying frontend application...
[deployment] ==> Frontend build started
[deployment] ==> Deploying backend application...
[deployment] ==> Backend build started
[secrets] ==> Updating secrets with application URLs...

╔═══════════════════════════════════════════════════════════╗
║  PHASE 6: CONFIGURATION                                   ║
╚═══════════════════════════════════════════════════════════╝
[deployment] ==> Configuring frontend environment...
[deployment] ==> Configuring backend environment...
[openshift] ==> Grouping application resources...

╔═══════════════════════════════════════════════════════════╗
║  PHASE 7: POST-DEPLOYMENT                                 ║
╚═══════════════════════════════════════════════════════════╝
[webhooks] ==> Setting up GitHub webhooks...
[webhooks] ==> Webhooks configured successfully

==> Deployment completed successfully!

╔═══════════════════════════════════════════════════════════╗
║           DEPLOYMENT SUMMARY                              ║
╚═══════════════════════════════════════════════════════════╝

Frontend URL:
  https://my-app-frontend.apps.cluster.example.com

Backend URL:
  https://my-app-backend.apps.cluster.example.com

Note: Builds may take a few minutes to complete.
Once builds are finished, your application will be accessible at the URLs above.
```

## Color Codes

The following color codes are used throughout the script:

- **TEAL** (`\033[0;36m`) - Status messages
- **GREEN** (`\033[0;32m`) - Success messages
- **RED** (`\033[0;31m`) - Error messages
- **YELLOW** (`\033[1;33m`) - Warning messages
- **BLUE** (`\033[0;34m`) - Library context prefix and section headers
- **NC** (`\033[0m`) - No color (reset)

## Best Practices

### When Adding New Functions

1. **Always use the appropriate print function** - Don't use `echo` directly for user-facing messages
2. **Pass library context** - Always pass the library name as the second parameter to print functions
3. **Use descriptive messages** - Messages should clearly indicate what's happening
4. **Be consistent** - Follow the existing message patterns

### Message Guidelines

- **Status messages**: Use present continuous tense ("Checking...", "Deploying...", "Creating...")
- **Success messages**: Use past tense ("Created successfully", "Deployment complete")
- **Error messages**: Be specific about what failed and why
- **Warning messages**: Explain the issue and potential impact

### Example

```bash
# Good
print_status "Deploying frontend application..."
# ... deployment logic ...
print_success "Frontend deployment complete"

# Bad
echo "deploying frontend"  # No context, inconsistent format
```

## Troubleshooting

### Library Context Not Showing

If the library context prefix is not appearing in log messages:

1. Check that `set_library_context()` is called at the top of the library file
2. Verify the library file is being sourced correctly in `oc-deploy.sh`
3. Ensure you're using the print functions from `00-common.sh`, not plain `echo`

### Colors Not Displaying

If colors are not showing in your terminal:

1. Check that your terminal supports ANSI color codes
2. Verify the color variables are defined in `00-common.sh`
3. Some CI/CD systems may strip colors - this is normal

## Future Enhancements

Potential improvements to the print system:

- Progress indicators (e.g., "Step 3/10")
- Elapsed time tracking per phase
- Verbose/quiet modes
- Log file output option
- JSON output for CI/CD integration