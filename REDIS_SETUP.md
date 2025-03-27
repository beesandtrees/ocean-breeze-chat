# Redis Setup Guide for Ocean Chat on AWS Lightsail

This guide explains how to set up Redis for the Ocean Chat application on an AWS Lightsail instance.

## Installing Redis on AWS Lightsail

### 1. Connect to Your Lightsail Instance

```bash
ssh -i your-lightsail-key.pem username@your-instance-ip
```

### 2. Update Package Lists

```bash
sudo apt update
```

### 3. Install Redis

```bash
sudo apt install redis-server -y
```

### 4. Configure Redis

Edit the Redis configuration file:

```bash
sudo nano /etc/redis/redis.conf
```

Make the following changes:

1. Set a password (find the `# requirepass foobared` line, uncomment it, and change "foobared" to your secure password):
   ```
   requirepass your_secure_password
   ```

2. By default, Redis only listens on localhost. If you're using Redis on the same server as your application, this is secure. Otherwise, to allow connections from other sources, find the line `bind 127.0.0.1 ::1` and modify it:
   ```
   bind 0.0.0.0
   ```
   
   > **IMPORTANT**: If you bind to 0.0.0.0, make sure to set a strong password and configure security groups properly.

3. Enable AOF persistence for better durability (find the `appendonly no` line and change it to):
   ```
   appendonly yes
   ```

Save and exit the editor (Ctrl+O, Enter, Ctrl+X in nano).

### 5. Configure Lightsail Firewall

If you need to access Redis from outside the Lightsail instance:

1. Go to the AWS Lightsail console
2. Select your instance
3. Go to the "Networking" tab
4. Add a custom firewall rule for TCP port 6379 (Redis)
   - For security, limit access to specific IP addresses if possible

### 6. Restart Redis to Apply Changes

```bash
sudo systemctl restart redis-server
```

### 7. Enable Redis to Start on Boot

```bash
sudo systemctl enable redis-server
```

### 8. Verify Installation

Check if Redis is running:

```bash
sudo systemctl status redis-server
```

Test Redis with the command-line interface:

```bash
redis-cli
```

Once in the Redis CLI, authenticate and test connectivity:

```
auth your_secure_password
ping
```

You should receive "PONG" as the response.

## Configuration for Ocean Chat

Update the application's environment variables in your deployment:

```bash
# Add these to your .env file
REDIS_HOST=localhost  # use localhost if Redis is on the same instance
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_secure_password  # must match the password in redis.conf
```

## Data Migration

To migrate existing JSON data to Redis, use the included migration script:

```bash
python migrate_json_to_redis.py
```

## Monitoring Redis

Monitor Redis memory usage and performance:

```bash
# Connect to Redis CLI
redis-cli -a your_secure_password

# Get server info
INFO

# Monitor memory usage
INFO memory

# List largest keys (be careful on production servers)
redis-cli --bigkeys -a your_secure_password
```

## Backup and Restore

### Setting Up Automatic Backups

Create a backup script:

```bash
sudo nano /usr/local/bin/redis-backup.sh
```

Add the following content:

```bash
#!/bin/bash
BACKUP_DIR="/path/to/backup/directory"
DATETIME=$(date +%Y%m%d_%H%M%S)
REDIS_PASSWORD="your_secure_password"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Create Redis backup
redis-cli -a $REDIS_PASSWORD --rdb $BACKUP_DIR/redis_backup_$DATETIME.rdb

# Keep only the last 7 backups
ls -1t $BACKUP_DIR/redis_backup_*.rdb | tail -n +8 | xargs -r rm
```

Make the script executable:

```bash
sudo chmod +x /usr/local/bin/redis-backup.sh
```

Set up a daily cron job:

```bash
sudo crontab -e
```

Add this line to run the backup daily at 2 AM:

```
0 2 * * * /usr/local/bin/redis-backup.sh
```

### Restoring from Backup

To restore from a backup file:

```bash
# Stop Redis
sudo systemctl stop redis-server

# Copy the RDB file to Redis data directory
sudo cp /path/to/backup/redis_backup_TIMESTAMP.rdb /var/lib/redis/dump.rdb

# Set proper ownership
sudo chown redis:redis /var/lib/redis/dump.rdb

# Restart Redis
sudo systemctl start redis-server
```

## Security Considerations

1. **Network Security**:
   - Only expose Redis to the internet if absolutely necessary
   - Use Lightsail firewall rules to restrict access to trusted IP addresses

2. **Authentication**:
   - Use a strong password in the Redis configuration
   - Rotate the password periodically

3. **Regular Updates**:
   - Keep your system and Redis up to date:
     ```bash
     sudo apt update && sudo apt upgrade -y
     ```

## Troubleshooting

### Common Issues

1. **Connection refused**:
   - Check if Redis is running: `sudo systemctl status redis-server`
   - Verify firewall settings in AWS Lightsail console
   - Check Redis configuration for binding issues

2. **Authentication failure**:
   - Verify the password in your environment variables matches redis.conf
   - Check Redis logs: `sudo journalctl -u redis-server`

3. **Memory issues**:
   - Monitor memory usage: `redis-cli -a your_password INFO memory`
   - Consider implementing key expiration policies
   - Adjust the `maxmemory` setting in redis.conf if needed