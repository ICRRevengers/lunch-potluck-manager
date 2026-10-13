# 🍱 Ứng Dụng Quản Lý Món Ăn Bữa Trưa (Office Potluck Manager)

Hệ thống quản lý đăng ký món ăn tự nấu mang lên công ty cho anh em đồng nghiệp, tích hợp tính năng **kiểm tra trùng lặp món ăn thông minh theo thời gian thực**.

---

## 🌟 Các Tính Năng Nổi Bật

1. **Form Đăng Ký Trực Quan**:
   - Nhập tên người mang và tên món ăn.
   - Phân loại món ăn theo nhóm: *Món mặn / Đạm*, *Món canh / Súp*, *Rau / Salad*, *Cơm / Tinh bột*, *Tráng miệng / Đồ uống*.
   - Khẩu phần (số người ăn) và ghi chú riêng (cay, ăn nóng, chay...).
2. **Hệ Thống Kiểm Tra Trùng Lặp Thông Minh (Real-time Duplicate Checker)**:
   - 🔴 **Báo động đỏ (Trùng hoàn toàn)**: Khi tên món gõ vào trùng khớp tuyệt đối (kể cả không dấu hay có dấu: VD *"Thịt kho tàu"* vs *"thit kho tau"*). Nút đăng ký sẽ tự động khóa lại để nhắc người dùng đổi món, kèm tùy chọn mở khóa nếu cố ý mang thêm.
   - 🟡 **Báo động vàng (Trùng tương đối / Tương đồng từ khóa)**: Khi phát hiện các món có chung thành phần cốt lõi (VD: một người đã đăng ký *"Thịt ba chỉ kho trứng"*, người tiếp theo gõ *"Thịt kho tàu"* hoặc *"Canh chua cá"* vs *"Canh chua tôm"*). Hệ thống sẽ nhắc nhở để cân nhắc đa dạng hóa thực đơn.
   - 🟢 **Báo động xanh (Món mới)**: Món độc đáo chưa ai mang trong ngày.
3. **Bảng Theo Dõi Cân Bằng Dinh Dưỡng**:
   - Thống kê trực tiếp số lượng món theo từng loại (Mặn, Canh, Rau, Tinh bột, Tráng miệng).
   - Tự động gợi ý nếu mâm cơm đang thiếu món canh, thiếu rau hoặc chưa có ai cắm cơm.
4. **Tiện Ích Cho Văn Phòng**:
   - 📋 **1-Click Sao chép Thực đơn**: Tự động format văn bản đẹp mắt để gửi ngay vào group chat Zalo / Slack / Telegram của công ty.
   - 📥 **Xuất file Excel / CSV**: Lưu trữ hoặc in danh sách phân công.
   - 🔍 **Tìm kiếm & Lọc nhanh**: Lọc theo phân loại món hoặc tìm theo tên người mang.
5. **Chế Độ Hoạt Động Kép (Dual-mode)**:
   - **Mạng nội bộ văn phòng (LAN / Wi-Fi)**: Chạy qua `server.py` (Python 3 tích hợp sẵn SQLite), tất cả anh em mở điện thoại hoặc laptop truy cập vào cùng 1 địa chỉ IP là thấy dữ liệu của nhau ngay lập tức.
   - **Chạy trực tiếp (Offline / LocalStorage)**: Nhấp đúp mở trực tiếp file `index.html` trên trình duyệt mà không cần cài thêm bất cứ phần mềm nào.

---

## 🚀 Hướng Dẫn Sử Dụng

### Cách 1: Chạy Server để cả văn phòng cùng truy cập qua Wi-Fi (Khuyên Dùng)

Mở Terminal và chạy lệnh:

```bash
cd /home/phu/workspace/repo/lunch-potluck-manager
python3 server.py
```

Server sẽ hiển thị:
- **Địa chỉ máy bạn**: `http://localhost:8080`
- **Địa chỉ cho anh em cùng mạng Wi-Fi**: `http://192.168.x.x:8080` (gửi link này vào nhóm chat là mọi người đều vào đăng ký được ngay trên điện thoại hoặc máy tính).

### Cách 2: Mở trực tiếp trên trình duyệt (Chế độ Local)

Mở file `index.html` trực tiếp bằng trình duyệt Chrome/Firefox/Edge. Dữ liệu sẽ được lưu an toàn trong `localStorage` của trình duyệt.

---

## 📂 Cấu Trúc Thư Mục

- [`index.html`](file:///home/phu/workspace/repo/lunch-potluck-manager/index.html): Giao diện người dùng web hoàn chỉnh.
- [`server.py`](file:///home/phu/workspace/repo/lunch-potluck-manager/server.py): Máy chủ Python 3 + SQLite không cần cài thêm thư viện phụ thuộc (`pip install`).
- [`potluck.db`](file:///home/phu/workspace/repo/lunch-potluck-manager/potluck.db): Cơ sở dữ liệu SQLite lưu danh sách món ăn (tự động tạo khi chạy).
