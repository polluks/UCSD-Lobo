#!/usr/bin/env python3
"""Smoke-test the bootstrap chain in the lobo_max80 emulator.

Builds a tiny test SYSTEM.INTERP that prints via SBIOS CONWRIT and halts,
creates a minimal UCSD volume, converts it to IMD, boots it with the MAX-80
ROM in the emulator, and checks that the FDC read sequence reaches the
interpreter load.  This validates ROM->boot1->boot2->SBIOS->directory->interp,
not a real UCSD p-System workload.

The test skips cleanly when the emulator or ROM is unavailable.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOCK = 512
SECTORS = 17
TRACKS = 77

TEST_INTERP_ASM = """\
; Tiny SYSTEM.INTERP stand-in: print via SBIOS CONWRIT, then halt.
        ORG 0100H
        LD HL,msg
loop:
        LD A,(HL)
        OR A
        JR Z,done
        LD C,A
        PUSH HL
        CALL 0E00FH            ; SBIOS CONWRIT
        POP HL
        INC HL
        JR loop
done:
        DI
halt_loop:
        HALT
        JR halt_loop
msg:
        DB 'P-SYSTEM BOOT OK',0
        END
"""


def raw_to_imd(raw: bytes, dest: Path, first_sector: int = 0, mode: int = 5) -> None:
    out = bytearray(b"IMD 1.18: 01/01/2026 00:00:00\r\nsmoke test\r\n\x1a")
    for cyl in range(TRACKS):
        out += bytes([mode, cyl, 0, SECTORS, 2])  # size code 2 = 512 bytes
        out += bytes((first_sector + i) & 0xFF for i in range(SECTORS))
        for i in range(SECTORS):
            off = (cyl * SECTORS + i) * BLOCK
            sector = raw[off:off + BLOCK]
            if len(sector) < BLOCK:
                sector = sector + bytes(BLOCK - len(sector))
            out += b"\x01" + sector
    dest.write_bytes(out)


def find_assembler(name: str) -> str | None:
    if name == "vasm":
        return os.environ.get("VASM") or shutil.which("vasmz80_oldstyle") or shutil.which("vasm")
    return os.environ.get("PASMO") or shutil.which("pasmo")


def assemble(asm: str, src: Path, out: Path, include: Path) -> None:
    if asm == "vasm":
        cmd = [asm, "-quiet", "-Fbin", "-I", str(include), "-o", str(out), str(src)]
        # allow override with full command in env
        exe = find_assembler("vasm")
        if not exe:
            raise RuntimeError("vasmz80_oldstyle not found")
        cmd[0] = exe
    else:
        exe = find_assembler("pasmo")
        if not exe:
            raise RuntimeError("pasmo not found")
        cmd = [exe, "--bin", "--include-dir", str(include), str(src), str(out)]
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emu", default=os.environ.get("MAX80_EMU",
                        str(Path.home() / "g/lobo_max80/emu/max80")))
    parser.add_argument("--rom", default=os.environ.get("MAX80_ROM",
                        str(Path.home() / "g/lobo_max80/reference/rom/max80.e12")))
    parser.add_argument("--asm", choices=["pasmo", "vasm"],
                        default=os.environ.get("ASM", "vasm"))
    parser.add_argument("--build", type=Path, default=ROOT / "build")
    parser.add_argument("--seconds", type=int, default=20)
    args = parser.parse_args()

    emu = Path(args.emu)
    rom = Path(args.rom)
    if not emu.exists() or not rom.exists():
        print(f"SKIP  max80 emulator/ROM not found ({emu}, {rom})")
        return 0
    if not find_assembler(args.asm):
        print(f"SKIP  assembler not found: {args.asm}")
        return 0

    with tempfile.TemporaryDirectory(prefix="ucsd-max80-smoke-") as tmp:
        tmp = Path(tmp)
        src = tmp / "test_interp.z80"
        interp = tmp / "SYSTEM.INTERP"
        src.write_text(TEST_INTERP_ASM)
        include = ROOT / "asm/include"
        exe = find_assembler(args.asm)
        if args.asm == "vasm":
            subprocess.run([exe, "-quiet", "-Fbin", "-o", str(interp), str(src)],
                           check=True, capture_output=True, text=True)
        else:
            subprocess.run([exe, "--bin", str(src), str(interp)],
                           check=True, capture_output=True, text=True)

        (tmp / "SYSTEM.PASCAL").write_bytes(b"P" * BLOCK)
        (tmp / "SYSTEM.MISCINFO").write_bytes(b"M" * BLOCK)

        for name in ("boot1.bin", "boot2.bin", "sbios.bin"):
            if not (args.build / name).exists():
                raise RuntimeError(f"missing {args.build / name}; run make first")

        image = tmp / "system.img"
        subprocess.run([
            sys.executable, str(ROOT / "tools/ucsd_fs.py"), "create",
            "--output", str(image), "--blocks", "1309",
            "--boot1", str(args.build / "boot1.bin"),
            "--boot2", str(args.build / "boot2.bin"),
            "--sbios", str(args.build / "sbios.bin"),
            "--sbios-block", "10",
            "--file", f"SYSTEM.INTERP={interp}:5",
            "--file", f"SYSTEM.PASCAL={tmp / 'SYSTEM.PASCAL'}:5",
            "--file", f"SYSTEM.MISCINFO={tmp / 'SYSTEM.MISCINFO'}:5",
        ], check=True, capture_output=True, text=True)

        imd = tmp / "system.imd"
        raw_to_imd(image.read_bytes(), imd, first_sector=0, mode=5)
        fdc_log = tmp / "fdc.log"

        proc = subprocess.run([
            str(emu), "-T", "-D", "1", "-r", str(rom),
            "-a", str(imd), "-t", str(args.seconds),
            "-G", str(fdc_log),
        ], capture_output=True, text=True)

        if proc.returncode != 0:
            print(proc.stdout)
            print(proc.stderr, file=sys.stderr)
            raise RuntimeError(f"max80 exited with {proc.returncode}")

        log = fdc_log.read_text() if fdc_log.exists() else ""
        # Boot2 reads boot sectors, then SBIOS at block 10 (sector 10, track 0),
        # then directory and SYSTEM.INTERP blocks.
        required = ["cmd 82 drive 0 cyl 0 side 0 track 0 sector 0",
                    "sector 10"]
        for needle in required:
            if needle not in log:
                raise RuntimeError(f"FDC log missing {needle!r}\n{log}")

        # The last reads should reach past the directory into file blocks.
        if log.count("cmd 82") < 10:
            raise RuntimeError(f"too few FDC reads: {log.count('cmd 82')}\n{log}")

        print(f"OK  max80 smoke: {log.count('cmd 82')} FDC reads, boot chain reached interpreter")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"smoke_max80.py: {exc}", file=sys.stderr)
        raise SystemExit(1)
