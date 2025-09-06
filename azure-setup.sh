#!/bin/bash

# Azure DevOps Setup Script for Freelenso Project
echo "🔧 Setting up Azure resources for Freelenso DevOps pipeline..."

# Install Azure CLI if not present
if ! command -v az &> /dev/null; then
    echo "Installing Azure CLI..."
    curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
fi

# Login to Azure
echo "🔐 Please login to Azure..."
az login

# Set subscription (if you have multiple)
echo "📋 Available subscriptions:"
az account list --output table
echo "Enter your subscription ID (or press Enter for default):"
read subscription_id
if [ ! -z "$subscription_id" ]; then
    az account set --subscription $subscription_id
fi

# Create resource group
RESOURCE_GROUP="freelenso-devops-rg"
LOCATION="eastus"
ACR_NAME="freelensoacr$(date +%s)"

echo "🏗️ Creating resource group: $RESOURCE_GROUP"
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Azure Container Registry (FREE tier)
echo "📦 Creating Azure Container Registry: $ACR_NAME"
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true

# Get ACR credentials
echo "🔑 Getting ACR credentials..."
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username --output tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value --output tsv)
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer --output tsv)

# Create App Service Plan (FREE tier)
APP_SERVICE_PLAN="freelenso-plan"
echo "🌐 Creating App Service Plan: $APP_SERVICE_PLAN"
az appservice plan create --name $APP_SERVICE_PLAN --resource-group $RESOURCE_GROUP --sku F1 --is-linux

# Create Web App for Django frontend
WEB_APP_NAME="freelenso-web-$(date +%s)"
echo "🚀 Creating Web App: $WEB_APP_NAME"
az webapp create --resource-group $RESOURCE_GROUP --plan $APP_SERVICE_PLAN --name $WEB_APP_NAME --deployment-container-image-name nginx

# Save configuration
cat > azure-config.env << EOF
# Azure Configuration for Freelenso DevOps
RESOURCE_GROUP=$RESOURCE_GROUP
ACR_NAME=$ACR_NAME
ACR_LOGIN_SERVER=$ACR_LOGIN_SERVER
ACR_USERNAME=$ACR_USERNAME
ACR_PASSWORD=$ACR_PASSWORD
WEB_APP_NAME=$WEB_APP_NAME
APP_SERVICE_PLAN=$APP_SERVICE_PLAN
LOCATION=$LOCATION
EOF

echo "✅ Azure setup completed!"
echo "📝 Configuration saved to azure-config.env"
echo ""
echo "🔧 Next steps:"
echo "1. Run Jenkins setup: cd jenkins-docker && ./setup-jenkins.sh"
echo "2. Configure Jenkins with Azure credentials"
echo "3. Push images to ACR: $ACR_LOGIN_SERVER"
echo "4. Deploy to Web App: $WEB_APP_NAME.azurewebsites.net"
