# Infrastructure Documentation

## Overview

This directory contains Infrastructure as Code (IaC) templates for deploying the Alpaca Trader application to Azure using Bicep templates.

## Prerequisites

Before deploying, ensure you have:

- **Azure CLI** (v2.50.0+)
  ```bash
  curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
  ```

- **Bicep CLI** (automatically installed with Azure CLI)
  ```bash
  az bicep install
  az bicep upgrade
  ```

- **Azure Subscription** with sufficient permissions to create resources

- **jq** for JSON processing
  ```bash
  # macOS
  brew install jq
  # Ubuntu/Debian
  sudo apt-get install jq
  ```

## Authentication

### Option 1: Interactive Login (Development)
```bash
az login
az account set --subscription <your-subscription-id>
```

### Option 2: Service Principal (CI/CD)
```bash
az login --service-principal \
  --username <app-id> \
  --password <password> \
  --tenant <tenant-id>
```

### Option 3: GitHub OIDC (Recommended for CI/CD)
Run the setup script to configure passwordless authentication:
```bash
./setup-oidc.sh
```

## Deployment

### Step 1: Configure Parameters
Edit `parameters.json` to match your requirements:
- `environmentName`: dev, staging, or prod
- `location`: Azure region (e.g., eastus2)
- `resourcePrefix`: Naming prefix for resources

### Step 2: Deploy Infrastructure
```bash
./deploy.sh
```

The script will prompt for secure parameters:
- PostgreSQL admin password
- Alpaca API credentials
- JWT secret

### Step 3: Post-Deployment Configuration
After successful deployment:

1. **Configure Container Registry**
   ```bash
   # Login to ACR
   az acr login --name <acr-name>
   
   # Build and push images (from project root)
   docker build -t <acr-name>.azurecr.io/alpaca-api:latest ./apps/api
   docker push <acr-name>.azurecr.io/alpaca-api:latest
   ```

2. **Update Container Apps**
   Container Apps will automatically pull the latest images once pushed to ACR.

3. **Configure Static Web App**
   Link your GitHub repository for automatic deployments.

## Resources Deployed

| Resource Type | Purpose | Naming Convention |
|---------------|---------|-------------------|
| Resource Group | Container for all resources | `rg-alpaca-trader-{env}` |
| Container Registry | Docker image storage | `acr{uniqueString}` |
| Container Apps Environment | Hosting for microservices | `{prefix}-{env}-env-{suffix}` |
| Container App (API) | REST API service | `{prefix}-{env}-api` |
| Container App (Engine) | Trading engine | `{prefix}-{env}-engine` |
| PostgreSQL Server | Database | `{prefix}-{env}-postgres-{suffix}` |
| Redis Cache | Caching layer | `{prefix}-{env}-redis-{suffix}` |
| Key Vault | Secrets management | `{prefix}-{env}-kv-{suffix}` |
| Static Web App | Frontend hosting | `{prefix}-{env}-web-{suffix}` |
| Managed Identities | Secure access | `{prefix}-{env}-{service}-identity` |

## Outputs

After deployment, the following information is available:

- **Container Registry Login Server**: For pushing Docker images
- **API App URL**: Public endpoint for the REST API
- **Static Web App URL**: Frontend application URL
- **Key Vault URI**: For accessing secrets
- **PostgreSQL FQDN**: Database connection endpoint

## Security

- **Managed Identities**: Container Apps use managed identities to access Key Vault
- **Key Vault**: All secrets are stored in Azure Key Vault
- **Network Security**: Redis and PostgreSQL are configured with minimal required access
- **RBAC**: Role-based access control for all resources

## Monitoring

Resources are tagged for cost tracking and management:
- `environment`: Environment name (dev/staging/prod)
- `project`: alpaca-trader

## Cleanup

To destroy all infrastructure:
```bash
./destroy.sh
```

**⚠️ WARNING**: This will permanently delete all resources and data.

## Troubleshooting

### Common Issues

1. **Deployment fails with "Resource name already exists"**
   - The `uniqueString()` function should prevent this, but if it occurs, delete the conflicting resource or change the `resourcePrefix` parameter.

2. **Key Vault access denied**
   - Ensure your account has Key Vault Administrator role or proper access policies.

3. **Container Apps fail to start**
   - Check that Docker images exist in the Container Registry
   - Verify managed identity has access to Key Vault secrets

4. **PostgreSQL connection issues**
   - Verify firewall rules allow your IP address
   - Check that the database user has proper permissions

### Useful Commands

```bash
# Check deployment status
az deployment group list --resource-group rg-alpaca-trader-dev --output table

# View resource group resources
az resource list --resource-group rg-alpaca-trader-dev --output table

# Get Container App logs
az containerapp logs show --name alpaca-trader-dev-api --resource-group rg-alpaca-trader-dev

# Test Key Vault access
az keyvault secret show --vault-name <vault-name> --name APCA-API-KEY-ID
```

## Cost Optimization

- **Development**: Use Basic tiers for all services
- **Production**: Scale up based on actual usage
- **Cleanup**: Regularly destroy development environments when not in use