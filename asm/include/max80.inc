;------------------------------------------------------------------------------
; max80.inc -- Lobo MAX-80 hardware register definitions
;
; All MAX-80 peripherals are MEMORY MAPPED inside a relocatable 4 KB block.
; There are no Z80 IN/OUT port numbers for the on-board devices.
;
; The block base is selected by bits 7..4 of VLATCH.  Reset leaves VLATCH=0,
; so the block starts at 0000H during boot.  The final SBIOS moves it to
; F000H (the convention used by the original Lobo CP/M BIOS sources).
;
; Sources: Lobo MAX-80 Technical Reference Manual, XPORTS.LIB, MAXROM13.MAC,
;          XFDC.MAC, XDATA.MAC (tim-mann.org/max80).
;------------------------------------------------------------------------------

; Base of the relocated 4 KB I/O block (x = F).
IO_BASE      EQU 0F000H

; Base of the I/O block while the boot ROM is in control (x = 0).
IO_BOOT      EQU 00000H

;--- Offsets inside the 4 KB I/O block ----------------------------------------

IO_SWAP1K    EQU 0000H       ; ROM/RAM/video/font 1 KB window
IO_RAM400    EQU 0400H       ; 768 bytes of bank A RAM
IO_SLORAM    EQU 0700H       ; 208 bytes of bank A RAM
IO_BAUDA     EQU 07D0H       ; SIO channel A baud latch
IO_BAUDB     EQU 07D4H       ; SIO channel B baud latch
IO_MLATCH    EQU 07D8H       ; floppy mode latch
IO_VLATCH    EQU 07DCH       ; video / memory control latch
IO_CRTREG    EQU 07E0H       ; write: CRTC register number; read: SYSCLR
IO_CRTBYT    EQU 07E1H       ; write: CRTC register data; read: SYSFLG
IO_SIODA     EQU 07E4H       ; SIO channel A data
IO_SIOCA     EQU 07E5H       ; SIO channel A control/status
IO_SIODB     EQU 07E6H       ; SIO channel B data
IO_SIOCB     EQU 07E7H       ; SIO channel B control/status
IO_PSTAT     EQU 07E8H       ; read: printer status
IO_PDATA     EQU 07E8H       ; write: printer data
IO_FSTAT     EQU 07ECH       ; read: FDC status (inverted)
IO_FCTRL     EQU 07ECH       ; write: FDC command (inverted)
IO_FTRACK    EQU 07EDH       ; FDC track (inverted)
IO_FSECTOR   EQU 07EEH       ; FDC sector (inverted)
IO_FDATA     EQU 07EFH       ; FDC data (inverted)
IO_UDATA     EQU 07F0H       ; UVC hard disk data
IO_UDATAHS   EQU 07F1H       ; UVC hard disk data, high speed
IO_USTAT     EQU 07F4H       ; read: UVC status
IO_UCTRL     EQU 07F4H       ; write: UVC control
IO_DIPSW     EQU 07F8H       ; read: DIP switches
IO_BEEP      EQU 07F8H       ; write: beeper
IO_PIODA     EQU 07FCH       ; PIO port A data / 32 KB chunk selector
IO_PIOCA     EQU 07FDH       ; PIO port A control
IO_PIODB     EQU 07FEH       ; PIO port B data / RTC
IO_PIOCB     EQU 07FFH       ; PIO port B control
IO_MATRIX    EQU 0800H       ; keyboard matrix (A0..A7 = row, D0..D7 = columns)
IO_RAM900    EQU 0900H       ; 768 bytes of bank A RAM
IO_VIDEO     EQU 0C00H       ; first 1 KB of video RAM

;--- Absolute addresses in the final (relocated) configuration ----------------

BAUDA        EQU IO_BASE+IO_BAUDA        ; F7D0H
BAUDB        EQU IO_BASE+IO_BAUDB        ; F7D4H
VLATCH       EQU IO_BASE+IO_VLATCH       ; F7DCH
MLATCH       EQU IO_BASE+IO_MLATCH       ; F7D8H
CRTREG       EQU IO_BASE+IO_CRTREG       ; F7E0H
CRTBYT       EQU IO_BASE+IO_CRTBYT       ; F7E1H
SIODA        EQU IO_BASE+IO_SIODA        ; F7E4H
SIOCA        EQU IO_BASE+IO_SIOCA        ; F7E5H
SIODB        EQU IO_BASE+IO_SIODB        ; F7E6H
SIOCB        EQU IO_BASE+IO_SIOCB        ; F7E7H
PSTAT        EQU IO_BASE+IO_PSTAT        ; F7E8H
PDATA        EQU IO_BASE+IO_PDATA        ; F7E8H
FSTAT        EQU IO_BASE+IO_FSTAT        ; F7ECH
FCTRL        EQU IO_BASE+IO_FCTRL        ; F7ECH
FTRACK       EQU IO_BASE+IO_FTRACK       ; F7EDH
FSECTOR      EQU IO_BASE+IO_FSECTOR      ; F7EEH
FDATA        EQU IO_BASE+IO_FDATA        ; F7EFH
DIPSW        EQU IO_BASE+IO_DIPSW        ; F7F8H
BEEP         EQU IO_BASE+IO_BEEP         ; F7F8H
PIODA        EQU IO_BASE+IO_PIODA        ; F7FCH
PIOCA        EQU IO_BASE+IO_PIOCA        ; F7FDH
PIODB        EQU IO_BASE+IO_PIODB        ; F7FEH
PIOCB        EQU IO_BASE+IO_PIOCB        ; F7FFH
MATRIX       EQU IO_BASE+IO_MATRIX       ; F800H
VIDEO        EQU IO_BASE+IO_VIDEO        ; FC00H
SWAP1K       EQU IO_BASE+IO_SWAP1K       ; F000H

