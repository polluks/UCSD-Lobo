# Building the native p-System image

## Prerequisites

| Tool | Purpose |
| :--- | :--- |
| `pasmo` or `vasm` (Z80, oldstyle syntax) | Z80 cross-assembler |
| Python 3.9+ | Disk-image manipulation and checks |
| `make` | Build driver |
| z80pack UCSD p-System IV disk image | Source of `SYSTEM.INTERP` and `SYSTEM.PASCAL` |
| Greaseweazle / FlashFloppy | Writing the final image |

## Source layout

```
asm/
  boot1.z80        primary bootstrap (Track 0, Sector 0 -> 0400H)
  boot2.z80        secondary bootstrap / system loader
  sbios.z80        SBIOS vectors and MAX-80 drivers
  include/
    max80.inc      memory-mapped hardware registers
    sbios.inc      SBIOS ABI and directory constants
    config.inc     block placements and load addresses
tools/
  ucsd_image.py    low-level 512-byte block image utility
  ucsd_fs.py       directory reader / volume creator
  check_sources.py assembled-binary checks
config/image.json  documented image layout
```

## 1. Obtain the adaptable system files

The original z80pack `ucsd-iv-1.dsk` image uses 128-byte sectors and must be
converted to 512-byte blocks before `ucsd_fs.py` can read it. Use your usual
image-conversion tool, then list and extract the required files:

```sh
python3 tools/ucsd_fs.py list converted.img
python3 tools/ucsd_fs.py extract converted.img SYSTEM.INTERP --out files/SYSTEM.INTERP
python3 tools/ucsd_fs.py extract converted.img SYSTEM.PASCAL --out files/SYSTEM.PASCAL
python3 tools/ucsd_fs.py extract converted.img SYSTEM.MISCINFO --out files/SYSTEM.MISCINFO
```

`SYSTEM.INTERP` must be the native Z80 binary supplied with the adaptable
system. If it is not present on your image, run `SYSGEN` in an emulator to
produce one.

## 2. Configure the terminal

Edit `SYSTEM.MISCINFO` with `SETUP` inside the p-System so that:

* screen width is 80 and height is 24,
* `HAS RANDOM CURSOR ADDRESSING` is true,
* GOTOXY uses sequences understood by the SBIOS escape parser (`ESC [ r;c H`).

Rename the result to `SYSTEM.MISCINFO` and include it in the build.

### Lobo MAX-80 default

The repository ships a default `SYSTEM.MISCINFO` at `files/SYSTEM.MISCINFO`
(the Apple II UCSD p-System IV payload, 192 bytes) configured for the Lobo
MAX-80 console. The Makefile defaults `MISCINFO` to that file, so a plain

```sh
make ASM=pasmo \
  INTERP=files/SYSTEM.INTERP \
  PASCAL=files/SYSTEM.PASCAL \
  image
```

includes it on the volume as `SYSTEM.MISCINFO` (file kind 5).  To use a
different console configuration, pass your own payload:

```sh
make ASM=pasmo \
  INTERP=files/SYSTEM.INTERP \
  PASCAL=files/SYSTEM.PASCAL \
  MISCINFO=files/MYCUSTOM.MISCINFO \
  image
```

## 3. Assemble and create the image

Either supported assembler can be selected with `ASM`; pasmo is the default:

```sh
make ASM=pasmo                       # or: make ASM=vasm
make ASM=pasmo \
  INTERP=files/SYSTEM.INTERP \
  PASCAL=files/SYSTEM.PASCAL \
  MISCINFO=files/SYSTEM.MISCINFO \
  image
make check
```

For vasm, build it with `make CPU=z80 SYNTAX=oldstyle` (the binary is
`vasmz80_oldstyle`). Custom paths can be passed as `PASMO=...` / `VASM=...`, or
as `ASMCMD=...` together with matching `PASMOFLAGS` / `VASMFLAGS`.

The sources are deliberately written in the common subset of both assemblers:
no `HIGH`/`LOW` or `<`/`>` byte operators and no `XOR`/`OR` expression keywords
(bitwise `|`, `~` and `>>` are used instead). To confirm this remains true:

```sh
make check-portability
```

## 4. Write media

```sh
gw write --drive 0 build/system.img
```

Or copy `build/system.img` to a Gotek/FlashFloppy USB stick.
