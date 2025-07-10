# Server File Management Guide - Lightsail

This guide will help you access and manage video files stored on your Amazon Lightsail server. **No coding experience required** - just follow these steps exactly as written.

## 🎯 What This Guide Covers

1. **Viewing files** stored on your server
2. **Manually deleting files** to free up space  
3. **Checking disk usage** to monitor storage
4. **Emergency cleanup** when storage is full

---

## 📋 Prerequisites

Before starting, you'll need:
- Your **Lightsail server IP address** (e.g., `13.126.173.223`)
- Your **SSH private key file** (usually named `LightsailDefaultKey-ap-south-1.pem`)
- A computer with terminal/command prompt access

---

## 🔐 Step 1: Connect to Your Server

### On Windows:
1. Open **Command Prompt** or **PowerShell**
2. Navigate to where your key file is stored:
   ```bash
   cd C:\path\to\your\key\file
   ```
3. Connect to your server (replace `YOUR_IP` with your actual IP):
   ```bash
   ssh -i LightsailDefaultKey-ap-south-1.pem ubuntu@YOUR_IP
   ```

### On Mac/Linux:
1. Open **Terminal**
2. Navigate to where your key file is stored:
   ```bash
   cd /path/to/your/key/file
   ```
3. Make sure key has correct permissions:
   ```bash
   chmod 400 LightsailDefaultKey-ap-south-1.pem
   ```
4. Connect to your server:
   ```bash
   ssh -i LightsailDefaultKey-ap-south-1.pem ubuntu@YOUR_IP
   ```

**Success indicator:** You should see something like `ubuntu@ip-YOUR-IP:~$`

---

## 📁 Step 2: Navigate to Video Files Location

Once connected to your server, run these commands:

```bash
# Go to the main application directory
cd /opt/meme-maker

# Go to the video storage location
cd storage
```

**What you'll see:** The terminal prompt will change to show you're in the storage directory.

---

## 👀 Step 3: View All Stored Video Files

### See Today's Files
```bash
# List files created today (shows dates and sizes)
ls -la $(date +%Y-%m-%d)/
```

### See All Files by Date
```bash
# See all date directories
ls -la

# See files in a specific date (replace with actual date)
ls -la 2025-01-02/
```

### See All Files with Details
```bash
# See all files with size and date information
find . -name "*.mp4" -type f -exec ls -lh {} \; | sort
```

**What you'll see:**
- File names like `My_Video_Title_abc123def456.mp4`
- File sizes (e.g., `15M` = 15 megabytes)
- Creation dates and times

---

## 🗑️ Step 4: Manually Delete Specific Files

### Delete a Single File
```bash
# Delete a specific file (replace with actual filename and date)
rm 2025-01-02/My_Video_Title_abc123def456.mp4
```

### Delete All Files from a Specific Date
```bash
# Delete all files from a specific date (replace with actual date)
rm -rf 2025-01-02/
```

### Delete Files Older Than 24 Hours
```bash
# Safe automated cleanup (removes files older than 1 day)
find . -name "*.mp4" -type f -mtime +1 -delete

# Remove empty directories after cleanup
find . -type d -empty -delete
```

**⚠️ WARNING:** Deleted files cannot be recovered. Double-check file names before deleting.

---

## 💾 Step 5: Check Storage Usage

### Check Total Disk Usage
```bash
# See how much disk space is used vs available
df -h /opt/meme-maker/storage
```

### Check Video Files Size
```bash
# See total size of all video files
du -sh .
```

### Check Detailed Breakdown by Date
```bash
# See storage used by each date directory
du -sh */
```

**What you'll see:**
- Total disk usage percentage (e.g., `Use% 45%`)
- Available space (e.g., `Avail 30G`)
- Size breakdown by date (e.g., `2.1G 2025-01-02/`)

---

## 🚨 Step 6: Emergency Storage Cleanup

**Use this when disk usage is >80% or when you're running out of space:**

