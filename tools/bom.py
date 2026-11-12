"""Gộp BOM P1 theo linh kiện, gán mã LCSC và kiểm tra tồn kho trên JLCPCB.

Nguồn: output/pcb-review/<bo>/<bo>-BOM-review.csv (xuất từ schematic P1 bằng tools/hardware.py).
Kết quả: output/bom/p1/. Không sửa schematic, PCB hay Gerber.

    python -X utf8 tools/bom.py             # tra tồn kho qua API công khai của JLCPCB
    python -X utf8 tools/bom.py --offline   # chỉ dùng bảng mã trong tệp này
    python -X utf8 tools/bom.py --boards 5  # số bo dùng để cảnh báo thiếu tồn kho
"""

import argparse
import csv
import json
from pathlib import Path
import re
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BOARDS = ("NS-CHEST-MB", "NS-CLIP-MB")
OUT = ROOT / "output/bom/p1"
API = "https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList"

# jlc  : JLCPCB hàn (SMD).  hand : tự hàn hoặc mua rời (xuyên lỗ, dây, module).  none : pad trên PCB, không có linh kiện.
# Mỗi mục: (LCSC, hãng, MPN, cách lắp, ghi chú). LCSC = None nghĩa là chưa có nguồn trên JLCPCB.
CAP = {
    ("100nF_10V", "0402"): ("C1525", "Samsung", "CL05B104KO5NNNC", "jlc", "16 V X7R, Basic"),
    ("1uF_10V", "0402"): ("C52923", "Samsung", "CL05A105KA5NQNC", "jlc", "25 V X5R, Basic"),
    ("10uF_10V", "0603"): ("C19702", "Samsung", "CL10A106KP8NNNC", "jlc", "10 V X5R, Basic"),
    ("22uF_10V", "0805"): ("C45783", "Samsung", "CL21A226MAQNNNE", "jlc", "25 V X5R thay 10 V để bớt tụt điện dung theo điện áp, Basic"),
    ("22pF_50V", "0402"): ("C1555", "FH", "0402CG220J500NT", "jlc", "C0G, Basic"),
    ("22nF_16V_X7R", "0402"): ("C1532", "FH", "0402B223K500NT", "jlc", "50 V X7R thay 16 V, Basic"),
    ("10nF_10V", "0402"): ("C15195", "Samsung", "CL05B103KB5NNNC", "jlc", "50 V X7R, Basic"),
    ("2.2nF_50V", "0402"): ("C106861", "YAGEO", "CC0402KRX7R9BB222", "jlc", "Không có dòng Basic, Extended"),
}


def res(lcsc, maker, mpn, basic=True):
    return (lcsc, maker, mpn, "jlc", "1% thick film, " + ("Basic" if basic else "Extended"))


RES = {
    ("0R", "0402"): res("C17168", "UNI-ROYAL", "0402WGF0000TCE"),
    ("0R_OPTION_5V", "0402"): res("C17168", "UNI-ROYAL", "0402WGF0000TCE"),
    ("22R", "0402"): res("C25092", "UNI-ROYAL", "0402WGF220JTCE"),
    ("100R", "0402"): res("C25076", "UNI-ROYAL", "0402WGF1000TCE"),
    ("1k", "0402"): res("C11702", "UNI-ROYAL", "0402WGF1001TCE"),
    ("2.2k", "0402"): res("C25879", "UNI-ROYAL", "0402WGF2201TCE"),
    ("3.0k_1%", "0402"): res("C25784", "UNI-ROYAL", "0402WGF3001TCE", False),
    ("4.7k", "0402"): res("C25900", "UNI-ROYAL", "0402WGF4701TCE"),
    ("5.1k_1%", "0402"): res("C25905", "UNI-ROYAL", "0402WGF5101TCE"),
    ("10k", "0402"): res("C25744", "UNI-ROYAL", "0402WGF1002TCE"),
    ("10k_1%", "0402"): res("C25744", "UNI-ROYAL", "0402WGF1002TCE"),
    ("15k_1%", "0402"): res("C25756", "UNI-ROYAL", "0402WGF1502TCE"),
    ("47k", "0402"): res("C25792", "UNI-ROYAL", "0402WGF4702TCE"),
    ("68k_1%", "0402"): res("C36871", "UNI-ROYAL", "0402WGF6802TCE", False),
    ("100k", "0402"): res("C25741", "UNI-ROYAL", "0402WGF1003TCE"),
    ("100k_1%", "0402"): res("C25741", "UNI-ROYAL", "0402WGF1003TCE"),
    ("150k_1%", "0402"): res("C25755", "UNI-ROYAL", "0402WGF1503TCE", False),
    ("470k", "0402"): res("C25790", "UNI-ROYAL", "0402WGF4703TCE", False),
    ("470k_1%", "0402"): res("C25790", "UNI-ROYAL", "0402WGF4703TCE", False),
    ("680k_1%", "0402"): res("C4131", "UNI-ROYAL", "0402WGF6803TCE", False),
    ("100R", "0603"): res("C22775", "UNI-ROYAL", "0603WAF1000T5E"),
    ("68R", "0603"): res("C27592", "UNI-ROYAL", "0603WAF680JT5E", False),
}

