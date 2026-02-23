# Deployment Guide - Fabritius-NG

## Requirements

- Linux server (Debian/Ubuntu)
- Python 3.10+
- Git
- Nginx (for reverse proxy)

## Connect to Server

Access your server via SSH:

First, connect to OpenVPN (IDLab)

```bash
ssh user@your-server.com
# or with specific hostname
ssh root@hensor.privatedmz
```

**Using SSH keys to connect to server (recommended):**[OPTIONAL]
```bash
# Generate SSH key on your local machine (if you don't have one)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy public key to server (hensor)
ssh-copy-id user@your-server.com

# Now connect without password
ssh user@your-server.com
```

**Store credentials locally** (never in git!):  
Create a `.login` file in your project root (already in .gitignore):
```
Server: your-server.com
User: root
```

Once connected, proceed with the setup steps below.

## Server Setup [OPTIONAL]

If starting with a fresh server, install required packages:

```bash
# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y nginx python3 python3-venv python3-pip build-essential git

# Verify nginx is running
systemctl status nginx --no-pager

# Verify nginx is listening on port 80
ss -tulpn | grep :80
# or
sudo lsof -i :80
```

**Expected output:**
```
● nginx.service - A high performance web server and a reverse proxy server
   Loaded: loaded (...; enabled; preset: enabled)
   Active: active (running) since ...
```
And for port check:
```
tcp   LISTEN  0  511  0.0.0.0:80  0.0.0.0:*  users:(("nginx",pid=...))
```

If nginx is **not running**, start it:
```bash
systemctl start nginx
systemctl enable nginx
```

**What is Nginx?**  
Nginx acts as a reverse proxy and provides:
- **Traffic routing** - Routes requests to different apps based on URL
- **Static content caching** - Improves performance
- **Multiple apps** - Run several Python apps on one server (different ports)
- **Load balancing** - Distributes traffic across instances

**Architecture:**
```
Internet (port 80/443) → Nginx → Python App (port 8003)
                              → Other App (port 8001)
                              → Another App (port 8002)
```

## Initial Deployment

### Production Setup (Recommended)

For production, use a **dedicated user per app** and **systemd service** for better security and management.

**Why a dedicated user per app?**
- **Security isolation**: If one app is compromised, attacker cannot access other apps
- **Resource tracking**: Easy to see which app uses which resources
- **Permission control**: Each app only has access to its own files
- **Best practice**: One user per service (e.g., `fabritius-ng-user`, `streamlit-user`, `api-user`)

#### 1. Create Dedicated User

```bash
# Create a user for this app (no login, no sudo access)
adduser --gecos "Fabritius-NG User" --disabled-password fabritius-ng-user
```

**What this does:**
- `--gecos "Fabritius-NG User"`: Sets the user's full name/description field 
- `--disabled-password`: No password login (more secure)
- Creates home directory `/home/fabritius-ng-user`
- User can only read/write in their own directories
- Cannot access other users' files
- Cannot use sudo

**Verify user exists:**
```bash
id fabritius-ng-user
# Expected: uid=1001(fabritius-ng-user) gid=1001(fabritius-ng-user) groups=1001(fabritius-ng-user)
```

#### 2. Setup Application Directory

**Run as root user** - the following commands need elevated privileges:

Web applications typically run from `/opt`:

```bash
# Create app directory in /opt (requires root)
mkdir -p /opt/Fabritius-NG
cd /opt/Fabritius-NG
```

**GitHub SSH Authentication Setup:**

Before cloning, setup SSH keys so the server can authenticate with GitHub:

