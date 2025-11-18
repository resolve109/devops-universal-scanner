// Azure Bicep Web App with security vulnerabilities
param webAppName string = 'vulnerable-webapp-${uniqueString(resourceGroup().id)}'
param location string = resourceGroup().location
param skuName string = 'F1'
param skuTier string = 'Free'

// Intentional Issue 1: App Service Plan without proper configuration
resource appServicePlan 'Microsoft.Web/serverfarms@2022-09-01' = {
  name: '${webAppName}-plan'
  location: location
  sku: {
    name: skuName
    tier: skuTier
  }
  properties: {
    reserved: false
  }
}

// Intentional Issue 2: Web App with security vulnerabilities
resource webApp 'Microsoft.Web/sites@2022-09-01' = {
  name: webAppName
  location: location
  properties: {
    serverFarmId: appServicePlan.id
    
    // Issue: HTTPS not enforced
    httpsOnly: false
    
    // Issue: Client affinity enabled (potential session fixation)
    clientAffinityEnabled: true
    
    siteConfig: {
      // Issue: HTTP 2.0 not enabled
      http20Enabled: false
      
      // Issue: Minimum TLS version too low
      minTlsVersion: '1.0'
      
      // Issue: FTP access allowed
      ftpsState: 'AllAllowed'
      
      // Issue: Always On disabled (for production apps)
      alwaysOn: false
      
      // Issue: Detailed error messages enabled
      detailedErrorLoggingEnabled: true
      httpLoggingEnabled: true
      
      // Issue: Application settings with secrets
      appSettings: [
        {
          name: 'DATABASE_CONNECTION'
          value: 'Server=tcp:server.database.windows.net,1433;Database=mydb;User ID=admin;Password=Password123!;'
        }
        {
          name: 'API_SECRET_KEY'
          value: 'sk-1234567890abcdefghijklmnopqrstuvwxyz'
        }
        {
          name: 'JWT_SECRET'
          value: 'mysupersecretjwtkey123'
        }
        {
          name: 'ENCRYPTION_KEY'
          value: 'hardcodedencryptionkey'
        }
      ]
      
      // Issue: Default documents that might expose information
      defaultDocuments: [
        'Default.htm'
        'Default.html'
        'Default.asp'
        'index.htm'
        'index.html'
        'iisstart.htm'
        'default.aspx'
        'index.php'
        'config.php'
        'phpinfo.php'
      ]
    }
  }
  
  // Issue: Identity not properly configured
  identity: {
    type: 'None'
  }
  
  tags: {
    Environment: 'production'
    // Issue: Sensitive information in tags
    AdminPassword: 'admin123'
    ServiceAccountKey: 'sa-key-123456'
  }
}

// Issue: Diagnostic settings not configured for monitoring
// Issue: No Application Insights configured

// Output sensitive information
output webAppUrl string = 'https://${webApp.properties.defaultHostName}'
output webAppFtpUrl string = 'ftp://${webApp.properties.ftpUsername}@${webApp.properties.hostNames[0]}'
