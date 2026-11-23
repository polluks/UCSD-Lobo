# UCSD p-System IV.0 (Full Adaptable) for Lobo MAX-80

Native port of the **SofTech Microsystems UCSD p-System IV.0** (*Full Adaptable System*) for the **Lobo MAX-80** microcomputer — booting directly from floppy disk or SASI hard drive **without CP/M**.

---

## 1. Overview & Architecture

The **Full Adaptable p-System IV** separates the hardware-independent p-Machine interpreter and operating system (`SYSTEM.PASCAL`) from hardware-specific drivers via the **SBIOS** (*Simplified Basic Input/Output System*).

On the Lobo MAX-80 (Z80-B @ 5.07 MHz, 64 KB / 128 KB RAM), the system runs in the linear **64 KB RAM mode** (bypassing the LDOS ROM/memory map) and directly accesses the onboard peripherals without CP/M overhead or sector deblocking.

### System Requirements
* **Hardware:** Lobo MAX-80 (64 KB RAM minimum; 128 KB supported for optional RAM disk)
* **Storage:** 5.25" or 8" floppy drive (WD179x FDC) or SASI hard drive, formatted with **512-byte physical sectors** (matching native UCSD 512-byte blocks)
* **Console:** Built-in `80×24` monochrome CRT (HD46505 CRTC) and integrated keyboard

---

## 2. Memory Map & Boot Process

Upon reset, the MAX-80 boot ROM maps into low memory and loads **Track 0, Sector 1** from the selected boot drive.

```text
+-----------------------------------+ FFFFh

|         SBIOS & Drivers           |  <- Hardware drivers (CRTC, KBD, FDC, SIO/PIO)
+-----------------------------------+ ~F000h (adjustable)

|     UCSD p-System Interpreter     |  <- SYSTEM.PASCAL & OS Kernel
|         & OS Heap / Stack         |
+-----------------------------------+

|                                   |
|     p-Code Application Space      |  <- User programs, compiler, editor
|                                   |
+-----------------------------------+ 0000h (Full 64 KB RAM mode active)
```

### Two-Stage Bootstrap
1. **Primary Bootstrap (Track 0, Sector 1):**
   * Switches the MAX-80 MMU into the **linear 64 KB RAM configuration** (disabling boot ROM overlay).
   * Loads the *Secondary Bootstrap* from the remaining reserved boot blocks on Track 0.
2. **Secondary Bootstrap (Track 0, Sectors 2+):**
   * Performs minimal hardware initialization (Z80-PIO, CTC, SIO, CRTC).
   * Loads the compiled **SBIOS** into high RAM.
   * Locates `SYSTEM.PASCAL` on the UCSD volume, loads the p-Machine interpreter into memory, and jumps to the `SYSINIT` entry point of the SBIOS.

---

## 3. Native MAX-80 SBIOS Implementation

The SBIOS jump table maps UCSD p-System logical I/O calls directly to the Lobo MAX-80 hardware controllers:

| SBIOS Vector | Target Hardware | Description |
| :--- | :--- | :--- |
| `SYSINIT` / `SYSHALT` | MMU, Z80-PIO, CTC, SIO | Initializes interrupt vectors, peripherals, and 64 KB RAM banking. |
| `CONSTAT` / `CONIN` | Keyboard Matrix / Z80-PIO | Polls keyboard matrix, decodes ASCII + control keys, handles auto-repeat. |
| `CONOUT` | HD46505 CRTC & Video RAM | Drives the `80×24` memory-mapped display; translates terminal escape codes (e.g., ADM-3A / ANSI) for cursor positioning (`GOTOXY`), clear screen, and scrolling. |
| `DISKREAD` / `DISKWRITE` | WD1793 / WD1797 FDC (or SASI) | Reads/writes native 512-byte UCSD blocks directly, translating linear block numbers into physical Track/Side/Sector coordinates. |
| `PRINTER` | Z80-PIO / Z80-SIO | Outputs characters to the parallel Centronics port or serial RS-232 port. |
| `AUXIN` / `AUXOUT` | Z80-SIO | Serial communication for `REMIN:` / `REMOUT:` devices. |

*(Optional)* If **128 KB RAM** is installed, the secondary 64 KB bank can be exposed as a fast block device (`#9:` / `#10:`) inside `DISKREAD`/`DISKWRITE` for faster UCSD Pascal compilation.

---

## 4. Build & Installation Workflow

Because building a standalone adaptable system requires running the UCSD system utilities (`SETUP`, `LINKER`, `SYSGEN`), use a cross-build workflow on a modern PC:

### Step 1: Prepare the Base System (Emulator)
1. Set up **z80pack** (`cpmsim`) with the **UCSD p-System IV.0 Adaptable** disk images.
2. Run `SETUP` inside the p-System to configure `SYSTEM.MISCINFO` with the control codes matching your MAX-80 `CONOUT` terminal emulation (screen dimensions: `80×24`, `GOTOXY` sequence, erase functions).
3. Link the p-Machine interpreter with your target memory configuration.

### Step 2: Assemble Bootloaders & SBIOS
1. Adapt the hardware routines (CRTC driver, keyboard scanner, WD179x FDC routines) from the original Lobo MAX-80 BIOS/ROM sources to match the **UCSD SBIOS jump table**.
2. Assemble `BOOT1.Z80` (Primary), `BOOT2.Z80` (Secondary), and `SBIOS.Z80` using a Z80 cross-assembler (e.g., `zmac` or `pasmo`).

### Step 3: Create the Bootable Disk Image
1. Inject the assembled `BOOT1` and `BOOT2` binaries into the reserved boot blocks (Block 0–1) of your UCSD system volume image.
2. Place the compiled `SBIOS` binary at its designated block/memory offset.
3. Write the resulting disk image to a physical 5.25"/8" floppy using a **Greaseweazle**, or load it directly via a **Gotek / FlashFloppy** drive emulator connected to the MAX-80.

---

## 5. References & Resources

* **SofTech Microsystems:** *Adaptable p-System IV.0 Installation Guide* (SBIOS specification, jump table offsets, and bootstrap requirements)
* **Lobo Systems:** *MAX-80 Operation Manual* & original BIOS/ROM source listings (Tim Mann's MAX-80 Archive: `tim-mann.org/max80`)
* **Emulation & Tools:**
  * `z80pack` – Z80 emulator and UCSD p-System IV.0 disk images
  * `EmulatorKit` – Open-source Lobo MAX-80 hardware emulator for testing
