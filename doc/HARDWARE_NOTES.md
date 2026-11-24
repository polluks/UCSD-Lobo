# Hardware assumptions and open items

The port is based on the original Lobo MAX-80 ROM/BIOS sources and Technical
Reference Manual. The following facts are considered verified:

* Peripherals live in a relocatable 4 KB **memory-mapped** block; there are no
  on-board Z80 I/O ports. The final map uses `x = F` (`F000H..FFFFH`).
* `VLATCH` (`F7DCH`) bit 7..4 selects the block base; bits 2..0 select the
  SWAP1K source. `F1H` relocates the block and replaces the boot ROM window
  with bank A RAM.
* `PIODA` (`F7FCH`) value `40H` maps bank A chunk A1 at `0000H` and A2 at
  `8000H`, giving contiguous 64 KB RAM.
* The boot ROM loads sector 0 to `0400H`; its disk-read entry is at `0003H`
  (HL = destination, DE = track, B..C = sectors, A = head, AF' = drive code).
* FDC registers `F7ECH..F7EFH` are complemented on every access.
* CRTC registers are written through `F7E0H`/`F7E1H`; the screen is 80×24.
* The keyboard is an 8×8 matrix at `F800H`.
* No Z80 CTC is fitted.

Items that still need validation on physical hardware:

1. **Sector numbering.** The boot ROM tries sectors 0 and 1, so physical
   sectors are treated as 0-based (`PHYS_SECTOR_BIAS = 1` converts the
   p-System's 1-based sector numbers). Confirm with a real formatted disk.
2. **Density and drive type.** The SBIOS selects drive 1 in double density
   with `MLATCH = ML_DS1 | ML_DD`. Single-sided 17×512 media is assumed.
3. **Side select.** MLATCH bit 4 is treated as a binary side select; Lobo's
   manual and BIOS comments use slightly different wording.
4. **Timing.** Motor-refresh and FDC busy/DRQ polling loops are conservative;
   fast 8-inch or hard-disk operation may need tuning.
5. **Escape sequences.** `CONWRIT` implements the subset of ADM-3A/ANSI codes
   typically emitted by `SYSTEM.MISCINFO`. Check your MISCINFO settings.  The
   implemented set is: `ESC H` / `ESC [ H` (home), `ESC J` / `ESC [ J` (clear
   screen), `ESC [ r;c H` (GOTOXY), `ESC [ J/K` (erase), and `ESC [ A/B/C/D`
   (cursor movement).  Other final bytes (for example a bare `ESC E`) are not
   implemented.  `ETX` (end-of-text/accept, `CRTINFO.ETX`) is likewise not handled
   by the console layer yet.

No physical MAX-80 or p-System disk image was available during development,
so nothing in this repository has been validated on real hardware.
