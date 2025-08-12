#!/bin/bash

# Mac Disk Cleanup Script
# Run with: chmod +x cleanup.sh && ./cleanup.sh

echo "🧹 Starting Mac disk cleanup..."
echo "⚠️  This script will delete temporary files and caches. Press Ctrl+C to cancel."
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 1
fi

# Function to get folder size
get_size() {
    if [ -d "$1" ]; then
        du -sh "$1" 2>/dev/null | cut -f1
    else
        echo "0B"
    fi
}

# Function to safely remove directory contents
safe_remove() {
    if [ -d "$1" ]; then
        local size=$(get_size "$1")
        echo "Cleaning $1 ($size)..."
        rm -rf "$1"/* 2>/dev/null
        rm -rf "$1"/.* 2>/dev/null
    fi
}

echo "📊 Checking disk usage before cleanup..."
df -h /

echo ""
echo "🗂️  Cleaning system caches..."

# Clear user caches
safe_remove "$HOME/Library/Caches"

# Clear system logs (older than 7 days)
echo "Cleaning system logs..."
sudo log collect --last 7d --output /tmp/logs.logarchive 2>/dev/null
sudo rm -rf /var/log/*.log 2>/dev/null
sudo rm -rf /var/log/*/*.log 2>/dev/null

# Clear temporary files
echo "Cleaning temporary files..."
safe_remove "/tmp"
safe_remove "/var/tmp"
sudo rm -rf /private/tmp/* 2>/dev/null

# Clear Downloads folder (ask first)
if [ -d "$HOME/Downloads" ]; then
    downloads_size=$(get_size "$HOME/Downloads")
    echo "Downloads folder size: $downloads_size"
    read -p "Clear Downloads folder? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        safe_remove "$HOME/Downloads"
    fi
fi

# Clear Trash
echo "Emptying Trash..."
rm -rf "$HOME/.Trash"/* 2>/dev/null

# Clear browser caches
echo "Cleaning browser caches..."
safe_remove "$HOME/Library/Caches/com.apple.Safari"
safe_remove "$HOME/Library/Caches/Google/Chrome"
safe_remove "$HOME/Library/Caches/Mozilla"

# Clear Xcode caches (if exists)
if [ -d "$HOME/Library/Developer/Xcode" ]; then
    echo "Cleaning Xcode caches..."
    safe_remove "$HOME/Library/Developer/Xcode/DerivedData"
    safe_remove "$HOME/Library/Developer/Xcode/Archives"
fi

# Clear iOS device backups (ask first)
ios_backup_dir="$HOME/Library/Application Support/MobileSync/Backup"
if [ -d "$ios_backup_dir" ]; then
    backup_size=$(get_size "$ios_backup_dir")
    echo "iOS backup size: $backup_size"
    read -p "Clear old iOS device backups? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        safe_remove "$ios_backup_dir"
    fi
fi

# Clear application logs
echo "Cleaning application logs..."
safe_remove "$HOME/Library/Logs"

# Clear QuickLook thumbnails
echo "Cleaning QuickLook thumbnails..."
qlmanage -r cache 2>/dev/null

# Clear font caches
echo "Cleaning font caches..."
sudo atsutil databases -remove 2>/dev/null

# Purge inactive memory (requires sudo)
echo "Purging inactive memory..."
sudo purge 2>/dev/null

# Clear DNS cache
echo "Clearing DNS cache..."
sudo dscacheutil -flushcache 2>/dev/null

echo ""
echo "🎉 Cleanup complete!"
echo "📊 Checking disk usage after cleanup..."
df -h /

echo ""
echo "💡 Additional manual cleanup suggestions:"
echo "   • Check Applications folder for unused apps"
echo "   • Review large files: find ~ -size +1G -type f 2>/dev/null"
echo "   • Clean up Desktop and Documents folders"
echo "   • Empty iPhoto/Photos library trash"
echo "   • Check for large duplicate files"