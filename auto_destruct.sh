#!/bin/bash
# 20/10 Lunch Prepare - Auto-Destruct and Complete Cleanup Script
# Executes automatic shutdown of Cloudflare tunnel, Python server, GitHub Pages/Repo, local repo, master-control docs, and crontab

DIR="/home/phu/workspace/repo/lunch-potluck-manager"
MASTER_REPO="/home/phu/workspace/repo/master-control"
SCRATCH_LINK="/home/phu/.gemini/antigravity/scratch/lunch-potluck-manager"
BACKUP_DIR="/home/phu/workspace/backup"
LOG_DIR="/home/phu/workspace/logs"
mkdir -p "$BACKUP_DIR" "$LOG_DIR"
LOG_FILE="$LOG_DIR/lunch-potluck-destruct.log"

echo "==================================================" >> "$LOG_FILE"
echo "💥 [$(date -u '+%Y-%m-%d %H:%M:%S UTC')] Bắt đầu quy trình tự hủy toàn diện dịch vụ 20/10 Lunch Prepare" >> "$LOG_FILE"

# 1. Sao lưu dữ liệu SQLite lần cuối trước khi xóa
if [ -f "$DIR/potluck.db" ]; then
    FINAL_BACKUP="$BACKUP_DIR/potluck-final-$(date -u '+%Y%m%d_%H%M%S').db"
    cp -p "$DIR/potluck.db" "$FINAL_BACKUP" >> "$LOG_FILE" 2>&1 || true
    echo "1. Đã sao lưu dữ liệu cuối cùng vào: $FINAL_BACKUP" >> "$LOG_FILE"
fi

# 2. Ngắt kết nối Cloudflare Tunnel
echo "2. Dừng Cloudflare Tunnel..." >> "$LOG_FILE"
pkill -f "cloudflared.*8080" || pkill -f "cloudflared" || true

# 3. Dừng máy chủ Python
echo "3. Dừng máy chủ Python backend..." >> "$LOG_FILE"
pkill -f "python3.*server.py" || pkill -f "server.py" || true

# 4. Hủy GitHub Pages và xóa/ẩn repo trên GitHub
echo "4. Hủy GitHub Pages và đóng repo GitHub ICRRevengers/lunch-potluck-manager..." >> "$LOG_FILE"
if command -v gh > /dev/null 2>&1; then
    gh api -X DELETE repos/ICRRevengers/lunch-potluck-manager/pages >> "$LOG_FILE" 2>&1 || true
    if ! gh api -X DELETE repos/ICRRevengers/lunch-potluck-manager >> "$LOG_FILE" 2>&1; then
        echo "   -> Token không có scope delete_repo, chuyển repo sang Private + Archived..." >> "$LOG_FILE"
        gh api -X PATCH repos/ICRRevengers/lunch-potluck-manager -F private=true -F archived=true >> "$LOG_FILE" 2>&1 || true
    fi
fi

# 5. Xóa symlink tạm và xóa toàn bộ thư mục repo local
echo "5. Xóa symlink và thư mục repo local $DIR..." >> "$LOG_FILE"
rm -f "$SCRATCH_LINK"
rm -rf "$DIR"

# 6. Gỡ thông tin dịch vụ khỏi repo master-control và push lên GitHub
echo "6. Dọn thông tin lunch-potluck-manager trong repo master-control..." >> "$LOG_FILE"
if [ -d "$MASTER_REPO/.git" ]; then
    rm -f "$MASTER_REPO/docs/services/lunch-potluck-manager.md"
    rmdir "$MASTER_REPO/docs/services" 2>/dev/null || true
    rmdir "$MASTER_REPO/docs" 2>/dev/null || true

    python3 - "$MASTER_REPO/SERVICES.md" << 'PYEOF' >> "$LOG_FILE" 2>&1 || true
import sys, re

path = sys.argv[1]
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Xóa dòng trong bảng tra nhanh
content = re.sub(r"^\| `david-worcester-herbal-steal\.trycloudflare\.com` \|.*?\n", "", content, flags=re.MULTILINE)

# Xóa mục chi tiết dịch vụ 20/10 Lunch Prepare
content = re.sub(
    r"\n### 20/10 Lunch Prepare \(Office Potluck Manager\)\n(?:- .*\n)+",
    "\n",
    content,
)

# Khôi phục ghi chú cron
content = content.replace(
    "Không có Docker, PM2. Crontab của user `phu` hiện có lịch tự hủy dịch vụ `lunch-potluck-manager` vào ngày `20/10/2026`.",
    "Không có Docker, PM2, cron của user.",
)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
PYEOF

    git -C "$MASTER_REPO" pull --ff-only origin main >> "$LOG_FILE" 2>&1 || true
    git -C "$MASTER_REPO" add -A >> "$LOG_FILE" 2>&1 || true
    git -C "$MASTER_REPO" commit -m "chore: remove retired lunch-potluck-manager service from docs and registry" >> "$LOG_FILE" 2>&1 || true
    git -C "$MASTER_REPO" push origin main >> "$LOG_FILE" 2>&1 || true
fi

# 7. Tự gỡ lịch tự hủy khỏi crontab
echo "7. Dọn dẹp lịch tự hủy khỏi crontab..." >> "$LOG_FILE"
(crontab -l 2>/dev/null | grep -v "lunch-potluck-manager" | grep -v "20/10 Lunch Prepare Auto-destruct" | grep -v "Fallback: 23:59 UTC on 20/10/2026") | crontab - || true

echo "✅ Đã hủy toàn bộ tiến trình, đóng link, xóa repo, cập nhật master-control và dọn crontab thành công lúc $(date -u '+%Y-%m-%d %H:%M:%S UTC')!" >> "$LOG_FILE"
