# TCP / UDP Connection Tester

[![Build and Release](https://github.com/xuanquangf5/TestTCP/actions/workflows/build.yml/badge.svg)](https://github.com/xuanquangf5/TestTCP/actions/workflows/build.yml)

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

## Tải app cho Windows, macOS và Linux

Tải tại [GitHub Releases](https://github.com/xuanquangf5/TestTCP/releases/latest). Mỗi Release có 6 bản, không cần cài Python:

| Bản | Định dạng | Yêu cầu |
| --- | --- | --- |
| Windows x86 | `.zip` chứa `.exe` 32-bit | Windows 10 trở lên, x86/x64 |
| Windows x64 | `.zip` chứa `.exe` 64-bit | Windows 10 trở lên, x64 |
| macOS Intel | `.zip` chứa `.app` | macOS 15 trở lên, Intel |
| macOS Apple Silicon | `.zip` chứa `.app` | macOS 15 trở lên, ARM64 |
| Linux x64 | `.tar.gz` chứa executable | Desktop Linux x86-64, glibc 2.35+ |
| Linux ARM64 | `.tar.gz` chứa executable | Desktop Linux ARM64, glibc 2.35+ |

Giải nén và mở app. Linux chạy `./TestTCP`; file tar giữ quyền thực thi. Trên Mac dùng `open -n TestTCP.app` để mở thêm cửa sổ độc lập. Linux yêu cầu môi trường desktop/X11 hoặc XWayland, không dành cho server chỉ có terminal. Windows ARM chưa có bản native riêng.

Bản macOS chưa ký Developer ID/notarize, nên có thể cần cho phép mở trong **System Settings → Privacy & Security**. Windows có thể hiện SmartScreen do app chưa ký.

## Build và phát hành

Workflow **Build and Release** chạy khi push `main`, push tag `v*`, mở PR hoặc chọn **Run workflow**. Mỗi bản đều chạy test mạng, mở giao diện từ source và mở app đã đóng gói rồi tự đóng để phát hiện lỗi khởi động. Artifacts của mỗi lần chạy được giữ 30 ngày.

Khi cả 6 bản thành công trên `main`, workflow đọc `VERSION` và tạo GitHub Release tương ứng (ban đầu `v1.0.0`), kèm 6 file và `SHA256SUMS.txt`. Release được chuẩn bị dạng draft rồi công khai sau khi upload. PR chỉ build, không phát hành.

Để phát hành phiên bản mới, sửa `VERSION` (ví dụ `1.0.1`) rồi push lên `main`. Release đã tồn tại sẽ được giữ nguyên; build mới vẫn có trong Artifacts. Nếu push tag thủ công, tag phải khớp `VERSION`. Không sửa nội dung một Release đã công khai; tăng phiên bản để phát hành lại.

Build thủ công trên đúng OS/kiến trúc cần xuất:

```sh
python -m pip install -r requirements-build.txt
python scripts/build.py Windows-x64
```

Thay đối số bằng `Windows-x86`, `macOS-x64`, `macOS-arm64`, `Linux-x64` hoặc `Linux-arm64` tương ứng. Build Windows x86 phải dùng Python 32-bit. File đóng gói nằm trong `release/`.