OTHER = {
    # Diode, LED
    "STATUS_WHITE": ("C2290", "KENTO", "KT-0603W", "jlc", "Vf 2,6–3,1 V, Basic"),
    "SOC_GREEN": ("C12624", "KENTO", "KT-0603G", "jlc", "Extended"),
    "FULL_GREEN": ("C12624", "KENTO", "KT-0603G", "jlc", "Extended"),
    "STATUS_GREEN": ("C12624", "KENTO", "KT-0603G", "jlc", "Extended"),
    "CHARGE_RED": ("C2286", "KENTO", "KT-0603R", "jlc", "Basic"),
    "BEACON_RED": ("C87271", "Everlight", "333-2SURD/S530-A3", "hand", "LED 5 mm xuyên lỗ, tự hàn"),
    "BEACON_WHITE": (None, "", "LED trắng 5 mm", "hand", "Mua rời, không tìm được mã LCSC phù hợp"),
    "B5819W": ("C2943878", "GOODWORK", "B5819W", "jlc", "Extended"),
    "SS14": ("C2480", "MDD", "SS14", "jlc", "Basic"),
    "PTC_HOLD_0.5A": ("C43379", "RUILON", "SMD1206P050TF/13.2", "jlc", "Giữ 0,5 A, 13,2 V, Extended"),
    # Connector, switch
    "USB-C": ("C3020560", "GCT", "USB4105-GF-A", "jlc", "Đối chiếu footprint 16P theo datasheet GCT trước khi đặt"),
    "USB-C_USB4105": ("C3020560", "GCT", "USB4105-GF-A", "jlc", "Đối chiếu footprint 16P theo datasheet GCT trước khi đặt"),
    "OV5640_DVP_FPC24": ("C202112", "Hirose", "FH12-24S-0.5SH(55)", "jlc", "Hậu tố (55) khác (98) ở đóng gói, cùng bước 0,5 mm, tiếp xúc dưới"),
    "TOF_HARNESS_VERIFY": ("C160407", "JST", "SM08B-SRSS-TB(LF)(SN)", "jlc", "Cần xác nhận pinout breakout ToF trước"),
    "BATTERY_PROTECTED_1S": ("C131337", "JST", "B2B-PH-K-S(LF)(SN)", "hand", "Xuyên lỗ, tự hàn. Xác nhận cực pin"),
    "MOTOR_R": ("C131337", "JST", "B2B-PH-K-S(LF)(SN)", "hand", "Xuyên lỗ, tự hàn"),
    "MOTOR_L": ("C131337", "JST", "B2B-PH-K-S(LF)(SN)", "hand", "Xuyên lỗ, tự hàn"),
    "JSN_R_VERIFY": ("C131334", "JST", "B4B-PH-K-S(LF)(SN)", "hand", "Xuyên lỗ, tự hàn. Cần xác nhận pinout JSN-SR04T"),
    "JSN_L_VERIFY": ("C131334", "JST", "B4B-PH-K-S(LF)(SN)", "hand", "Xuyên lỗ, tự hàn. Cần xác nhận pinout JSN-SR04T"),
    "GY521_OPTION_DNP": ("C160405", "JST", "SM06B-SRSS-TB(LF)(SN)", "none", "DNP"),
    "BATTERY_1S_WIRE": (None, "", "Dây pin hàn trực tiếp", "none", "Pad dây, không có linh kiện"),
    "MOTOR_L_WIRE": (None, "", "Dây motor hàn trực tiếp", "none", "Pad dây, không có linh kiện"),
    "MOTOR_R_WIRE": (None, "", "Dây motor hàn trực tiếp", "none", "Pad dây, không có linh kiện"),
    "POWER_ON": ("C431540", "SHOU HAN", "MSK12C02", "jlc", "Chịu 50 mA, chỉ dùng để điều khiển MOSFET hoặc chân EN"),
    "MODE_EVQPUJ02K_SIDE": ("C128539", "Panasonic", "EVQPUA02K", "jlc", "EVQPUJ02K hết hàng. EVQPUA02K dùng chung footprint nhưng chỉ còn rất ít tồn kho"),
    "BOOT": ("C2886897", "E-Switch", "TL3342F450QG", "jlc", "4,5 N"),
    "RESET": ("C2886897", "E-Switch", "TL3342F450QG", "jlc", "4,5 N"),
    "IP_KEY_TEST": ("C2886897", "E-Switch", "TL3342F450QG", "none", "DNP"),
    "MODE": ("C713480", "Panasonic", "EVQP2B02B", "jlc", "2,5 N, chọn lực nhấn lớn cho nút điều khiển"),
    "ROUTE": ("C713480", "Panasonic", "EVQP2B02B", "jlc", "2,5 N"),
    "SOS": ("C713480", "Panasonic", "EVQP2B02B", "jlc", "2,5 N, lực lớn để giảm bấm nhầm"),
    # Inductor
    "XAL7020-102_1uH_VERIFY": (None, "Coilcraft", "XAL7020-102", "hand", "Không có trên JLCPCB. Mua tại Coilcraft hoặc nhà phân phối (chọn hậu tố theo catalog, thường MEB ±20%), tự hàn"),
    "2.2uH_Isat1.5A": ("C913207", "Bourns", "SRN4018-2R2M", "jlc", "Isat 2,9 A, Extended"),
    # Transistor
    "AO3401A": ("C15127", "AOS", "AO3401A", "jlc", "Basic"),
    "AO3400A": ("C20917", "AOS", "AO3400A", "jlc", "Basic"),
    "2N7002": ("C8545", "Changjing", "2N7002", "jlc", "Basic"),
    "FS8205A_Fortune": ("C5148694", "HXY", "8205A", "jlc", "Bản Fortune C16052 hết hàng. Footprint TSSOP-8 giữ nguyên, kiểm tra pinout theo datasheet HXY"),
    # IC
    "USBLC6-2SC6": ("C7519", "ST", "USBLC6-2SC6", "jlc", "Bản ST chính hãng"),
    "IP5306": ("C181692", "INJOINIC", "IP5306", "jlc", "ESOP-8"),
    "SY8088IAAC": ("C479072", "Silergy", "SY8088IAAC", "jlc", ""),
    "ESP32-S3-WROOM-1-N16R8": ("C2913202", "Espressif", "ESP32-S3-WROOM-1-N16R8", "jlc", ""),
    "ESP32-C3-MINI-1-N4X": ("C2838502", "Espressif", "ESP32-C3-MINI-1-N4", "jlc", "N4X hết hàng, N4 cùng footprint và flash 4 MB. Cần bạn đồng ý đổi"),
    "74AHCT1G125": ("C7484", "TI", "SN74AHCT1G125DBVR", "jlc", ""),
    "ME6211C28M5G-N": ("C53099", "MICRONE", "ME6211C28M5G-N", "jlc", ""),
    "ME6211C15M5G-N": ("C53100", "MICRONE", "ME6211C15M5G-N", "jlc", ""),
    "MPU-6050": ("C24112", "TDK InvenSense", "MPU-6050", "jlc", "Giá khoảng 21 USD mỗi con"),
    "SN74LVC1G125DBVR_XCLK_2V8": ("C23654", "TI", "SN74LVC1G125DBVR", "jlc", ""),
    "TLV809EC26DBZR": ("C2868082", "TI", "TLV809EC26DBZR", "jlc", ""),
    "TPS389015DSER": ("C702226", "TI", "TPS389015DSER", "consign", "Hết hàng ở JLCPCB, không có biến thể cùng ngưỡng 1,5 V. Mua ngoài và gửi JLCPCB hàn (WSON-6 1,5 × 1,5 mm khó tự hàn)"),
    "TP4056-42-ESOP8": ("C16581", "TOPPOWER", "TP4056-42-ESOP8", "jlc", ""),
    "AP2112K-3.3TRG1": ("C51118", "Diodes Inc", "AP2112K-3.3TRG1", "jlc", "Bản chính hãng"),
    "DW01A": ("C351410", "PUOLOP", "DW01A", "jlc", ""),
}