```bash
# 1. Generate SSH key on the SERVER (no passphrase for automation)
ssh-keygen -t ed25519 -C "fabritius-ng-github-key"
# When prompted for filename: Press ENTER (use default ~/.ssh/id_ed25519)
# When prompted for passphrase: Press ENTER twice (no passphrase for servers)

# 2. Verify key permissions (ssh-keygen does this automatically)
ls -la ~/.ssh/
# Expected:
# -rw------- 1 root root  464 Jan 19 22:30 id_ed25519      (private key - 600)
# -rw-r--r-- 1 root root  103 Jan 19 22:30 id_ed25519.pub  (public key - 644)

# 3. Display the PUBLIC key
cat ~/.ssh/id_ed25519.pub
# Copy the ENTIRE output (starts with "ssh-ed25519 ...")

# 4. Add to GitHub
# - Go to https://github.com/settings/keys
# - Click "New SSH key"
# - Title: "Hensor Server" (or any descriptive name)
# - Pick Auth keh, (other key is only if you want to make commits)
# - Paste the public key
# - Click "Add SSH key"

# 5. Test the connection
ssh -T git@github.com
# Expected: "Hi username! You've successfully authenticated..."
# If you get "Are you sure you want to continue connecting?": Type "yes"

# 6. Now clone the repository
cd /opt/Fabritius-NG
git clone git@github.com:drdwitte/Fabritius-NG.git .
# Clones directly into: /opt/Fabritius-NG/
```

**Important Notes:**
- The public key (`id_ed25519.pub`) is safe to share with GitHub
- NEVER share the private key (`id_ed25519`)
- The `.` at the end of git clone means "clone into current directory"

```bash
# After cloning, assign ownership to app user
chown -R fabritius-ng-user:fabritius-ng-user /opt/Fabritius-NG

# Set permissions (owner: read+write+execute, group: read+execute, others: none)
chmod 750 /opt/Fabritius-NG
```

#### 3. Setup Virtual Environment

Switch to the app user and create venv:

```bash
# Become the app user
su - fabritius-ng-user

# Navigate to app
cd /opt/Fabritius-NG

# Create and activate venv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Configure Environment

```bash
# Create .env file
# It contains the OpenAI keys, and the connection information for Supabase
nano .env
```

**⚠️ IMPORTANT: Server HOST setting**
- Use `FABRITIUS_HOST="0.0.0.0"` for server deployment (listens on all interfaces)
- The default `127.0.0.1` in config.py is only for local Windows development
- If you use `127.0.0.1` on the server, nginx cannot connect to your app!

**⚠️ IMPORTANT: Base path for reverse proxy**
- Use `FABRITIUS_BASE_PATH="/fabritius"` to match your nginx location path
- This ensures all routes and navigation work correctly behind the proxy
- Without this, navigation to /detail, /label, etc. will result in 404 errors
- Keep commented out (or empty) for local development

**Essential settings:**
```env
# Server (choose a free port if running multiple apps!)
FABRITIUS_HOST="0.0.0.0"  # MUST be 0.0.0.0 for server deployment!
FABRITIUS_PORT=1234  # Your chosen port
FABRITIUS_RELOAD=False  # No auto-reload in production

# Reverse proxy configuration (REQUIRED for nginx deployment!)
FABRITIUS_BASE_PATH="/fabritius"  # Must match nginx location path

# Secrets
FABRITIUS_SUPABASE_URL="https://your-project.supabase.co"
FABRITIUS_SUPABASE_KEY="your-key"
FABRITIUS_OPENAI_API_KEY="sk-your-key"

# Optional
FABRITIUS_TITLE="Your Title"
FABRITIUS_IMAGE_BASE_URL="https://your-cdn.com"
```

**Port conflicts:** Check available ports with `sudo lsof -i :1234` before choosing.

**Secure the file:**
```bash
chmod 600 .env  # Only owner can read/write
```


#### 5. Test Manually (Optional)
Before creating a service, test the app:

```bash
# Run in background with logs (as fabritius-ng-user, use /tmp/)
nohup python Fabritius-NG.py > /tmp/fabritius-ng.log 2>&1 &

# Check if running
ps aux | grep Fabritius-NG.py
# example output: fabriti+  300955 11.9  0.5 289216 98296 pts/0    Sl   23:24   0:01 python Fabritius-NG.py => 23:24 start time followed by commmand running; 300955 is PID

# Check port is listening
ss -tulpn | grep 1234  # Replace 1234 with your FABRITIUS_PORT
# example output: tcp   LISTEN 0      2048       127.0.0.1:1234      0.0.0.0:*    users:(("python",pid=300955,fd=19)) => PID matches

