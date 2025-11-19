// Azure Bicep template with intentional security issues for testing
param storageAccountName string = 'testingaccount123'
param location string = resourceGroup().location
param environment string = 'dev'

// Intentional Issue 1: No encryption at rest specified
// Intentional Issue 2: Public access allowed
// Intentional Issue 3: No secure transfer required
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    // Issue: Public access allowed (should be disabled)
    allowBlobPublicAccess: true
    
    // Issue: Secure transfer not required
    supportsHttpsTrafficOnly: false
    
    // Issue: No minimum TLS version specified
    minimumTlsVersion: 'TLS1_0'
    
    // Issue: Network access rules too permissive
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
      ipRules: []
      virtualNetworkRules: []
    }
    
    // Issue: No encryption configuration
    encryption: {
      services: {
        blob: {
          enabled: false
        }
        file: {
          enabled: false
        }
      }
      keySource: 'Microsoft.Storage'
    }
  }
  
  tags: {
    Environment: environment
    // Issue: Sensitive information in tags
    DatabasePassword: 'admin123'
    ApiKey: 'sk-1234567890abcdef'
  }
}

// Intentional Issue 4: Blob container with public access
resource blobContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  name: '${storageAccount.name}/default/publiccontainer'
  properties: {
    // Issue: Public access level too permissive
    publicAccess: 'Container'
    metadata: {
      // Issue: Sensitive data in metadata
      password: 'secretpassword123'
    }
  }
}

// Output potentially sensitive information
output storageAccountKey string = storageAccount.listKeys().keys[0].value
output connectionString string = 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value}'
