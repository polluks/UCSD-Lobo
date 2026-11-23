# UCSD p-System IV.0 (Full Adaptable) for Lobo MAX-80

Native port of the **SofTech Microsystems UCSD p-System IV.0** (*Full Adaptable System*) for the **Lobo MAX-80** microcomputer — booting directly from floppy disk **without CP/M**.

---

## 1. Overview & Architecture

The Full Adaptable p-System IV separates the hardware-independent p-Machine interpreter and operating system from hardware-specific drivers via the **SBIOS** (*Simplified Basic Input/Output System*).

On the Lobo MAX-80 (Z80-B @ 5.07 MHz, 64 KB / 128 KB RAM) the system runs with bank A RAM mapped as a contiguous 64 KB address space. All on-board peripherals are **memory-mapped** inside a relocatable 4 KB block — the Z80 I/O port space is used only by expansion cards. The MAX-80 has **no Z80 CTC**; the SIO, PIO, CRTC, MB8866 FDC and 1 KB SWAP1K window are accessed directly.

### System requirements

* **Hardware:** Lobo MAX-80 with 64 KB RAM minimum.
* **Storage:** 5.25" or 8" floppy formatted with **17 sectors × 512 bytes** per track (one UCSD logical block = one physical sector).
* **Console:** built-in 80×24 monochrome CRT (HD46505/6845 CRTC) and keyboard matrix.

---

## 2. Memory map & boot process

The boot ROM overlays 0000H–03FFH, loads Track 0 / Sector 0 into **0400H**, and jumps there. It has already selected contiguous bank A RAM (PIO data A = 40H) and left `IY` pointing at the memory-mapped MLATCH register.

```text
FFFFH +-----------------------------------+
      |   4 KB memory-mapped I/O block    |  F000H..FFFFH (VLATCH = F1H)
      |   FDC / CRTC / PIO / SIO / KBD    |
F000H +-----------------------------------+
      |         SBIOS (0E000H)            |  vector table + drivers
E000H +-----------------------------------+
      |     secondary bootstrap (D000H)   |
D000H +-----------------------------------+
      |          free application RAM     |
      +-----------------------------------+
0100H |   p-Machine interpreter / kernel  |
0000H +-----------------------------------+
```

### Bootstrap chain

1. **BOOT1** (Track 0, Sector 0 → 0400H): uses the ROM's disk-read entry at 0003H to load BOOT2, then relocates the I/O block to F000H (`VLATCH = F1H`) and hides the ROM overlay.
2. **BOOT2** (D000H): loads the SBIOS from reserved blocks, scans the UCSD directory for `SYSTEM.INTERP`, loads it, pushes the 12 boot parameter words required by the Interpreter, and jumps to it.
3. **Interpreter**: its own tertiary bootstrap loads `SYSTEM.PASCAL` and starts the p-System.

---

## 3. MAX-80 SBIOS implementation

`asm/sbios.z80` implements the full 15-entry mandatory SBIOS vector table at `0E000H` (offsets `00H`–`2AH`) plus the 13 extended vectors (`2DH`–`51H`).

| Vector | Hardware / function |
| :--- | :--- |
| `SYSINIT` / `SYSHALT` | CRTC, SIO and FDC initialization; stores the Interpreter jump table pointer |
| `CONINIT` / `CONWRIT` | 80×24 text output, scroll, tab/backspace/CR/LF, DLE blank compression and a small ANSI/ADM-3A escape parser |
| `CONSTAT` / `CONREAD` | 8×8 keyboard matrix scan with one-character pending buffer |
| `SETDISK` / `SETTRK` / `SETSEC` / `SETBUFR` | SBIOS disk state (`CURDISK`, `CURTRAK`, `CURSECT`, `CURBUFR`) |
| `DSKREAD` / `DSKWRIT` / `DSKINIT` | MB8866/FD1793-compatible FDC with complemented registers; 512-byte blocks |
| `PRN*` | Centronics parallel port |
| `REM*` | Z80-SIO channel A (9600 baud) |
| `CLKREAD` | MSM5832 real-time clock via PIO port B |

The second 1 KB of video RAM is reached through the SWAP1K window by temporarily changing `VLATCH`, then restoring it.

---

## 4. Build & installation workflow

Build on a modern host with a Z80 cross-assembler (`pasmo`) and Python 3:

```sh
make PASMO=pasmo
make PASMO=pasmo INTERP=files/SYSTEM.INTERP PASCAL=files/SYSTEM.PASCAL image
make check
```

`doc/BUILDING.md` explains how to obtain `SYSTEM.INTERP` and `SYSTEM.PASCAL` from an adaptable p-System IV disk (for example the z80pack images) and how to configure `SYSTEM.MISCINFO` for the 80×24 console.

The final image uses 512-byte logical blocks:

| Block | Contents |
| ---: | :--- |
| 0 | BOOT1 (Track 0, Sector 0) |
| 1 | BOOT2 |
| 2–5 | UCSD directory |
| 10–17 | SBIOS |
| 18+ | `SYSTEM.INTERP`, `SYSTEM.PASCAL`, `SYSTEM.MISCINFO` |

Write `build/system.img` to a floppy with a Greaseweazle, or load it on a Gotek/FlashFloppy attached to the MAX-80.

---

## 5. References & Resources

* **SofTech Microsystems:** *Adaptable p-System IV.0 Installation Guide* (SBIOS specification, jump table offsets, bootstrap requirements)
* **Lobo Systems:** *MAX-80 Technical Reference Manual* and original BIOS/ROM listings (`tim-mann.org/max80`)
* **Reference SBIOS:** GmEsoft `Z80-MBC2_UCSDP` (`ucsdp.asm`)
* **Tools:** `pasmo`, z80pack UCSD p-System IV images, `ucsdpsys_fs`