# Mục tồn kho ít đã được duyệt cho lô 1 bo (EVQPUA02K thay EVQPUJ02K).
APPROVED_LOW = {"C128539"}


def package(footprint):
    m = re.search(r"_(\d{4})_\d{4}Metric", footprint)
    return m.group(1) if m else ""


def lookup(value, footprint):
    if footprint.startswith("TestPoint"):
        return (None, "", "Pad thử trên PCB", "none", "Test point, không có linh kiện")
    pkg = package(footprint)
    if footprint.startswith("Capacitor_SMD"):
        return CAP.get((value, pkg))
    if footprint.startswith("Resistor_SMD"):
        return RES.get((value, pkg))
    return OTHER.get(value)


def query(code):
    body = json.dumps({"keyword": code, "currentPage": 1, "pageSize": 10}).encode()
    for _ in range(3):
        try:
            req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=40) as response:
                items = json.load(response)["data"]["componentPageInfo"]["list"] or []
            for item in items:
                if item["componentCode"] == code:
                    return item
        except OSError:
            pass
        time.sleep(1.5)
    return None


def load(board):
    path = ROOT / "output/pcb-review" / board / f"{board}-BOM-review.csv"
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def group(rows):
    lines, missing = {}, []
    for row in rows:
        entry = lookup(row["Value"], row["Footprint"])
        if entry is None:
            missing.append(f"{row['Refs']} {row['Value']} {row['Footprint']}")
            continue
        dnp = bool(row["DNP"].strip())
        key = (entry[0], row["Value"] if entry[0] is None else "", entry[2], "none" if dnp else entry[3])
        line = lines.setdefault(key, {"entry": entry, "refs": [], "values": set(), "footprint": row["Footprint"],
                                      "mode": "none" if dnp else entry[3], "dnp": dnp})
        line["refs"].append(row["Refs"])
        line["values"].add(row["Value"])
    return lines, missing


