# TCP / UDP Connection Tester

[![Build Windows](https://github.com/xuanquangf5/TestTCP/actions/workflows/build-windows.yml/badge.svg)](https://github.com/xuanquangf5/TestTCP/actions/workflows/build-windows.yml)

App Python desktop dùng thư viện chuẩn: Tkinter, socket, threading. Python 3.9 trở lên.

## Chạy

```sh
python3 app.py
```

Mở thêm terminal và chạy lại lệnh để có cửa sổ độc lập khác.
Nếu Python báo thiếu `tkinter`, cài bản Python có hỗ trợ Tcl/Tk.

## Sử dụng

1. Cửa sổ server: nhập IP LAN của máy server (hoặc `127.0.0.1` khi thử cùng máy), TCP `8008`, UDP `8004`, nhấn **Start Server**.
2. Cửa sổ client: nhập cùng IP và port của server, nhấn **Start Client**.
3. TCP gửi ngay `Hello TCP 001`; một giây sau UDP gửi `Hello UDP 001`. Mỗi giao thức gửi mỗi hai giây, bộ đếm độc lập.
4. Server trả `Okie TCP 001` hoặc `Okie UDP 001` theo đúng số nhận. Log hiển thị gửi, nhận, lỗi và cảnh báo quá 5 giây chưa có phản hồi.
5. Nhấn nút **Stop** màu đỏ để dừng. Start lại sẽ đặt lại hai bộ đếm về `001`.

IP mặc định được lấy từ địa chỉ IPv4 của giao diện mạng dùng định tuyến; nếu không lấy được sẽ dùng `127.0.0.1`. Máy nhiều card mạng có thể cần sửa IP bằng tay. Server có thể bind `0.0.0.0` để nghe mọi giao diện; client phải dùng IP cụ thể của server.

Khi thử hai máy, cho phép TCP 8008 và UDP 8004 qua firewall của máy server. TCP phải kết nối thành công trước khi client bắt đầu gửi cả hai giao thức. UDP không có bắt tay kết nối; xem phản hồi để biết đường truyền hoạt động.

Mỗi cửa sổ chạy một vai trò. Nhiều client có thể dùng chung server. Hai server bind trùng IP/port sẽ báo lỗi. Khi một trong hai port server không mở được, app hủy cả phiên.

Thông điệp TCP mã hóa UTF-8 và kết thúc bằng `\n`; UDP dùng một datagram cho mỗi thông điệp. App giữ tối đa khoảng 5.000 dòng log. Nút bo góc được vẽ riêng để giữ nền giao diện gốc và màu xanh/đỏ trên macOS.

## Kiểm tra phần mạng

```sh
python3 -m unittest -v test_network.py
```

## Tải app Windows

Vào tab **Actions → Build Windows**, chọn lần chạy thành công mới nhất, tải artifact **TestTCP-Windows-x64** và giải nén. Mở `TestTCP.exe`; không cần cài Python. Mở file nhiều lần để có nhiều cửa sổ độc lập.

Workflow tự chạy khi push lên `main`, khi mở pull request hoặc khi chọn **Run workflow**. Workflow kiểm tra mạng, giao diện, đóng gói bằng PyInstaller rồi kiểm tra file exe có khởi động được. Artifact lưu trong 30 ngày.

Để tự build trên Windows:

```sh
python -m pip install -r requirements-build.txt
python -m PyInstaller --noconfirm --clean --onefile --windowed --name TestTCP app.py
```

File kết quả: `dist/TestTCP.exe` (Windows x64).
