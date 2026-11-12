"""Audit current P1 schematics and CAM. Export review files to a new directory."""

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from xml.etree import ElementTree
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
BOARDS = ("NS-CHEST-MB", "NS-CLIP-MB")
COMMON_LAYERS = ("F.Mask", "B.Mask", "F.Silkscreen", "B.Silkscreen", "F.Paste", "Edge.Cuts")
CHEST_PINS = {
    "sda": "I2C_SDA", "scl": "I2C_SCL", "imuInt": "IMU_INT",
    "motorLeft": "MOT_L_PWM", "motorRight": "MOT_R_PWM", "mode": "BTN_MODE",
    "status": "LED_STATUS", "battery": "VBAT_ADC", "vbus": "VBUS_DET",
    "triggerLeft": "JSN_L_TRIG_IN", "echoLeft": "JSN_L_ECHO",
    "triggerRight": "JSN_R_TRIG_IN", "echoRight": "JSN_R_ECHO", "tofEnable": "TOF_LPN",
    "tofInt": "TOF_INT", "camSda": "CAM_SIOD", "camScl": "CAM_SIOC",
    "camVsync": "CAM_VSYNC", "camHref": "CAM_HREF", "camXclk": "CAM_XCLK_SRC", "camPclk": "CAM_PCLK",
}
CLIP_PINS = {key: CHEST_PINS[key] for key in
             ("sda", "scl", "imuInt", "motorLeft", "motorRight", "mode", "status", "battery", "vbus")}
CLIP_PINS.update(route="BTN_ROUTE", sos="BTN_SOS", beacon="LED_BEACON")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def locate_cli(explicit):
    if explicit:
        return explicit
    found = shutil.which("kicad-cli")
    if found:
        return found
    local = Path(os.environ.get("LOCALAPPDATA", ".")) / "Programs/KiCad/10.0/bin/kicad-cli.exe"
    require(local.is_file(), "KiCad CLI not found. Set KICAD_CLI or pass --kicad.")
    return str(local)


