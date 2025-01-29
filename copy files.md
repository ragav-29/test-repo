# Variables
$remoteUser = "your_remote_user"
$remoteHost = "remote_server_ip_or_hostname"
$remoteFolder = "\\remote_server_ip_or_hostname\path\to\remote\folder"
$localFolder = "C:\path\to\local\folder"
$password = "your_remote_password" | ConvertTo-SecureString -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential($remoteUser, $password)

# Map the remote folder as a network drive
New-PSDrive -Name "RemoteDrive" -PSProvider "FileSystem" -Root $remoteFolder -Credential $credential

# Copy folder from remote server to local server
Copy-Item -Path "RemoteDrive:\*" -Destination $localFolder -Recurse -Force

# Check if the copy was successful
if ($?) {
    Write-Host "Folder copied successfully!"
} else {
    Write-Host "Failed to copy folder."
    exit 1
}

# Remove the mapped network drive
Remove-PSDrive -Name "RemoteDrive"



option 2: 
trigger:
- main

pool:
  vmImage: 'windows-latest'

steps:
- powershell: |
    # Run the PowerShell script
    .\copy-folder.ps1
  env:
    remoteUser: $(REMOTE_USER)
    remoteHost: $(REMOTE_HOST)
    remoteFolder: $(REMOTE_FOLDER)
    localFolder: $(LOCAL_FOLDER)
    password: $(REMOTE_PASSWORD)
  displayName: 'Copy Folder from Remote Server'


