Server luôn bind `0.0.0.0` cho TCP và UDP. Ô IP chỉ dùng khi chạy client và vẫn tự điền IP local.

App test TCP/UDP có giao diện, chạy độc lập ở chế độ server hoặc client. Không cần cài Python.

| File | Máy phù hợp |
| --- | --- |
| Windows-x86.zip | Windows 10/11 x86 hoặc x64; bản 32-bit |
| Windows-x64.zip | Windows 10/11 x64; bản 64-bit |
| macOS-x64.zip | Mac Intel, macOS 15 trở lên |
| macOS-arm64.zip | Mac Apple Silicon, macOS 15 trở lên |
| Linux-x64.tar.gz | Linux x86-64 có giao diện desktop, glibc 2.35+ (Ubuntu 22.04+) |
| Linux-arm64.tar.gz | Linux ARM64 có giao diện desktop, glibc 2.35+ (Ubuntu 22.04+) |

Giải nén rồi mở `TestTCP.exe`, `TestTCP.app` hoặc `./TestTCP`. Trên macOS, dùng `open -n TestTCP.app` để mở thêm cửa sổ độc lập.

Các bản macOS chưa được ký Developer ID/notarize; Gatekeeper có thể yêu cầu cho phép mở trong System Settings → Privacy & Security. Windows có thể hiển thị cảnh báo SmartScreen cho app chưa ký.

`SHA256SUMS.txt` chứa checksum các file tải về. Mỗi bản đã qua kiểm thử TCP/UDP và kiểm tra khởi động giao diện trong CI; vẫn nên kiểm tra trên máy sử dụng thực tế.