; Addresses used during stage 1, before the I/O block is relocated.
VLATCH_BOOT  EQU IO_BOOT+IO_VLATCH        ; 07DCH
MLATCH_BOOT  EQU IO_BOOT+IO_MLATCH        ; 07D8H
FSTAT_BOOT   EQU IO_BOOT+IO_FSTAT         ; 07ECH
FCTRL_BOOT   EQU IO_BOOT+IO_FCTRL         ; 07ECH
FTRACK_BOOT  EQU IO_BOOT+IO_FTRACK        ; 07EDH
FSECTOR_BOOT EQU IO_BOOT+IO_FSECTOR       ; 07EEH
FDATA_BOOT   EQU IO_BOOT+IO_FDATA         ; 07EFH
PIODA_BOOT   EQU IO_BOOT+IO_PIODA         ; 07FCH

;--- VLATCH bits ---------------------------------------------------------------

; Bits 7..4: I/O block base nibble (x).  0 = boot, F = CP/M/SBIOS convention.
VL_X_SHIFT   EQU 4
VL_X_BOOT    EQU 000H
VL_X_F       EQU 0F0H

; Bit 3: double-width characters.
VL_WIDE      EQU 008H

; Bits 2..0: SWAP1K source.
VL_SWAP_ROM  EQU 000H       ; boot ROM (duplicate 512 bytes)
VL_SWAP_RAM  EQU 001H       ; bank A RAM peek-through -- use to hide boot ROM
VL_SWAP_VID2 EQU 002H       ; second half of video RAM (also 003H)
VL_SWAP_FONT EQU 004H       ; character generator RAM (004H..007H)

; Final value: I/O at F000H, boot ROM hidden, ordinary RAM at 0000H..03FFH.
VLATCH_FINAL EQU VL_X_F OR VL_SWAP_RAM

;--- PIODA: 32 KB chunk selection ---------------------------------------------

; bits 7..6 select the chunk mapped at 8000H..FFFFH
; bits 5..4 select the chunk mapped at 0000H..7FFFH
;   00 = bank A chunk 1, 01 = bank A chunk 2
;   10 = bank B chunk 1, 11 = bank B chunk 2
PIO_LOW_A1   EQU 000H
PIO_LOW_A2   EQU 010H
PIO_LOW_B1   EQU 020H
PIO_LOW_B2   EQU 030H
PIO_HIGH_A1  EQU 000H
PIO_HIGH_A2  EQU 040H
PIO_HIGH_B1  EQU 080H
PIO_HIGH_B2  EQU 0C0H

; Contiguous 64 KB of bank A RAM: A1 at 0000H, A2 at 8000H.
PIO_LINEAR64 EQU PIO_LOW_A1 OR PIO_HIGH_A2      ; = 40H

;--- MLATCH bits ---------------------------------------------------------------

ML_NMI       EQU 080H       ; 1 = allow NMI
ML_DD        EQU 040H       ; 1 = double density
ML_8INCH     EQU 020H       ; 1 = 8-inch drive, 0 = 5-inch
ML_SIDE      EQU 010H       ; side select (0 = side 0, 1 = side 1)
ML_DS4       EQU 008H
ML_DS3       EQU 004H
ML_DS2       EQU 002H
ML_DS1       EQU 001H

; Every FDC register access uses the complement of the desired byte.
FD_READ      EQU 082H
FD_READ_S1   EQU 08AH
FD_WRITE     EQU 0A2H
FD_WRITE_S1  EQU 0AAH
FD_SEEK      EQU 018H
FD_SEEK_SLOW EQU 01BH         ; used by the Lobo boot ROM; refreshes motors
FD_RESTORE   EQU 008H
FD_STEP_OUT  EQU 068H
FD_READ_ADDR EQU 0C4H
FD_FORCE     EQU 0D0H

; FSTAT bits, after complementing the byte read from the register.
FS_NOTREADY  EQU 080H
FS_WPROT     EQU 040H
FS_WFAULT    EQU 020H
FS_NOTFOUND  EQU 010H
FS_CRC       EQU 008H
FS_LOST      EQU 004H
FS_DRQ       EQU 002H
FS_BUSY      EQU 001H

;--- SYSCLR / SYSFLG bits ------------------------------------------------------

SYS_HEARTBEAT EQU 080H
SYS_DISPTMG   EQU 040H
SYS_MOTORS    EQU 020H
SYS_8IN_SINGLE EQU 010H

;--- CRTC initialization (80 x 24, 9 scan lines per row) ----------------------

CRT_COLS     EQU 80
CRT_ROWS     EQU 24
CRT_CELLS    EQU CRT_COLS*CRT_ROWS            ; 1920 bytes -> needs both 1 KB halves
CRT_VISIBLE1 EQU 400H                         ; cells in the first video RAM half

;--- Keyboard matrix row strobes ----------------------------------------------

KB_CTRL      EQU 080H
KB_SHIFT     EQU 001H
KB_ROWS      EQU 8

;--- Baud rate generator codes (COM8116) --------------------------------------

BAUD_300     EQU 6
BAUD_1200    EQU 8
BAUD_2400    EQU 10
BAUD_4800    EQU 12
BAUD_9600    EQU 14
BAUD_19200   EQU 15

;--- Boot ROM entry points -----------------------------------------------------

; HL = destination, DE = track, B = first sector, C = last sector,
; A = head (0-based).  AF' must be preserved by the caller.
ROM_DISKREAD EQU 0003H
BOOT_LOAD    EQU 0400H
BOOT_STACK   EQU 06FFH
