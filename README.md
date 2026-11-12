# NovaSight · Rev A P1

NovaSight là nguyên mẫu hỗ trợ người dùng gậy trắng. NovaChest đo phía trước và cảnh báo qua hai vai. NovaCane Clip gắn dưới tay cầm, có rung, đèn Xin đường và nút SOS. NovaApp là giao diện thử nghiệm tùy chọn cho Clip.

**Tài liệu chính** · [Cookbook NovaSight](COOKBOOK.md)

| Thư mục | Nội dung |
| --- | --- |
| [firmware](firmware/) | PlatformIO cho ESP32-S3 NovaChest và ESP32-C3 NovaCane Clip |
| [novaapp](novaapp/) | Ứng dụng web tĩnh tiếng Việt cho Clip qua BLE |
| [output/3d](output/3d/NovaSight-3D.html) | Lắp ráp 3D và mô phỏng sử dụng: nhân vật tóc trắng, băng mắt, áo đen tím; bối cảnh phố với cửa hàng và cây xanh |
| [hardware](hardware/) | Hai project KiCad P1, báo cáo ERC/DRC và lịch sử đi dây |
| [output/pcb-prototype](output/pcb-prototype/README.md) | Gerber, khoan và yêu cầu chế tạo bo mẫu |
| [output/pcb-review](output/pcb-review/README.md) | BOM/CPL, DXF, STEP và ghi chú kỹ thuật |
| [source_review](source_review/) | Mô tả sản phẩm, brief PCB và tài liệu tham chiếu |
| [tools](tools/) và [tests](tests/) | Kiểm tra CAD/CAM, logic firmware và giao thức NovaApp. `python -X utf8 tools/bom.py` gộp BOM P1, gán mã LCSC và kiểm tra tồn kho JLCPCB, kết quả ở `output/bom/p1` |

Chạy từ thư mục gốc sau khi đã cài PlatformIO, Python, KiCad 10 và Node.js. Nếu đường dẫn dự án có dấu tiếng Việt, `pio run` lỗi `.tmp: Invalid argument`. Đặt trước `PYTHONUTF8=1`, `PLATFORMIO_BUILD_DIR` và `PLATFORMIO_LIBDEPS_DIR` trỏ tới thư mục ASCII, như [Cookbook mục 3](COOKBOOK.md).

```powershell
pio run -d firmware
python tools/hardware.py
python tools/test_core.py
node --test tests/app_test.mjs
python -m http.server 8000 --bind 127.0.0.1 --directory novaapp
```

Mở [NovaApp trên localhost](http://localhost:8000) trong trình duyệt hỗ trợ Web Bluetooth. Cookbook có lệnh cho đường dẫn Windows chứa dấu, thứ tự cấp nguồn, nạp, hiệu chuẩn và kiểm thử trên mẫu.

Để xem mô phỏng, chạy `python -m http.server 8765 --bind 127.0.0.1` từ thư mục gốc rồi mở [NovaSight 3D](http://localhost:8765/output/3d/NovaSight-3D.html), chọn **Mô phỏng sử dụng**. Phím **5** hoặc nút **Cận cảnh nhân vật** mở góc nhìn nhân vật; **1–4** đổi các góc nhìn còn lại, **Space** chạy/dừng, **F** trình chiếu. Hình học nhân vật và bối cảnh được dựng trực tiếp trong HTML; Three.js vẫn tải qua CDN nên cần kết nối mạng khi mở lần đầu.

P1 dùng cho thử nghiệm kỹ thuật có giám sát. Hãy tiếp tục dùng gậy trắng và kỹ thuật định hướng, di chuyển (O&M). Các phép đo trên bo thật, hiệu năng phát hiện nguy cơ và độ tin cậy SOS cần được nghiệm thu trước thử nghiệm di chuyển.
