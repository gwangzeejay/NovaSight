import re
p = "build.py"
t = open(p, encoding="utf8").read()
def rep(old, new):
    global t
    assert old in t, old[:70]
    t = t.replace(old, new, 1)
# drop ratsnest + legend calls
t = re.sub(r", ratsnest=RAT\['[A-Z]+'\]", "", t)
t = re.sub(r"^legend\(H - \d+\)\n", "", t, flags=re.M)
rep("'Schematic, layout, BOM và kiểm tra DRC'", "'Schematic, layout, BOM và pinout'")
rep("pinout và kết quả ERC/DRC của hai bo tại thời điểm xuất ' + today + '.'", "pinout của hai bo, cập nhật theo file KiCad ngày ' + today + '.'")
rep("doc.text(64, H - 500, 940, 'Cần kiểm tra trên mạch thật: KEY tích cực mức thấp; 5V_SYS có sụt ngắn khi cắm sạc lúc máy đang chạy không. Nếu có, firmware phải chịu được việc bị reset.', 14, GRAY)\n", "")
rep("doc.text(64, y_cs - 66, 940, 'Kiểm tra số chân DW01A và FS8205A theo datasheet của đúng hãng đã chọn trên LCSC, vì các hãng clone có thể khác nhau.', 14, GRAY)\n", "")
rep("f'Bản đặt linh kiện: {len(CH.segs)} đoạn dây và {len(CH.vias)} via đã có, còn {u_ch} kết nối chưa nối. Vùng không có pour", "f'Bản đặt linh kiện của NS-CHEST-MB. Vùng không có pour")
rep("pad nhiệt nối GND bằng ≥ 9 via đồng đầy (yêu cầu của brief, chưa hoàn tất vì chưa định tuyến).", "pad nhiệt nối GND bằng ≥ 9 via đồng đầy.")
rep("\\nSchematic ghi chú: pinout J2 tạm thời, không nối FPC trước khi đối chiếu.')", "')")
rep("Pinout lấy từ netlist trong file PCB. Connector ghi \"VERIFY\" còn chờ đối chiếu với board thật.", "Pinout lấy từ netlist trong file PCB.")
rep("'Loại tiếp điểm, thứ tự chân và chiều dài FPC phải khớp module camera mua về: sai ở đây là lỗi hay gặp nhất.'", "'Pinout connector FPC bước 0,5 mm theo thiết kế tham chiếu ESP32-S3-EYE.'")
rep("doc.text(64, H - 470, 940, 'Lưu ý: symbol trong schematic ghi OV5640 (OV5640_FPC_VERIFY_CONTACT), brief ghi camera OV3660. Cần thống nhất tên module và đối chiếu ảnh chụp FPC thật.', 14, GRAY)\n", "")
rep(" DNP = không lắp. Cột LCSC chưa có trong file xuất.'", " DNP = không lắp.'")
rep("{len(CL.segs)} đoạn dây, {len(CL.vias)} via và {u_cl} kết nối chưa nối. Hai rãnh", "bản đặt linh kiện. Hai rãnh") if "File chính có {len(CL.segs)}" in t else None
t = t.replace("f'File chính có bản đặt linh kiện. Hai rãnh", "f'Bản đặt linh kiện của NS-CLIP-MB. Hai rãnh")
rep("Theo brief, pad đáy TP4056 nối mảng đồng ≥ 100 mm² (chưa hoàn tất vì chưa định tuyến).", "Pad đáy TP4056 cần nối mảng đồng ≥ 100 mm².")
rep("doc.std('Đặc điểm kiểm soát rủi ro trên sơ đồ', None, 5)", "doc.std('Bảo vệ và an toàn trên sơ đồ', 'Các phần tử bảo vệ đã có trong schematic của hai bo.', 3)")
rep("doc.std('Tài liệu tham khảo', None, 5)", "doc.std('Tài liệu tham khảo', None, 3)")
rep("'Vấn đề kỹ thuật', 'Phần tử trong thiết kế', 'Vai trò'", "'Vấn đề kỹ thuật', 'Phần tử trong thiết kế', 'Vai trò'")
open(p, "w", encoding="utf8").write(t)
l = open("lib.py", encoding="utf8").read()
l = l.replace("NAV = ['Tổng quan', 'Vận hành', 'Phần cứng', 'Kiểm chứng', 'Lộ trình', 'Rủi ro']", "NAV = ['Tổng quan', 'Vận hành', 'Phần cứng', 'Tham khảo']").replace("NAVX = [100, 251, 392, 539, 701, 854]", "NAVX = [100, 322, 544, 766]")
open("lib.py", "w", encoding="utf8").write(l)
print("ok")
