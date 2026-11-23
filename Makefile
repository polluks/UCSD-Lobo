# Native UCSD p-System IV for the Lobo MAX-80
#
# Cross-build: assemble Z80 sources on the host, then create a bootable
# 512-byte-block p-System volume from the user-supplied adaptable-system files.

PASMO      ?= pasmo
PYTHON     ?= python3
ASFLAGS    ?= --bin --include-dir asm/include
BUILD      ?= build
CONFIG     ?= config/image.json
IMAGE      ?= $(BUILD)/system.img

# Required: binaries extracted from an adaptable p-System IV volume
# (see doc/BUILDING.md).  INTERP = SYSTEM.INTERP, PASCAL = SYSTEM.PASCAL.
INTERP     ?=
PASCAL     ?=
MISCINFO   ?=

SOURCES  := asm/boot1.z80 asm/boot2.z80 asm/sbios.z80
INCLUDES := asm/include/max80.inc asm/include/sbios.inc asm/include/config.inc
BINS     := $(BUILD)/boot1.bin $(BUILD)/boot2.bin $(BUILD)/sbios.bin

.PHONY: all image check check-image test clean

all: $(BINS)

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/%.bin: asm/%.z80 $(INCLUDES) | $(BUILD)
	$(PASMO) $(ASFLAGS) $< $@

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

test:
	$(PYTHON) -m unittest discover -s tests -v

clean:
	rm -rf $(BUILD)
