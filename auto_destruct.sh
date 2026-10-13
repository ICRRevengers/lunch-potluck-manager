#!/bin/bash
# 20/10 Lunch Prepare - Auto-Destruct and Shutdown Script
# Executes automatic shutdown of Cloudflare tunnel, Python server, and GitHub Pages

DIR="/home/phu/workspace/repo/lunch-potluck-manager"
LOG_FILE="$DIR/destruct.log"

echo "==================================================" >> "$LOG_FILE"
echo "💥 [$(date -u '+%Y-%m-%d %H:%M:%S UTC')] Bắt đầu quy trình tự hủy dịch vụ 20/10 Lunch Prepare" >> "$LOG_FILE"

# 1. Ngắt kết nối Cloudflare Tunnel
echo "1. Dừng Cloudflare Tunnel..." >> "$LOG_FILE"
pkill -f "cloudflared" || true

# 2. Dừng máy chủ Python
echo "2. Dừng máy chủ Python backend..." >> "$LOG_FILE"
pkill -f "server.py" || true

# 3. Hủy bỏ dịch vụ GitHub Pages qua GitHub API
echo "3. Hủy kích hoạt GitHub Pages..." >> "$LOG_FILE"
if command -v gh > /dev/null 2>&1; then
    gh api -X DELETE repos/ICRRevengers/lunch-potluck-manager/pages >> "$LOG_FILE" 2>&1 || true
fi

# 4. Dọn dẹp file URL tạm thời
rm -f "$DIR/current_url.txt" "$DIR/tunnel.log"

echo "✅ Đã hủy toàn bộ dịch vụ và đóng link thành công lúc $(date -u '+%Y-%m-%d %H:%M:%S UTC')!" >> "$LOG_FILE"
