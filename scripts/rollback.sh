#!/bin/bash

RESOURCE_GROUP="rg-alpaca-trader-prod"
APP_NAME=$1

if [ -z "$APP_NAME" ]; then
    echo "Usage: ./rollback.sh <api|engine|web>"
    exit 1
fi

echo "Rolling back $APP_NAME..."

if [ "$APP_NAME" == "api" ] || [ "$APP_NAME" == "engine" ]; then
    FULL_APP_NAME="alpaca-trader-production-$APP_NAME"
    
    # Get previous revision
    PREVIOUS_REVISION=$(az containerapp revision list \
      --name $FULL_APP_NAME \
      --resource-group $RESOURCE_GROUP \
      --query "[1].name" -o tsv)
    
    if [ -z "$PREVIOUS_REVISION" ]; then
        echo "No previous revision found for $APP_NAME"
        exit 1
    fi
    
    echo "Rolling back to revision: $PREVIOUS_REVISION"
    
    # Activate previous revision
    az containerapp revision activate \
      --name $FULL_APP_NAME \
      --resource-group $RESOURCE_GROUP \
      --revision $PREVIOUS_REVISION
    
    # Route all traffic to previous
    az containerapp ingress traffic set \
      --name $FULL_APP_NAME \
      --resource-group $RESOURCE_GROUP \
      --revision-weight $PREVIOUS_REVISION=100
    
    echo "✅ Rolled back $APP_NAME to revision: $PREVIOUS_REVISION"
    
elif [ "$APP_NAME" == "web" ]; then
    echo "For Static Web Apps, use Git to revert the commit and re-deploy"
    echo "Example:"
    echo "  git revert HEAD"
    echo "  git push origin main"
fi

echo "Rollback complete!"