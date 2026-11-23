;------------------------------------------------------------------------------
; config.inc -- image layout and load addresses shared by all bootstrap stages
;
; These values must agree with config/image.json and with the SYSGEN output of
; the adaptable p-System used to build the base image.
;------------------------------------------------------------------------------

;--- Physical disk layout ------------------------------------------------------

; The MAX-80 boot ROM works in terms of physical sectors starting at 0.
; The 512-byte-sector format has 17 sectors per track, so one UCSD logical
; block maps directly to one physical sector.
SECTORS_PER_TRACK  EQU 17
FIRST_PHYS_SECTOR  EQU 0                 ; boot ROM sector numbering starts at 0
HEADS              EQU 1                 ; single-sided volume
TRACKS_PER_DISK    EQU 77

; The p-System numbers sectors from 1; the MAX-80 FDC registers use 0-based
; sector numbers (as evidenced by the boot ROM trying sectors 0 and 1).
PHYS_SECTOR_BIAS   EQU 1

;--- Stage 1 (primary bootstrap) ----------------------------------------------

BOOT2_TRACK        EQU 0
BOOT2_FIRST_SECTOR EQU 1
BOOT2_SECTORS      EQU 4                  ; boot2 may occupy up to 2 KB
BOOT2_LOAD         EQU 0D000H

;--- Stage 2 (secondary bootstrap) --------------------------------------------

DIR_BLOCK          EQU 2                  ; first block of the p-System directory
DIR_BLOCKS         EQU 4                  ; 78 entries x 26 bytes
SBIOS_BLOCK        EQU 10                 ; first UCSD block of sbios.bin
SBIOS_BLOCKS       EQU 8                  ; reserved extent (4 KB)

;--- Memory layout ------------------------------------------------------------

STACK_TOP          EQU 0CFF0H             ; below boot2 at D000H
DIR_BUFFER         EQU 0C000H             ; 2 KB directory buffer
SBIOS_ORG          EQU 0E000H             ; SBIOS vector table (below I/O block)
INTERP_LOAD        EQU 0100H              ; must be page-aligned (low byte 00)
INTERP_ENTRY       EQU 0100H
RAM_LOW            EQU 0100H
RAM_HIGH           EQU SBIOS_ORG-2        ; DFFEH, word-aligned

;--- Boot parameter block (pushed by stage 2) ---------------------------------

BOOT_TRACKS        EQU TRACKS_PER_DISK
BOOT_SECTORS       EQU SECTORS_PER_TRACK
BOOT_BYTES         EQU 512
BOOT_INTERLEAVE    EQU 1
BOOT_FIRST_PASCAL  EQU 1
BOOT_SKEW          EQU 0
BOOT_MAX_SECTORS   EQU SECTORS_PER_TRACK
BOOT_MAX_BYTES     EQU 512