def natural(ref):
    return [int(p) if p.isdigit() else p for p in re.split(r"(\d+)", ref)]


def main():
    sys.stdout.reconfigure(errors="backslashreplace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--boards", type=int, default=1, help="Số bo cần lắp, dùng để so với tồn kho")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    cache = {}
    problems, summary = [], []
    for board in BOARDS:
        lines, missing = group(load(board))
        if missing:
            print(f"{board}: CHƯA CÓ ÁNH XẠ cho:\n  " + "\n  ".join(missing))
            return 1
        final, jlc_rows = [], []
        cost, extended = 0.0, set()
        for key in sorted(lines, key=lambda k: natural(lines[k]["refs"][0])):
            line = lines[key]
            code, maker, mpn, _, note = line["entry"]
            refs = sorted(line["refs"], key=natural)
            qty = len(refs)
            info = None
            if code and not args.offline and line["mode"] != "none":
                info = cache.get(code) or cache.setdefault(code, query(code))
            library = stock = price = ""
            status = "ok"
            if line["mode"] == "none":
                status = "DNP" if line["dnp"] else "không cần mua"
            elif line["mode"] == "consign":
                status = "đã duyệt: mua ngoài, gửi JLCPCB hàn"
            elif code is None:
                status = "đã duyệt: mua ngoài" if line["mode"] == "hand" else "THIẾU MÃ"
            elif not args.offline:
                if info is None:
                    status = "KHÔNG TRA ĐƯỢC"
                else:
                    library = ("Basic" if info["componentLibraryType"] == "base" else
                               "Preferred" if info.get("preferredComponentFlag") else "Extended")
                    stock = info["stockCount"] or 0
                    price = info["componentPrices"][0]["productPrice"] if info.get("componentPrices") else ""
                    if stock <= 0:
                        status = "HẾT HÀNG"
                    elif line["mode"] == "jlc" and stock < qty * args.boards * 2:
                        status = "đã duyệt: tồn kho thấp, đủ cho 1 bo" if code in APPROVED_LOW and args.boards <= 1 else "TỒN KHO THẤP"
            if line["mode"] == "jlc" and (status == "ok" or status.startswith("đã duyệt") or status == "TỒN KHO THẤP"):
                if price != "":
                    cost += float(price) * qty
                if library == "Extended":
                    extended.add(code)
            if not (status in ("ok", "DNP", "không cần mua") or status.startswith("đã duyệt")):
                problems.append((board, ",".join(refs), code or "—", mpn, status, note))
            value = "/".join(sorted(line["values"]))
            final.append({"Refs": ",".join(refs), "Qty": qty, "Value": value, "Footprint": line["footprint"],
                          "Manufacturer": maker, "MPN": mpn, "LCSC": code or "", "Library": library,
                          "Assembly": {"jlc": "JLCPCB", "hand": "Tự hàn/mua rời", "consign": "Mua ngoài, gửi JLCPCB hàn", "none": "—"}[line["mode"]],
                          "Stock": stock, "UnitUSD": price, "Status": status, "Note": note})
            if line["mode"] == "jlc" and code:
                jlc_rows.append({"Comment": mpn, "Designator": ",".join(refs), "Footprint": line["footprint"].split(":")[-1],
                                 "LCSC Part #": code})
        with (OUT / f"{board}-BOM-final.csv").open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=list(final[0]))
            writer.writeheader()
            writer.writerows(final)
        buy = [r for r in final if r["Assembly"] in ("Tự hàn/mua rời", "Mua ngoài, gửi JLCPCB hàn")]
        with (OUT / f"{board}-mua-ngoai.csv").open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["Refs", "Qty", "Manufacturer", "MPN", "LCSC", "Assembly", "Status", "Note"],
                                    extrasaction="ignore")
            writer.writeheader()
            writer.writerows(buy)
        with (OUT / f"{board}-BOM-JLCPCB.csv").open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=list(jlc_rows[0]))
            writer.writeheader()
            writer.writerows(jlc_rows)
        placed = sum(r["Qty"] for r in final if r["Assembly"] == "JLCPCB")
        hand = sum(r["Qty"] for r in final if r["Assembly"] == "Tự hàn/mua rời")
        summary.append((board, len(jlc_rows), placed, hand, len(extended), cost))
    print("Bo | dòng JLC | linh kiện JLC hàn | tự hàn | mã Extended (có phí) | tiền linh kiện JLC (USD, 1 bo, chưa gồm phí)")
    for board, lines_n, placed, hand, ext, cost in summary:
        print(f"{board} | {lines_n} | {placed} | {hand} | {ext} | {cost:.2f}")
    print("\nVấn đề cần xử lý:" if problems else "\nKhông có vấn đề tồn kho.")
    for board, refs, code, mpn, status, note in problems:
        print(f"  {board} {refs}: {status} ({code} {mpn}) {note}")
    print(f"\nĐã ghi vào {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
