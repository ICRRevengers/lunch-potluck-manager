#!/usr/bin/env python3
"""
Ứng Dụng Quản Lý Món Ăn Bữa Trưa Công Ty (Lunch Potluck Manager)
- Zero-dependency: Chạy trực tiếp bằng Python 3 standard library
- Lưu trữ SQLite tự động
- API REST đầy đủ + Phục vụ giao diện Web trực tiếp
"""

import http.server
import json
import os
import re
import socket
import sqlite3
import sys
import unicodedata
from urllib.parse import parse_qs, urlparse

PORT = 8080
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "potluck.db")
STATIC_DIR = os.path.dirname(os.path.abspath(__file__))


def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS dishes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            dish_name TEXT NOT NULL,
            category TEXT NOT NULL,
            servings INTEGER DEFAULT 4,
            note TEXT,
            lunch_date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Thêm dữ liệu mẫu cho ngày 20/10/2026 nếu chưa có
    cursor.execute("SELECT COUNT(*) FROM dishes WHERE lunch_date = '2026-10-20'")
    count = cursor.fetchone()[0]
    if count == 0:
        sample_dishes = [
            (
                "Anh Tuấn",
                "Thịt ba chỉ kho trứng cút",
                "man",
                5,
                "Kho đậm đà, có kèm ớt cay riêng",
                "2026-10-20",
            ),
            (
                "Chị Mai",
                "Canh chua cá lóc Nam Bộ",
                "canh",
                6,
                "Có bạc hà, giá, đậu bắp",
                "2026-10-20",
            ),
            (
                "Hoàng Nam",
                "Rau muống luộc + Nước mắm tỏi ớt",
                "rau",
                6,
                "Lấy cả nước canh dầm sấu thanh mát",
                "2026-10-20",
            ),
            (
                "Khánh Linh",
                "Dưa hấu & Hoa quả tráng miệng",
                "trang_mieng",
                8,
                "Đã gọt sẵn bỏ hộp lạnh",
                "2026-10-20",
            ),
            (
                "Đức Anh",
                "Cơm trắng dẻo thơm (nồi cơm điện)",
                "tinh_bot",
                10,
                "Cắm tại pantry lúc 11h30",
                "2026-10-20",
            ),
        ]
        cursor.executemany(
            """
            INSERT INTO dishes (user_name, dish_name, category, servings, note, lunch_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            sample_dishes,
        )
    conn.commit()
    conn.close()


def remove_vietnamese_tones(text):
    if not text:
        return ""
    text = unicodedata.normalize("NFD", text)
    text = re.sub(r"[\u0300-\u036f]", "", text)
    text = text.replace("đ", "d").replace("Đ", "D")
    return text.lower().strip()


def check_dish_duplicate(new_dish, target_date, exclude_id=None):
    """Kiểm tra xem món ăn mới có bị trùng hoặc tương đồng với món đã đăng ký trong ngày hay không."""
    conn = get_db()
    cursor = conn.cursor()
    query = (
        "SELECT id, user_name, dish_name, category FROM dishes WHERE lunch_date = ?"
    )
    params = [target_date]
    if exclude_id:
        query += " AND id != ?"
        params.append(exclude_id)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    norm_new = remove_vietnamese_tones(new_dish)
    words_new = set(re.findall(r"\w+", norm_new))
    stopwords = {"mon", "cac", "va", "cung", "co", "kem", "voi", "nau"}
    sig_words_new = words_new - stopwords

    exact_matches = []
    similar_matches = []

    for row in rows:
        reg_dish = row["dish_name"]
        norm_reg = remove_vietnamese_tones(reg_dish)
        words_reg = set(re.findall(r"\w+", norm_reg))
        sig_words_reg = words_reg - stopwords

        # 1. Trùng tuyệt đối (sau khi bỏ dấu, khoảng trắng)
        if norm_new == norm_reg:
            exact_matches.append(
                {
                    "id": row["id"],
                    "user_name": row["user_name"],
                    "dish_name": row["dish_name"],
                    "match_type": "exact",
                }
            )
            continue

        # 2. Kiểm tra từ khóa chính trùng lặp (ví dụ: 'thit kho', 'canh chua', 'ga ran')
        overlap = sig_words_new.intersection(sig_words_reg)
        if len(overlap) >= 2 or (
            len(overlap) == 1
            and any(len(w) >= 4 for w in overlap)
            and (norm_new in norm_reg or norm_reg in norm_new)
        ):
            similar_matches.append(
                {
                    "id": row["id"],
                    "user_name": row["user_name"],
                    "dish_name": row["dish_name"],
                    "overlap": list(overlap),
                    "match_type": "similar_keyword",
                }
            )
        elif norm_new in norm_reg or norm_reg in norm_new:
            similar_matches.append(
                {
                    "id": row["id"],
                    "user_name": row["user_name"],
                    "dish_name": row["dish_name"],
                    "match_type": "substring",
                }
            )

    return {
        "has_exact": len(exact_matches) > 0,
        "exact_matches": exact_matches,
        "has_similar": len(similar_matches) > 0,
        "similar_matches": similar_matches,
    }


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class PotluckHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS"
        )
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS"
        )
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == "/api/dishes":
            date = params.get("date", [None])[0]
            conn = get_db()
            cursor = conn.cursor()
            if date:
                cursor.execute(
                    "SELECT * FROM dishes WHERE lunch_date = ? ORDER BY id DESC",
                    (date,),
                )
            else:
                cursor.execute("SELECT * FROM dishes ORDER BY id DESC")
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            self._send_json({"success": True, "data": rows})
            return

        elif path == "/api/check-duplicate":
            dish = params.get("dish", [""])[0]
            date = params.get("date", [""])[0]
            exclude_id = params.get("exclude_id", [None])[0]
            if not dish or not date:
                self._send_json(
                    {"success": False, "error": "Thiếu dish hoặc date"}, 400
                )
                return
            result = check_dish_duplicate(dish, date, exclude_id)
            self._send_json({"success": True, "result": result})
            return

        elif path == "/api/summary":
            date = params.get("date", [""])[0]
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT category, COUNT(*) as count, SUM(servings) as total_servings
                FROM dishes
                WHERE lunch_date = ?
                GROUP BY category
            """,
                (date,),
            )
            rows = [dict(r) for r in cursor.fetchall()]
            cursor.execute(
                "SELECT COUNT(DISTINCT user_name) FROM dishes WHERE lunch_date = ?",
                (date,),
            )
            total_members = cursor.fetchone()[0]
            conn.close()
            self._send_json(
                {
                    "success": True,
                    "categories": rows,
                    "total_members": total_members,
                }
            )
            return

        # Phục vụ file tĩnh thông thường (index.html, v.v.)
        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/dishes":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            try:
                data = json.loads(body)
            except Exception:
                self._send_json({"success": False, "error": "JSON không hợp lệ"}, 400)
                return

            user_name = data.get("user_name", "").strip()
            dish_name = data.get("dish_name", "").strip()
            category = data.get("category", "khac").strip()
            servings = int(data.get("servings", 4))
            note = data.get("note", "").strip()
            lunch_date = data.get("lunch_date", "").strip()

            if not user_name or not dish_name or not lunch_date:
                self._send_json(
                    {
                        "success": False,
                        "error": "Vui lòng nhập tên người đăng ký, tên món ăn và ngày!",
                    },
                    400,
                )
                return

            import datetime
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            expire_utc = datetime.datetime(2026, 10, 20, 16, 59, 59, tzinfo=datetime.timezone.utc)
            if now_utc > expire_utc:
                self._send_json({
                    "success": False,
                    "error": "Thời hạn đăng ký 20/10 Lunch Prepare đã kết thúc lúc 23:59 ngày 20/10/2026!"
                }, 403)
                return

            # Kiểm tra trùng lặp trước khi lưu
            dup_check = check_dish_duplicate(dish_name, lunch_date)
            # Nếu người dùng không bắt buộc ghi đè mà bị trùng tuyệt đối
            force = data.get("force", False)
            if dup_check["has_exact"] and not force:
                names = ", ".join(
                    [
                        f"{m['dish_name']} (của {m['user_name']})"
                        for m in dup_check["exact_matches"]
                    ]
                )
                self._send_json(
                    {
                        "success": False,
                        "duplicate": True,
                        "error": f"Món ăn đã được đăng ký: {names}. Bạn có thể chọn món khác để bữa trưa phong phú hơn!",
                        "matches": dup_check["exact_matches"],
                    },
                    409,
                )
                return

            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO dishes (user_name, dish_name, category, servings, note, lunch_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (user_name, dish_name, category, servings, note, lunch_date),
            )
            new_id = cursor.lastrowid
            conn.commit()

            cursor.execute("SELECT * FROM dishes WHERE id = ?", (new_id,))
            created_row = dict(cursor.fetchone())
            conn.close()

            self._send_json(
                {"success": True, "data": created_row, "warnings": dup_check}, 201
            )
            return

        self._send_json({"success": False, "error": "Endpoint không tồn tại"}, 404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        match = re.match(r"^/api/dishes/(\d+)$", parsed.path)
        if match:
            dish_id = int(match.group(1))
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM dishes WHERE id = ?", (dish_id,))
            conn.commit()
            conn.close()
            self._send_json(
                {"success": True, "message": f"Đã xóa món ăn ID {dish_id}"}
            )
            return
        self._send_json({"success": False, "error": "Endpoint không tồn tại"}, 404)


def main():
    init_db()
    local_ip = get_local_ip()
    server = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), PotluckHandler)
    print("=" * 60)
    print("💐 20/10 LUNCH PREPARE - HỆ THỐNG QUẢN LÝ BỮA TRƯA VĂN PHÒNG")
    print("=" * 60)
    print(f"👉 Máy bạn truy cập:         http://localhost:{PORT}")
    print(f"👉 Anh em cùng mạng Wi-Fi:   http://{local_ip}:{PORT}")
    print("=" * 60)
    print("Nhấn Ctrl+C để dừng server.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã dừng server.")
        server.server_close()


if __name__ == "__main__":
    main()
