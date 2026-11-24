# Native UCSD p-System IV for the Lobo MAX-80
#
# Cross-build: assemble Z80 sources on the host, then create a bootable
# 512-byte-block p-System volume from the user-supplied adaptable-system files.

# Assembler selection: ASM=pasmo (default) or ASM=vasm.
# PASMO/PASMOFLAGS and VASM/VASMFLAGS can be overridden for custom builds,
# e.g. make ASM=vasm VASM=/opt/vasm/vasmz80_oldstyle
ASM        ?= pasmo
PASMO      ?= pasmo
PASMOFLAGS ?= --bin --include-dir asm/include
VASM       ?= vasmz80_oldstyle
VASMFLAGS  ?= -quiet -Fbin -I asm/include

ifeq ($(ASM),vasm)
ASMCMD     ?= $(VASM)
ASFLAGS    ?= $(VASMFLAGS)
ASSEMBLE    = $(ASMCMD) $(ASFLAGS) -o $@ $<
else ifeq ($(ASM),pasmo)
ASMCMD     ?= $(PASMO)
ASFLAGS    ?= $(PASMOFLAGS)
ASSEMBLE    = $(ASMCMD) $(ASFLAGS) $< $@
else
$(error Unknown ASM '$(ASM)' (use pasmo or vasm))
endif

PYTHON     ?= python3
BUILD      ?= build
CONFIG     ?= config/image.json
IMAGE      ?= $(BUILD)/system.img

# Required: binaries extracted from an adaptable p-System IV volume
# (see doc/BUILDING.md).  INTERP = SYSTEM.INTERP, PASCAL = SYSTEM.PASCAL.
# Defaults point at files/; the MBC2 DS2N20.DSK-extracted copies are
# provided as a convenient source (see files/README provenance in git log).
INTERP     ?= $(wildcard files/SYSTEM.INTERP)
PASCAL     ?= $(wildcard files/SYSTEM.PASCAL)
MISCINFO   ?= files/SYSTEM.MISCINFO

SOURCES  := asm/boot1.z80 asm/boot2.z80 asm/sbios.z80
INCLUDES := asm/include/max80.inc asm/include/sbios.inc asm/include/config.inc
BINS     := $(BUILD)/boot1.bin $(BUILD)/boot2.bin $(BUILD)/sbios.bin

.PHONY: all image check check-image check-portability smoke test clean

all: $(BINS)

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/%.bin: asm/%.z80 $(INCLUDES) | $(BUILD)
	$(ASSEMBLE)

image: $(BINS)
	@test -n "$(INTERP)" || { echo "ERROR: set INTERP=/path/to/SYSTEM.INTERP"; exit 1; }
	@test -n "$(PASCAL)" || { echo "ERROR: set PASCAL=/path/to/SYSTEM.PASCAL"; exit 1; }
	$(PYTHON) tools/ucsd_fs.py create \
		--output $(IMAGE) --blocks 1309 \
		--boot1 $(BUILD)/boot1.bin \
		--boot2 $(BUILD)/boot2.bin \
		--sbios $(BUILD)/sbios.bin \
		--sbios-block 10 \
		--file SYSTEM.INTERP=$(INTERP):5 \
		--file SYSTEM.PASCAL=$(PASCAL):5 \
		$(if $(MISCINFO),--file SYSTEM.MISCINFO=$(MISCINFO):5,)

check: $(BINS)
	$(PYTHON) tools/check_sources.py --build $(BUILD) --config $(CONFIG)

check-image: image
	$(PYTHON) tools/check_image.py --config $(CONFIG) --image $(IMAGE)

# Assemble every source with both supported assemblers and compare the output.
check-portability:
	@mkdir -p $(BUILD)/verify
	@set -e; for src in $(patsubst asm/%.z80,%,$(SOURCES)); do \
		$(PASMO) $(PASMOFLAGS) asm/$$src.z80 $(BUILD)/verify/$$src.pasmo.bin; \
		$(VASM) $(VASMFLAGS) -o $(BUILD)/verify/$$src.vasm.bin asm/$$src.z80 >/dev/null; \
		cmp $(BUILD)/verify/$$src.pasmo.bin $(BUILD)/verify/$$src.vasm.bin; \
		echo "OK  $$src: pasmo and vasm output identical"; \
	done

smoke: $(BINS)
	$(PYTHON) tools/smoke_max80.py --asm $(ASM)

test:
	$(PYTHON) -m unittest discover -s tests -v

clean:
	rm -rf $(BUILD)