# View logs
tail -f /tmp/fabritius-ng.log

# Stop when satisfied (find PID with ps aux)
kill <PID>
```

**nohup explained:**
- `nohup`: Keep running after logout
- `> /var/log/fabritius-ng.log`: Redirect stdout to log file
- `2>&1`: Redirect stderr to same file
- `&`: Run in background

#### 6. Create Systemd Service

**Why systemd before nginx?** First create a stable, auto-starting service on port 1234, then configure nginx to proxy traffic to it.

Exit back to root user and create service file:

```bash
exit  # Exit from fabritius-ng-user back to root

nano /etc/systemd/system/fabritius-ng.service
```

**Service file content:**
```ini
[Unit]
Description=Fabritius-NG NiceGUI Application
After=network.target

[Service]
Type=simple
User=fabritius-ng-user
Group=fabritius-ng-user
WorkingDirectory=/opt/Fabritius-NG
Environment="PATH=/opt/Fabritius-NG/venv/bin"
ExecStart=/opt/Fabritius-NG/venv/bin/python Fabritius-NG.py
Restart=always
RestartSec=10

StandardOutput=append:/var/log/fabritius-ng.log
StandardError=append:/var/log/fabritius-ng-error.log

[Install]
WantedBy=multi-user.target
```


```bash
#Explanation file above
#After= wait until network becomes operational
#WantedBy => means service will reboot after system reboot, regular service
```


**Enable and start service:**
```bash
# Reload systemd to recognize new service
systemctl daemon-reload

# Enable service (start on boot) (creates symlink)
systemctl enable fabritius-ng

# Start service now
systemctl start fabritius-ng

# Check status
systemctl status fabritius-ng --no-pager

# FYI to remove
#1 stop
#systemctl stop fabritius-ng
# 2. Disable: removes autostart link
#systemctl disable fabritius-ng
# 3. remove service file
#rm /etc/systemd/system/fabritius-ng.service
# 4. Reload systemd
#systemctl daemon-reload
```

**What is systemd?**  
`systemctl` manages all services on Ubuntu/Debian servers. It handles:
- Starting/stopping services
- Auto-restart on failure
- Running services at boot
- Logging via journald

**Check all running services:**
```bash
systemctl --no-pager --state=running | grep -E 'nginx|fabritius'
```

#### 7. Configure Nginx

**Add Fabritius-NG to your existing nginx configuration:**

Note: You need **root privileges** to modify `/etc/nginx/` files.

```bash
# As root, edit the hensor site config
nano /etc/nginx/sites-available/hensor
```

**Add a new location block** for Fabritius-NG (place it before the `location / { ... }` block):

```nginx
# Fabritius-NG app on /fabritius/
location /fabritius/ {
    proxy_pass http://127.0.0.1:1234;  # NO trailing slash! (preserves /fabritius prefix)
    proxy_http_version 1.1;

    # Headers
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # WebSocket support (required for NiceGUI)
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";

    # Performance settings
    proxy_read_timeout 3600;
    proxy_send_timeout 3600;
    proxy_buffering off;
    
    # Fix for "Message too long" WebSocket error
    client_max_body_size 100M;
    proxy_request_buffering off;
}