def run(cli, *args):
    process = subprocess.run([cli, *map(str, args)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = process.stdout.decode("utf-8", errors="replace").strip()
    if process.returncode:
        raise ValueError(f"KiCad exit {process.returncode} for {' '.join(map(str, args))}\n{output}")
    return output


def json_file(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def verify_reports(drc, erc):
    errors = [item for item in drc["violations"] if item["severity"] == "error"]
    warnings = [item for item in drc["violations"] if item["severity"] == "warning"]
    erc_items = [item for sheet in erc["sheets"] for item in sheet["violations"]]
    require(not errors and not drc["unconnected_items"] and not drc["schematic_parity"] and not erc_items,
            f"{drc['source']}: {len(errors)} DRC errors, {len(drc['unconnected_items'])} open, "
            f"{len(drc['schematic_parity'])} parity, {len(erc_items)} ERC")
    return len(warnings)


def verify_pins(netlist, chest):
    module = "U4" if chest else "U1"
    source = (ROOT / "firmware/include/pins.h").read_text(encoding="utf-8")
    chest_text, clip_text = source.split("#elif defined(NOVA_CLIP)")
    pins = chest_text if chest else clip_text
    expected = CHEST_PINS if chest else CLIP_PINS
    gpio = {}
    for net in ElementTree.parse(netlist).findall("./nets/net"):
        for node in net.findall("node"):
            if node.get("ref") != module:
                continue
            function = node.get("pinfunction", "")
            match = re.match(r"(?:GPIO|IO)(\d+)", function)
            if match:
                value = int(match[1])
            elif chest and function.startswith("RXD0_"):
                value = 44
            else:
                continue
            gpio[net.attrib["name"].lstrip("/")] = value
    for name, net in expected.items():
        match = re.search(rf"\b{name}\s*=\s*(\d+)", pins)
        require(match and int(match[1]) == gpio.get(net), f"{module} {name} disagrees with {net}")
    if chest:
        match = re.search(r"camData\[\]\s*=\s*\{([\d, ]+)\}", pins)
        require(match and [int(value) for value in match[1].split(",")] ==
                [gpio[f"CAM_Y{index}"] for index in range(2, 10)], "OV5640 D0..D7 order differs from netlist")
    return len(expected) + (8 if chest else 0)


def cam_layers(chest):
    copper = ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu") if chest else ("F.Cu", "B.Cu")
    return (*copper, *COMMON_LAYERS)


def export_cam(cli, board, pcb, dest):
    dest.mkdir()
    out = str(dest) + os.sep
    layers = ",".join(cam_layers(board == BOARDS[0]))
    run(cli, "pcb", "export", "gerbers", "--no-protel-ext", "--subtract-soldermask", "--layers", layers, "-o", out, pcb)
    run(cli, "pcb", "export", "drill", "--format", "excellon", "--excellon-units", "mm",
        "--excellon-separate-th", "--generate-report", "--report-path", dest / f"{board}-drill-report.txt",
        "-o", out, pcb)


def pcb_vias(pcb):
    text = pcb.read_text(encoding="utf-8")
    found = set()
    for via in re.findall(r"^\t\(via\b.*?^\t\)", text, flags=re.M | re.S):
        if "(filling yes)" not in via or "(capping yes)" not in via:
            continue
        x, y = map(float, re.search(r"\(at ([^)]+)\)", via)[1].split())
        drill = float(re.search(r"\(drill ([^)]+)\)", via)[1])
        found.add((round(x, 4), round(-y, 4), round(drill, 3)))
    require(len(found) == 9, f"{pcb.name}: expected nine filled and capped vias")
    return found


def listed_vias(content):
    rows = list(csv.DictReader(io.StringIO(content)))
    found = {(float(row["Excellon_X_mm"]), float(row["Excellon_Y_mm"]), float(row["Drill_mm"])) for row in rows}
    require(len(rows) == len(found) == 9 and all(row["Process"] == "Filled and capped" for row in rows),
            "Invalid filled-and-capped via list")
    return found


def plated_hits(content):
    require("absolute / metric / decimal" in content and "TF.FileFunction,Plated" in content, "Unexpected drill format")
    tools, hits = {}, set()
    active = None
    for line in content.splitlines():
        tool = re.fullmatch(r"T(\d+)C([.\d]+)", line)
        selection = re.fullmatch(r"T(\d+)", line)
        point = re.fullmatch(r"X(-?[.\d]+)Y(-?[.\d]+)", line)
        if tool:
            tools[tool[1]] = float(tool[2])
        elif selection:
            active = tools.get(selection[1])
        elif point and active is not None:
            hits.add((round(float(point[1]), 4), round(float(point[2]), 4), round(active, 3)))
    return hits


def normalized(content):
    text = content.decode("utf-8-sig").replace("\r\n", "\n")
    return re.sub(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[+-]\d{2}:\d{2})?", "<timestamp>", text)


def verify_archive(board, pcb, fresh):
    archive = ROOT / "output/pcb-prototype" / f"{board}-RevA-P1-Gerber.zip"
    generated = {file.name for file in fresh.iterdir() if file.is_file()}
    expected = {f"{board}-{layer.replace('.', '_')}.gbr" for layer in cam_layers(board == BOARDS[0])}
    expected |= {f"{board}-{suffix}" for suffix in ("PTH.drl", "NPTH.drl", "job.gbrjob", "drill-report.txt")}
    require(generated == expected, f"{board}: unexpected CAM members {generated ^ expected}")
    with ZipFile(archive) as zip_file:
        names = zip_file.namelist()
        require(len(names) == len(set(names)) and set(names) ==
                expected | {"Fabrication-notes.txt", "Filled-capped-vias.csv"}, f"{board}: unexpected archive contents")
        require(zip_file.testzip() is None, f"{board}: corrupt archive")
        changed = [name for name in sorted(expected) if normalized(zip_file.read(name)) != normalized((fresh / name).read_bytes())]
        require(not changed, f"{board}: archived CAM differs from fresh export: {', '.join(changed)}")
        listed = listed_vias(zip_file.read("Filled-capped-vias.csv").decode("utf-8-sig"))
        hits = plated_hits(zip_file.read(f"{board}-PTH.drl").decode("utf-8-sig"))
        require(listed == pcb_vias(pcb) and listed <= hits, f"{board}: via locations disagree with PCB or plated drills")
    return hashlib.sha256(archive.read_bytes()).hexdigest()


def export_review(cli, board, pcb, sch, folder, step):
    run(cli, "sch", "export", "bom", "--fields", "Reference,Value,Footprint,LCSC,QUANTITY,DNP",
        "--labels", "Refs,Value,Footprint,LCSC,Qty,DNP", "-o", folder / f"{board}-BOM-review.csv", sch)
    run(cli, "pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "front",
        "--smd-only", "--exclude-dnp", "-o", folder / f"{board}-CPL-review.csv", pcb)
    run(cli, "sch", "export", "pdf", "-o", folder / f"{board}-schematic.pdf", sch)
    run(cli, "pcb", "export", "dxf", "--mode-single", "--output-units", "mm",
        "--layers", "Edge.Cuts,F.Fab", "--drill-shape-opt", "2", "-o", folder / f"{board}-mechanical-review.dxf", pcb)
    if step:
        log = run(cli, "pcb", "export", "step", "--no-dnp", "--subst-models",
                  "-o", folder / f"{board}-assembly.step", pcb)
        (folder / "step.log").write_text(log + "\n", encoding="utf-8")
    # Use the published notes only after every fresh CAM file matches the P1 release.
    with ZipFile(ROOT / "output/pcb-prototype" / f"{board}-RevA-P1-Gerber.zip") as archive:
        for name in ("Fabrication-notes.txt", "Filled-capped-vias.csv"):
            (folder / "cam" / name).write_bytes(archive.read(name))
    with ZipFile(folder / f"{board}-RevA-P1-Gerber.zip", "w", ZIP_DEFLATED) as archive:
        for path in sorted((folder / "cam").iterdir()):
            archive.write(path, path.name)


def audit(cli, base, boards, export, step):
    version = run(cli, "version")
    print(f"KiCad {version}")
    for board in boards:
        project = ROOT / "hardware" / board
        pcb, sch = (project / f"{board}.kicad_{suffix}" for suffix in ("pcb", "sch"))
        dest = base / board
        dest.mkdir()
        drc, erc, netlist = (dest / f"{board}-{kind}" for kind in ("drc.json", "erc.json", "net.xml"))
        run(cli, "pcb", "drc", "--format", "json", "--all-track-errors", "--schematic-parity",
            "--severity-all", "--refill-zones", "-o", drc, pcb)
        run(cli, "sch", "erc", "--format", "json", "--severity-all", "-o", erc, sch)
        warnings = verify_reports(json_file(drc), json_file(erc))
        run(cli, "sch", "export", "netlist", "--format", "kicadxml", "-o", netlist, sch)
        gpio = verify_pins(netlist, board == BOARDS[0])
        export_cam(cli, board, pcb, dest / "cam")
        checksum = verify_archive(board, pcb, dest / "cam")
        print(f"{board}: 0 DRC errors, 0 open, 0 parity, 0 ERC, {warnings} DRC warnings; "
              f"{gpio} GPIO; 9 vias; CAM matches P1")
        print(f"  Published ZIP SHA-256 {checksum}")
        if export:
            export_review(cli, board, pcb, sch, dest, step)


def main():
    # Redirected Windows consoles can default to a code page that cannot print the workspace path.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")
        sys.stderr.reconfigure(errors="backslashreplace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kicad", default=os.environ.get("KICAD_CLI"))
    parser.add_argument("--board", choices=BOARDS)
    parser.add_argument("--out", type=Path, help="New destination directory for verified exports")
    parser.add_argument("--step", action="store_true", help="Include STEP and exporter log with --out")
    options = parser.parse_args()
    if options.step and options.out is None:
        parser.error("--step requires --out")
    try:
        cli = locate_cli(options.kicad)
        boards = (options.board,) if options.board else BOARDS
        if options.out is None:
            with tempfile.TemporaryDirectory(prefix="novasight-") as tmp:
                audit(cli, Path(tmp), boards, False, False)
        else:
            dest = options.out.resolve()
            dest.parent.mkdir(parents=True, exist_ok=True)
            require(not dest.exists(), f"Output already exists: {dest}")
            with tempfile.TemporaryDirectory(prefix="novasight-", dir=dest.parent) as tmp:
                staging = Path(tmp) / "package"
                staging.mkdir()
                audit(cli, staging, boards, True, options.step)
                staging.rename(dest)
            print(f"Verified exports: {dest}")
    except (OSError, ValueError, KeyError, ElementTree.ParseError) as error:
        print(f"Audit failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
