# MyCPU Test Programs (2-mmio-trap)

This directory contains test programs for the MyCPU RISC-V processor with MMIO peripherals and trap handling support.

## Building Programs

All programs use a unified build process with shared initialization code:

```bash
make all       # Build all test programs
make update    # Copy binaries to ../src/main/resources/
make clean     # Remove build artifacts
```

## Available Programs

### Basic Tests
- **fibonacci.asmbin** - Recursive Fibonacci calculation
- **quicksort.asmbin** - Array sorting test
- **sb.asmbin** - Store byte operations test

### MMIO Peripheral Tests
- **irqtrap.asmbin** - Interrupt entry/exit test
- **uart.asmbin** - UART peripheral test
- **nyancat.asmbin** - VGA peripheral with 12-frame nyancat animation

## Program Details

### nyancat.asmbin - VGA Animation Demo (Opcode-RLE Compressed)

**Purpose**: Demonstrates VGA peripheral with indexed color mode and frame buffer animation using opcode-based RLE compression.

**Features**:
- 12-frame nyancat character animation (64×64 pixels per frame)
- 14-color custom palette (6-bit RRGGBB format)
- 4-bit indexed color mode (16 colors, packed 8 pixels per word)
- Continuous animation loop at ~20Hz
- **Opcode-RLE compression**: 86% data reduction (49KB → 6.7KB), 79% binary reduction (52KB → 11KB)

**Compression Format**:
```
0x0X = SetColor (current color = X, 0-13)
0x2Y = Repeat Y+1 times (1-16 pixels)
0x3Y = Repeat (Y+1)*16 times (16-256 pixels)
0xFF = EndOfFrame marker
```

**Memory Layout**:
- Code: ~1.5KB (VGA control + opcode-RLE decoder)
- Data: ~6.7KB (opcode-RLE compressed frames + palette)
- .bss: 4KB static frame buffer (decompression workspace)
- Stack: Grows down from 0x400000 (4MB)

**Build Configuration**:
- Uses minimal `init_minimal.S` (no trap handler)
- Stack pointer: 0x400000 (4MB)
- Optimization: `-O0` for predictable code layout
- Static buffer avoids stack overflow
- Runtime decompression: ~2ms per frame (negligible)

**Binary Size**:
- Total: 11KB (vs 52KB original, 79% reduction)
- All 12 frames verified pixel-perfect

**Testing**:
```bash
cd ..
make demo    # Runs VGA demo with SDL2 window
```

Expected output:
- SDL2 window opens (640×480)
- Nyancat animation displays with rainbow trail
- Press ESC or close window to exit

## Source Files

### Shared Infrastructure
- **init.S** - Common startup code with trap handler support
  - Initializes stack pointer to 0x10000000
  - Provides trap handler for interrupt/exception support
  - Includes helper functions: enable_interrupt, get_mtval, get_epc

- **link.lds** - Linker script defining memory layout
  - .text section starts at 0x1000
  - .data section aligned to 4KB boundary
  - .bss section starts at 0x100000

### Test Program Sources
- **nyancat.c** - VGA animation program
- **nyancat-data.h** - 12-frame animation data (auto-generated)
- **irqtrap.c** - Interrupt handling test
- **uart.c** - UART communication test
- **fibonacci.c** - Fibonacci calculation
- **quicksort.c** - Sorting algorithm
- **sb.S** - Assembly-level store byte test

### MMIO Header
- **mmio.h** - Memory-mapped I/O register definitions
  - Timer peripheral (0x20000000)
  - VGA peripheral (0x30000000)
  - UART peripheral (0x40000000)

## Build System

### Makefile Targets
```makefile
all:       # Build all binaries
update:    # Copy to resources directory
clean:     # Remove build artifacts
```

### Compilation Flags
- **ASFLAGS**: `-march=rv32i_zicsr -mabi=ilp32`
- **CFLAGS**: `-O0 -Wall -march=rv32i_zicsr -mabi=ilp32`
- **LDFLAGS**: `--oformat=elf32-littleriscv`

