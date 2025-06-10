**Create Keygen in windows**

ssh-keygen -t rsa

**Sample hosts.ini (Inventory File)**
ini
Copy
Edit
[windows]
192.168.1.5

[all:vars]
ansible_user=ragav
ansible_password=yourpassword
ansible_connection=ssh
ansible_port=22
ansible_shell_type=cmd
ansible_shell_executable=powershell

**Is OpenSSH Server installed and running on Windows?
On the Windows machine :

Run this in PowerShell:**

powershell
Copy
Edit
Get-Service sshd
If it’s not installed:
**
powershell**

Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd
Set-Service -Name sshd -StartupType 'Automatic'
✅ **3. Is port 22 allowed in Windows Firewall & Network Security Group (NSG)?
If this is an Azure VM:

Go to the VM's Networking tab in the Azure portal.

Under Inbound port rules, ensure SSH (port 22) is allowed from your Ubuntu server's IP (or 0.0.0.0/0 for testing).

On the Windows firewall:**

powershell
Copy
Edit
New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH Server' -Enabled True -Protocol TCP -Direction Inbound -Action Allow -LocalPort 22
✅ 4. Is the IP correct?
You may have confused the internal IP (like 172.31.X.X) with the public IP or vice versa. Confirm using:

powershell
Copy
Edit
Invoke-RestMethod -Uri "http://ifconfig.me"
**
File Permissions
**
icacls "$env:USERPROFILE\.ssh\authorized_keys" /inheritance:r
icacls "$env:USERPROFILE\.ssh\authorized_keys" /grant "$($env:USERNAME):F"



Example usage in playbook
yaml
===================================================================================================
- name: Create backup folder on Ubuntu control node
  hosts: local
  gather_facts: false
  tasks:
    - name: Ensure /home/ubuntu/backup exists
      file:
        path: /home/ubuntu/backup
        state: directory
        mode: '0755'
**✅ Full workflow example
You can combine Windows and local tasks in one playbook like this:
**
yaml
========================
- name: Backup blogify/bin on Windows
  hosts: windows
  gather_facts: false
  vars:
    zip_date: "{{ lookup('pipe', 'date +%Y%m%d') }}"
    source_path: "C:\\Blogify\\bin"
    backup_dir: "C:\\Backup"
    zip_name: "Blogify_bin_{{ zip_date }}.zip"
    zip_path: "{{ backup_dir }}\\{{ zip_name }}"

  tasks:
    - name: Ensure backup folder exists on Windows
      win_file:
        path: "{{ backup_dir }}"
        state: directory

    - name: Create ZIP of Blogify\bin
      win_command: powershell.exe -Command "Compress-Archive -Path '{{ source_path }}\\*' -DestinationPath '{{ zip_path }}' -Force"

    - name: Fetch ZIP from Windows to control node
      fetch:
        src: "{{ zip_path }}"
        dest: "/home/ubuntu/backup/"
        flat: yes


- name: Ensure backup folder exists on control node
  hosts: local
  gather_facts: false
  tasks:
    - name: Create /home/ubuntu/backup
      file:
        path: /home/ubuntu/backup
        state: directory
        mode: '0755'