### Quick Safe Cleanup (Recommended)
```bash
# Go to storage directory
cd /opt/meme-maker/storage

# Delete files older than 12 hours (aggressive but safe)
find . -name "*.mp4" -type f -mtime +0.5 -delete

# Remove empty date directories
find . -type d -empty -delete

# Check how much space was freed
df -h /opt/meme-maker/storage
```

### Nuclear Option (Use Only in Emergencies)
```bash
# ⚠️ WARNING: This deletes ALL video files
# Only use if server is completely full and nothing else works

cd /opt/meme-maker/storage
rm -rf */
```

---

## 📊 Step 7: Monitor Storage Health

### Check Current Status
```bash
# Quick health check
cd /opt/meme-maker/storage
echo "=== STORAGE SUMMARY ==="
echo "Disk Usage: $(df -h . | tail -1 | awk '{print $5}')"
echo "Total Files: $(find . -name "*.mp4" | wc -l)"
echo "Total Size: $(du -sh . | cut -f1)"
echo "Oldest File: $(find . -name "*.mp4" -type f -printf '%T+ %p\n' | sort | head -1)"
echo "Newest File: $(find . -name "*.mp4" -type f -printf '%T+ %p\n' | sort | tail -1)"
```

### Set Up Automated Monitoring Alert
```bash
# Create a simple alert script (copy and paste this entire block)
cat > /home/ubuntu/check_storage.sh << 'EOF'
#!/bin/bash
USAGE=$(df /opt/meme-maker/storage | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $USAGE -gt 80 ]; then
    echo "WARNING: Storage usage is ${USAGE}% - cleanup needed!"
    echo "Run: cd /opt/meme-maker/storage && find . -name '*.mp4' -type f -mtime +1 -delete"
else
    echo "Storage OK: ${USAGE}% used"
fi
EOF

# Make it executable
chmod +x /home/ubuntu/check_storage.sh

# Run the check
/home/ubuntu/check_storage.sh
```

---

## 🔄 Step 8: Exit the Server

When you're done managing files:

```bash
# Exit the SSH connection
exit
```

**Success indicator:** You'll return to your local computer's command prompt.

---

## 📋 Quick Reference Commands

| Task | Command |
|------|---------|
| **Connect to server** | `ssh -i keyfile.pem ubuntu@YOUR_IP` |
| **Go to files** | `cd /opt/meme-maker/storage` |
| **List today's files** | `ls -la $(date +%Y-%m-%d)/` |
| **Check disk usage** | `df -h .` |
| **Delete old files** | `find . -name "*.mp4" -mtime +1 -delete` |
| **Check storage health** | `/home/ubuntu/check_storage.sh` |
| **Exit server** | `exit` |

---

## ⚠️ Important Safety Notes

1. **Always check disk usage before and after cleanup**
2. **Files are organized by date** - look in the correct date directory
3. **File names include job IDs** - they look like `Title_abc123def456.mp4`
4. **Deleted files cannot be recovered** - be careful with `rm` commands
5. **Don't delete system files** - only delete `.mp4` files in the storage directory
6. **Monitor storage regularly** - aim to keep usage below 80%

---

## 🆘 Troubleshooting

### Can't Connect to Server
- Check your IP address is correct
- Verify your key file name and location
- Ensure key file has correct permissions (400)

### No Files Found
- Files might be in a different date directory
- Check if files were already automatically cleaned up
- Verify you're in the correct directory: `/opt/meme-maker/storage`

### Permission Denied
- Make sure you're logged in as `ubuntu` user
- Use `sudo` before commands if needed: `sudo rm filename`

### Still Out of Space
- Run the nuclear cleanup option
- Consider upgrading server storage
- Check for other large files: `sudo du -sh /*`

---

## 📞 Need Help?

If you encounter issues not covered here:
1. Take a screenshot of the error message
2. Note which step you were on
3. Include the command you ran
4. Contact your technical support with this information

**Remember:** When in doubt, it's safer to ask for help than to delete the wrong files! 