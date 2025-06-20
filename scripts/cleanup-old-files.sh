#!/bin/bash
# Cleanup script for Meme Maker
# Removes old video files to prevent disk space issues

set -e

CLIPS_DIR="/opt/meme-maker/storage"
LOG_FILE="/var/log/meme-maker-cleanup.log"

echo "🧹 Starting cleanup at $(date)" | tee -a "$LOG_FILE"

# Check if storage directory exists
if [ ! -d "$CLIPS_DIR" ]; then
    echo "⚠️  Storage directory $CLIPS_DIR does not exist" | tee -a "$LOG_FILE"
    exit 1
fi

# Count files before cleanup
BEFORE_COUNT=$(find "$CLIPS_DIR" -name "*.mp4" -type f | wc -l)
echo "📊 Found $BEFORE_COUNT video files before cleanup" | tee -a "$LOG_FILE"

# Remove files older than 24 hours
echo "🗑️  Removing files older than 24 hours..." | tee -a "$LOG_FILE"
find "$CLIPS_DIR" -name "*.mp4" -type f -mtime +1 -delete

# Remove empty directories
echo "📁 Removing empty directories..." | tee -a "$LOG_FILE"
find "$CLIPS_DIR" -type d -empty -delete 2>/dev/null || true

# Count files after cleanup
AFTER_COUNT=$(find "$CLIPS_DIR" -name "*.mp4" -type f | wc -l)
REMOVED_COUNT=$((BEFORE_COUNT - AFTER_COUNT))

echo "✅ Cleanup completed: Removed $REMOVED_COUNT files, $AFTER_COUNT files remaining" | tee -a "$LOG_FILE"

# Check disk usage
DISK_USAGE=$(df "$CLIPS_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
echo "💾 Storage usage: ${DISK_USAGE}%" | tee -a "$LOG_FILE"

if [ "$DISK_USAGE" -gt 80 ]; then
    echo "⚠️  Warning: Storage usage is ${DISK_USAGE}% - consider more aggressive cleanup" | tee -a "$LOG_FILE"
fi

echo "🧹 Cleanup completed at $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE" 