# NiceGUI static assets (REQUIRED - NiceGUI uses absolute URLs) (HTTP requests ~ shorter config)
location /_nicegui/ {
    proxy_pass http://127.0.0.1:1234/_nicegui/;  # Same port as above
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# NiceGUI WebSocket endpoint (REQUIRED for real-time communication) (websocket ~ longer config)
location /_nicegui_ws/ {
    proxy_pass http://127.0.0.1:1234/_nicegui_ws/;  # Same port as above
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # WebSocket upgrade headers
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    
    # Timeouts
    proxy_read_timeout 3600;
    proxy_send_timeout 3600;
}
```

**Important:** Place this block **before** the `location / { ... }` block in your config. Specific paths must come first!

**After editing the hensor file, follow these steps:**

```bash
# 1. Save and close nano (Ctrl+O, Enter, Ctrl+X)

# 2. Test configuration for syntax errors (CRITICAL - prevents breaking nginx!)
nginx -t

# Expected output:
# nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
# nginx: configuration file /etc/nginx/nginx.conf test is successful

# 3. If test FAILS, fix the errors before proceeding => fix hensor config file and test agina

# 4. Only if test passes, reload nginx (applies new config without downtime)
systemctl reload nginx

# 5. Verify nginx is still running
systemctl status nginx --no-pager

# Expected: Active: active (running)

# 6. If not: Check nginx error logs if something's wrong
tail -n 20 /var/log/nginx/error.log
```

**Access your app:**

Your app is now available at: `http://hensor.ilabt.imec.be/fabritius/`

**Nginx configuration structure:**

```
/etc/nginx/
├── sites-available/
│   └── hensor              # Main config file (you edited this)
└── sites-enabled/
    └── hensor -> ../sites-available/hensor  # Symlink (already exists)
```

**View current config:**
```bash
cat /etc/nginx/sites-available/hensor
```

**Example nginx config** (adjust to your setup):
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8003;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```
**⚠️ CRITICAL: Understanding proxy_pass trailing slash**

The trailing slash in `proxy_pass` determines how nginx handles URL rewriting:

**Without trailing slash (preserves path prefix):**
```nginx
location /fabritius/ {
    proxy_pass http://127.0.0.1:1234;  # NO trailing slash!
}
```
- Browser request: `/fabritius/search`
- Forwarded to app: `/fabritius/search` ✅ (prefix preserved)
- **Use this when:** Your app expects routes WITH the base path (our case!)

**With trailing slash (strips path prefix):**
```nginx
location /fabritius/ {
    proxy_pass http://127.0.0.1:1234/;  # Trailing slash!
}
```
- Browser request: `/fabritius/search`
- Forwarded to app: `/search` (strips `/fabritius`)
- **Use this when:** Your app doesn't know about the base path

**For absolute paths (like NiceGUI assets), always use trailing slash:**
```nginx
location /_nicegui/ {
    proxy_pass http://127.0.0.1:1234/_nicegui/;  # Both have trailing slash
}
```
- Browser request: `/_nicegui/static/file.js`
- Forwarded to app: `/_nicegui/static/file.js` (direct match)

**Summary for Fabritius-NG:**
- `/fabritius/` → NO trailing slash (app uses FABRITIUS_BASE_PATH)
- `/_nicegui/` → YES trailing slash (absolute path from NiceGUI)
- `/_nicegui_ws/` → YES trailing slash (absolute WebSocket endpoint)

**If the app doesn't work after nginx setup, check:**
1. **Static assets failing?** (CSS/JS not loading)
   - NiceGUI might be generating absolute URLs like `/static/...` instead of `/fabritius/static/...`
   - Solution: Configure NiceGUI with a base path (check NiceGUI docs) or use different nginx config

2. **Redirects going to wrong URL?** (app redirects to `hensor.ilabt.imec.be/search` instead of `.../fabritius/search`)
   - App doesn't know it's behind a proxy
   - Check NiceGUI configuration for proxy/base_path settings

3. **WebSocket connection failing?**
   - Check browser console for WebSocket errors
   - Verify the WebSocket headers are present in nginx config

4. **404 errors?**
   - Verify the app is running: `systemctl status fabritius-ng`
   - Check the port matches: `ss -tulpn | grep 1234`
   - Test direct access: `curl http://127.0.0.1:1234` (should return HTML)


## Updates

When deploying code updates from git:

### Step-by-step update workflow:

**1. Push your local changes to GitHub:**
```bash
# On your local machine (Windows)
git add .
git commit -m "Your update description"
git push origin main
```

**2. SSH to server:**
```bash
ssh root@hensor.privatedmz
```

**3. Pull latest code (as root - has SSH key):**
```bash
# Navigate to app directory
cd /opt/Fabritius-NG

# If first time pulling as root, add safe directory exception
# (only needed once due to ownership by fabritius-ng-user)
git config --global --add safe.directory /opt/Fabritius-NG

# Pull updates
git pull origin main
```

**4. Check if dependencies changed:**
```bash
# If requirements.txt was updated, install new packages
su - fabritius-ng-user
cd /opt/Fabritius-NG
source venv/bin/activate
pip install -r requirements.txt
exit  # Back to root
```

**5. Update .env if needed:**
```bash
# If new environment variables were added
nano /opt/Fabritius-NG/.env
# Add/update variables, save and exit
# WARNING: server host is 0.0.0.0 not 127.0.0.1 (localhost laptop)
# WARNING: FABRITIUS_BASE_PATH must be set! (uncomment
```

**6. Restart the service:**
```bash
systemctl restart fabritius-ng
```

**7. Verify everything works:**
```bash
# Check service status
systemctl status fabritius-ng --no-pager

# Check port is listening
ss -tulpn | grep 1234  # Replace with your port

# View recent logs
journalctl -u fabritius-ng -n 30 --no-pager
# Or
tail -f /var/log/fabritius-ng-error.log

# Test in browser
# Open: http://hensor.ilabt.imec.be/fabritius/
```

**Quick update (if only Python code changed, no dependencies):**
```bash
# SSH as root
ssh root@hensor.privatedmz

# Pull and restart (root has SSH key)
cd /opt/Fabritius-NG && git pull origin main && systemctl restart fabritius-ng && systemctl status fabritius-ng --no-pager
```

### Common update scenarios:

**New Python packages added:**
```bash
su - fabritius-ng-user
cd /opt/Fabritius-NG
source venv/bin/activate
pip install -r requirements.txt
exit
systemctl restart fabritius-ng
```

**New environment variables:**
```bash
nano /opt/Fabritius-NG/.env  # Add FABRITIUS_NEW_VAR="value"
systemctl restart fabritius-ng
```

**Nginx config changed:**
```bash
nano /etc/nginx/sites-available/hensor
nginx -t  # Test syntax
systemctl reload nginx  # Apply changes
```

**Database schema changed:**
```bash
# Run any migration scripts first, then restart
systemctl restart fabritius-ng
```

## Troubleshooting

**Is the app running?**

If you've completed step 6 (systemd service), your app runs automatically in the background. **You don't need to do anything** - it keeps running even after you logout or reboot.

**Always check service status first:**
```bash
# As root - this should be your first check when troubleshooting
systemctl status fabritius-ng --no-pager

# Check if port is listening
ss -tulpn | grep 1234  # Replace with your port

# View logs - Option 1: Via systemd journal
journalctl -u fabritius-ng -n 50 --no-pager  # Last 50 lines
journalctl -u fabritius-ng -f                # Follow in real-time

# View logs - Option 2: Direct file access
cat /var/log/fabritius-ng.log               # Stdout logs
cat /var/log/fabritius-ng-error.log         # Stderr logs
tail -f /var/log/fabritius-ng.log           # Follow in real-time
```

Expected output when running correctly:
- Status: `Active: active (running)`
- Port listening on your configured FABRITIUS_PORT

**Reconnecting to the server (new bash session):**

You only need to reactivate the venv for **manual operations** (not for the running service):

```bash
# SSH to server
ssh root@hensor.privatedmz

# Switch to app user
su - fabritius-ng-user

# Navigate to app directory
cd /opt/Fabritius-NG

# Reactivate venv (required for every new session!)
source venv/bin/activate

# Now you can run manual commands
python Fabritius-NG.py
# or
pip install <package>
```

**Note:** The systemd service automatically uses the venv path, so the app keeps running even when you logout. You only need to reactivate the venv for manual operations like testing or installing packages.

**Common issues:**

```bash
# Check if running
ps aux | grep Fabritius-NG.py

# Check port
sudo lsof -i :1234

# Test manually
source venv/bin/activate
python Fabritius-NG.py
```

## Security

- Set `.env` permissions: `chmod 600 .env`
- Never commit `.env` to git
- Use production-specific API keys