### Build Flow
```
1. Assemble init.S → init.o (shared by all C programs)
2. Compile <program>.c → <program>.o
3. Link <program>.o + init.o → <program>.elf
4. Extract binary sections → <program>.asmbin
```

## VGA Peripheral Specification

### Registers (Base: 0x30000000)
| Offset | Name | Description |
|--------|------|-------------|
| 0x00 | VGA_ID | Device ID (0x56474131 = "VGA1") |
| 0x04 | VGA_CTRL | Control register |
| 0x08 | VGA_STATUS | Status register |
| 0x10 | VGA_UPLOAD_ADDR | Frame buffer upload address |
| 0x14 | VGA_STREAM_DATA | Pixel data stream |
| 0x20-0x5C | VGA_PALETTE(0-15) | Palette entries (16 colors) |

### Pixel Format
- **Mode**: 4-bit indexed color
- **Packing**: 8 pixels per 32-bit word
- **Color depth**: 6-bit per palette entry (RRGGBB)
- **Frame size**: 64×64 pixels = 4096 pixels = 512 words

### Frame Upload Protocol
```c
// 1. Set upload address
vga_write32(VGA_UPLOAD_ADDR, (frame_index << 16) | 0);

// 2. Stream pixel data (512 words)
for (int i = 0; i < 512; i++) {
    uint32_t packed_pixels = pack8_pixels(&frame_data[i * 8]);
    vga_write32(VGA_STREAM_DATA, packed_pixels);
}
```

## Implementation Notes

The nyancat animation uses opcode-based RLE compression for efficient storage:
- **Encoder tool**: `../scripts/gen-nyancat-opcode-rle.py` (generates compressed data)
- **Decoder**: Embedded in `nyancat.c` (runtime decompression)
- **Compression ratio**: 13.7% (6,715 bytes from 49,152 bytes)
- **Quality**: Pixel-perfect lossless compression
- **Performance**: O(n) linear decompression, ~2ms per frame

## Toolchain Requirements

- **RISC-V GNU Toolchain**: `riscv-none-elf-*` tools
  - Default location: `~/rv/toolchain/bin/`
  - Override with `CROSS_COMPILE` environment variable

- **Architecture**: RV32I with Zicsr extension
- **ABI**: ILP32 (32-bit integers, longs, and pointers)

## Notes

### Special Build Process for Nyancat

**Why nyancat needs minimal init:**

Nyancat uses RLE-compressed animation data and minimal initialization for optimal memory usage. The program includes runtime decompression that requires:
- Minimal init without trap handlers (saves ~3KB)
- Stack at 0x400000 (4MB) for decompression buffer
- RLE data section with stable memory layout

**Build process:**
```bash
make nyancat.asmbin    # Automatically uses init_minimal.S
make update            # Copy to ../src/main/resources/
```

**Memory Layout:**
```
RLE-compressed nyancat (current):
  0x0000-0x000C: Minimal startup (12 bytes)
  0x000C-0x1500: Code (VGA control + RLE decompression ~1.3KB)
  0x1500+:       RLE data (6.25KB compressed frames)
  Stack:         0x400000 (4MB, includes 4KB decompression buffer)

Total binary: ~10KB (81% reduction from 52KB)
```

**Opcode-RLE Compression Benefits:**
- Data size: 49KB → 6.7KB (86% reduction)
- Binary size: 52KB → 11KB (79% reduction)
- Runtime overhead: ~2ms decompression per frame (negligible)
- Visual quality: Lossless (100% identical to original)
- Stack safety: Static buffer prevents overflow

### Stack Configuration
- Stack starts at 0x10000000 (256MB)
- Grows downward toward program code/data
- Sufficient space for all test programs
- Trap handler uses stack for context save/restore

### Memory Safety
Programs run from 0x1000, stack from 0x10000000, providing ~256MB separation. The trap handler saves all registers (128 bytes) on stack, so minimum 256 bytes stack space recommended.
