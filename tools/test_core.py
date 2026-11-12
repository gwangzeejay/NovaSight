"""Compile and execute the portable C++ behavior tests on the host."""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--cxx", default=os.environ.get("CXX") or shutil.which("g++") or shutil.which("clang++"))
args = parser.parse_args()
if not args.cxx:
    parser.error("Provide a C++ compiler with --cxx or CXX.")

with tempfile.TemporaryDirectory(prefix="novasight-core-") as folder:
    binary = Path(folder) / ("core.exe" if os.name == "nt" else "core")
    subprocess.run([args.cxx, "-std=c++14", "-Wall", "-Wextra", "-Werror", "-I", "firmware/include",
                    "firmware/src/common/nova_core.cpp", "tests/core_test.cpp", "-o", str(binary)],
                   cwd=root, check=True)
    subprocess.run([str(binary)], check=True)
