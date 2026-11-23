;------------------------------------------------------------------------------
; sbios.inc -- UCSD p-System IV SBIOS ABI (Z80)
;
; The SBIOS is a table of 15 mandatory three-byte JP instructions at offsets
; 00H..2AH, followed by 13 optional extended entries at offsets 2DH..51H.
; Callers use CALL SBIOS_BASE+offset; every routine returns with RET.
;
; Parameters: B/C (16-bit values BC with B = high), C for single bytes/chars.
; IORESULT is returned in A: 0 = OK, 9 = offline, 1 = read error,
; 16 = write error.
;------------------------------------------------------------------------------

;--- Basic vector offsets ------------------------------------------------------

SBIOS_SYSINIT  EQU 00H
SBIOS_SYSHALT  EQU 03H
SBIOS_CONINIT  EQU 06H
SBIOS_CONSTAT  EQU 09H
SBIOS_CONREAD  EQU 0CH
SBIOS_CONWRIT  EQU 0FH
SBIOS_SETDSK   EQU 12H
SBIOS_SETTRK   EQU 15H
SBIOS_SETSEC   EQU 18H
SBIOS_SETBUFR  EQU 1BH
SBIOS_DSKREAD  EQU 1EH
SBIOS_DSKWRIT  EQU 21H
SBIOS_DSKINIT  EQU 24H
SBIOS_DSKSTRT  EQU 27H
SBIOS_DSKSTOP  EQU 2AH

;--- Extended vector offsets --------------------------------------------------

SBIOS_PRNINIT  EQU 2DH
SBIOS_PRNSTAT  EQU 30H
SBIOS_PRNREAD  EQU 33H
SBIOS_PRNWRIT  EQU 36H
SBIOS_REMINIT  EQU 39H
SBIOS_REMSTAT  EQU 3CH
SBIOS_REMREAD  EQU 3FH
SBIOS_REMWRIT  EQU 42H
SBIOS_USRINIT  EQU 45H
SBIOS_USRSTAT  EQU 48H
SBIOS_USRREAD  EQU 4BH
SBIOS_USRWRIT  EQU 4EH
SBIOS_CLKREAD  EQU 51H

;--- IORESULT values ----------------------------------------------------------

IO_OK          EQU 0
IO_OFFLINE     EQU 9
IO_READERR     EQU 1
IO_WRITEERR    EQU 16

;--- Directory entry layout (26 bytes) ----------------------------------------

DIR_ENTRY_SIZE EQU 26
DIR_ENTRIES    EQU 78
DIR_FIRSTBLK   EQU 0
DIR_PASTEND    EQU 2
DIR_KIND       EQU 4
DIR_NAME       EQU 6
DIR_LASTBYTES  EQU 22
DIR_DATE       EQU 24

;--- Character codes used by CONWRIT -----------------------------------------

CH_NUL         EQU 00H
CH_BS          EQU 08H
CH_TAB         EQU 09H
CH_LF          EQU 0AH
CH_DLE         EQU 10H
CH_CR          EQU 0DH
CH_ESC         EQU 1BH

;--- Macro: emit a three-byte JP vector ---------------------------------------

VECTOR MACRO target
        JP target
        ENDM
