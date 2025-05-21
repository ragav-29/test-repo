# Ensure PM2 is installed
if (-not (Get-Command pm2 -ErrorAction SilentlyContinue)) {
    Write-Host "Installing PM2 globally..."
    npm install -g pm2
    $npmPath = npm config get prefix
    $env:Path += ";$npmPath"
}

# Navigate to app directory
Set-Location "C:\nextjs-app"

# Install dependencies
npm install --production

# Stop existing instance if running
try { pm2 delete nextjs-app } catch { Write-Host "No existing process to delete" }

# Start application with PM2
pm2 start npm --name "nextjs-app" -- start

# Save PM2 process list
pm2 save

# Verify
pm2 list


-_-_-_-_-_-_-_-

# Ensure PM2 is installed
if (-not (Get-Command pm2 -ErrorAction SilentlyContinue)) {
    Write-Host "Installing PM2 globally..."
    npm install -g pm2
    $npmPath = npm config get prefix
    $env:Path += ";$npmPath"
}

# Navigate to app directory
Set-Location "C:\nextjs-app"

# Install dependencies
npm install --production

# Stop existing instance if running
try {
    pm2 delete nextjs-app
} catch {
    Write-Host "No existing process to delete"
}

# Start application with PM2 using ecosystem.config.js
pm2 start ecosystem.config.js --only nextjs-app

# Save PM2 process list
pm2 save

# Verify
pm2 list

