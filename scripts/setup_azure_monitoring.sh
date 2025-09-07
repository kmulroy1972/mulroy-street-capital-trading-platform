#!/bin/bash

RESOURCE_GROUP="rg-alpaca-trader-prod"
WORKSPACE_NAME="alpaca-logs"
LOCATION="eastus2"

echo "Setting up Azure monitoring for Alpaca Trading System..."

# Create Log Analytics Workspace
echo "Creating Log Analytics workspace..."
az monitor log-analytics workspace create \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $WORKSPACE_NAME \
  --location $LOCATION

# Get workspace ID and key
WORKSPACE_ID=$(az monitor log-analytics workspace show \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $WORKSPACE_NAME \
  --query customerId -o tsv)

WORKSPACE_KEY=$(az monitor log-analytics workspace get-shared-keys \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $WORKSPACE_NAME \
  --query primarySharedKey -o tsv)

echo "✅ Log Analytics workspace created"

# Create Application Insights
echo "Creating Application Insights..."
az monitor app-insights component create \
  --app alpaca-insights \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP \
  --workspace $WORKSPACE_ID

echo "✅ Application Insights created"

# Create metric alerts
echo "Creating metric alerts..."

# High CPU Alert
az monitor metrics alert create \
  --name "alpaca-high-cpu" \
  --resource-group $RESOURCE_GROUP \
  --scopes "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.App/containerApps/alpaca-trader-production-engine" \
  --condition "avg Percentage CPU > 80" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --description "Alert when engine CPU usage is high"

# High Memory Alert  
az monitor metrics alert create \
  --name "alpaca-high-memory" \
  --resource-group $RESOURCE_GROUP \
  --scopes "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.App/containerApps/alpaca-trader-production-engine" \
  --condition "avg Working Set Bytes > 1073741824" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --description "Alert when engine memory usage exceeds 1GB"

# Container restart alert
az monitor metrics alert create \
  --name "alpaca-container-restarts" \
  --resource-group $RESOURCE_GROUP \
  --scopes "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.App/containerApps/alpaca-trader-production-engine" \
  --condition "total Restarts > 0" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --description "Alert when containers restart"

echo "✅ Metric alerts created"

# Create action group for notifications
echo "Creating action group..."
az monitor action-group create \
  --name "alpaca-alerts" \
  --resource-group $RESOURCE_GROUP \
  --short-name "alpaca"

echo "✅ Action group created"

# Update container apps to use monitoring
echo "Enabling monitoring for container apps..."

# Update API app
az containerapp update \
  --name alpaca-trader-production-api \
  --resource-group $RESOURCE_GROUP \
  --set-env-vars APPINSIGHTS_INSTRUMENTATIONKEY="$(az monitor app-insights component show --app alpaca-insights --resource-group $RESOURCE_GROUP --query instrumentationKey -o tsv)"

# Update Engine app  
az containerapp update \
  --name alpaca-trader-production-engine \
  --resource-group $RESOURCE_GROUP \
  --set-env-vars APPINSIGHTS_INSTRUMENTATIONKEY="$(az monitor app-insights component show --app alpaca-insights --resource-group $RESOURCE_GROUP --query instrumentationKey -o tsv)"

echo "✅ Container apps updated with monitoring"

echo ""
echo "================================"
echo "Monitoring Setup Complete!"
echo "================================"
echo "Workspace ID: $WORKSPACE_ID"
echo "Application Insights: alpaca-insights"
echo ""
echo "View logs with:"
echo "  az monitor log-analytics query -w $WORKSPACE_ID --analytics-query 'ContainerAppConsoleLogs_CL | order by TimeGenerated desc'"
echo ""
echo "Monitor in Azure portal:"
echo "  https://portal.azure.com/#@/resource/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.App/containerApps/alpaca-trader-production-engine/overview"