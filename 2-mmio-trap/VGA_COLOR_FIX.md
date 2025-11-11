# Nyancat Color Palette Fix

## Problem

After implementing the unified Python script for nyancat animation compression, the generated animation displayed with incorrect colors. The nyancat body appeared blue instead of gray.

## Root Cause

The color character-to-palette index mapping in `scripts/gen-nyancat-data.py` was incorrect. The mapping was based on assumptions rather than the actual upstream klange/nyancat source code.

## Investigation

WebFetch was used to download and analyze the upstream nyancat.c source:
- URL: https://raw.githubusercontent.com/klange/nyancat/master/src/nyancat.c
- Found the authoritative character-to-color mapping in the main() function

## Character Set

Characters actually used in animation.c frames:
```
'#', '$', '%', '&', "'", '*', '+', ',', '-', '.', ';', '=', '>', '@'
```

Note: The original mapping incorrectly included `'0'` (zero) which doesn't appear in the upstream animation.

## Corrected Mapping

Based on upstream nyancat.c documentation:

| Character | Meaning | Palette Index | Color (6-bit RRGGBB) |
|-----------|---------|---------------|---------------------|
| `,` | Blue background | 0 | 0x01 (Dark blue) |
| `.` | White stars | 1 | 0x3F (White) |
| `'` | Black border | 2 | 0x00 (Black) |
| `@` | Tan poptart | 3 | 0x3E (Light pink/beige) |
| `$` | Pink poptart | 5 | 0x36 (Hot pink) |
| `-` | Red poptart | 6 | 0x30 (Red) |
| `>` | Red rainbow | 6 | 0x30 (Red) |
| `&` | Orange rainbow | 7 | 0x38 (Orange) |
| `+` | Yellow rainbow | 8 | 0x3C (Yellow) |
| `#` | Green rainbow | 9 | 0x0C (Green) |
| `=` | Light blue rainbow | 10 | 0x0B (Light blue) |
| `;` | Dark blue rainbow | 11 | 0x17 (Purple) |
| `*` | Gray cat face | 12 | 0x2A (Gray) |
| `%` | Pink cheeks | 4 | 0x3B (Pink) |

## Changes Made

### scripts/gen-nyancat-data.py

Updated `map_color_to_palette()` function with correct character mapping:

```python
color_map = {
    ',': 0,   # Dark blue background
    '.': 1,   # White (stars)
    "'": 2,   # Black (border)
    '@': 3,   # Tan/Light pink (poptart) -> Light pink/beige
    '$': 5,   # Pink poptart -> Hot pink
    '-': 6,   # Red poptart
    '>': 6,   # Red rainbow (same as red poptart)
    '&': 7,   # Orange rainbow
    '+': 8,   # Yellow rainbow
    '#': 9,   # Green rainbow
    '=': 10,  # Light blue rainbow
    ';': 11,  # Dark blue/Purple rainbow -> Purple
    '*': 12,  # Gray cat face
    '%': 4,   # Pink cheeks
}
```

Key corrections:
- Removed incorrect `'0': 9` mapping
- Added missing `'>': 6` mapping (Red rainbow)
- Fixed `'$'` from index 12 (Gray) to 5 (Hot pink)
- Fixed `'*'` mapping to correctly point to palette index 12 (Gray)
- Fixed `';'` from index 10 to 11 (Purple instead of Light blue)

## Verification

After regenerating nyancat-data.h with corrected mapping:
- Compression still achieves 87% reduction (49KB → 6.7KB)
- All 12 frames verify with pixel-perfect match
- Demo completes successfully with correct colors
- Nyancat cat body now displays in gray (palette[12]) instead of blue

## Build Workflow

```bash
cd 2-mmio-trap/csrc
make clean
make nyancat.asmbin  # Auto-generates nyancat-data.h with correct colors
cp nyancat.asmbin ../src/main/resources/
cd ..
make demo  # Displays animation with correct colors
```

## Date

2025-11-10
