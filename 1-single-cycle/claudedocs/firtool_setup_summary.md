# Firtool Installation Complete

## Installation Summary

Successfully installed `firtool` version 1.136.0 to enable Verilator builds.

### Installation Details

- **Version**: CIRCT firtool-1.136.0 (LLVM 22.0.0git)
- **Location**: `~/.local/bin/firtool`
- **Platform**: macOS ARM64 (using x64 binary via Rosetta 2)
- **Source**: https://github.com/llvm/circt/releases/tag/firtool-1.136.0

### Changes Made

1. **Downloaded and installed firtool** to `~/.local/bin/`
2. **Updated all Makefiles** to include firtool in PATH:
   - `1-single-cycle/Makefile`
   - `2-mmio-trap/Makefile`
   - `3-pipeline/Makefile`

3. **Updated Top.scala files** for CIRCT compatibility:
   - Changed from deprecated `-X verilog` to `--target verilog`
   - All three projects now use modern CIRCT command-line options

### Verilator Build Process

The `make verilator` target now works as follows:

```makefile
verilator:
	PATH=$$HOME/.local/bin:$$PATH sbt "runMain board.verilator.VerilogGenerator"
	cd verilog/verilator && verilator --trace --exe --cc sim.cpp Top.v && make -C obj_dir -f VTop.mk
```

This ensures firtool is in PATH during Verilog generation.

### Usage

From any project directory (1-single-cycle, 2-mmio-trap, or 3-pipeline):

```bash
# Generate Verilog and build Verilator simulator
make verilator

# Run simulation
make sim SIM_ARGS="-instruction src/main/resources/fibonacci.asmbin"
```

### Verification

Test firtool installation:
```bash
~/.local/bin/firtool --version
# Output: CIRCT firtool-1.136.0
```

### Notes

- **No ARM64 native build**: CIRCT doesn't provide ARM64 binaries, so we use the x64 build which runs via Rosetta 2
- **Version mismatch warning**: Chisel 3.6.1 was built against firtool 1.37.0, but 1.136.0 (latest) works fine and is backward compatible
- **PATH configuration**: The Makefiles automatically add `~/.local/bin` to PATH, so no shell configuration changes are needed

### Alternative: Manual PATH Setup

If you prefer to add firtool to your shell PATH permanently:

```bash
# Add to ~/.zshrc or ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"

# Reload shell
source ~/.zshrc  # or source ~/.bashrc
```

Then the Makefile PATH prefix becomes redundant but harmless.

### Automated Installation Script

For future reference or other machines, an automated installation script is available at:
`scripts/install-firtool.sh`

The script handles:
- Platform detection (macOS ARM64/x64, Linux x64)
- Downloading correct CIRCT release
- Installing to `~/.local/bin`
- Verification and PATH instructions

## Status

✅ Firtool installed and working
✅ All Makefiles updated
✅ All Top.scala files updated for CIRCT
✅ Verilator builds are now functional

The complete toolchain is now ready:
- Chisel 3.6.1 → FIRRTL → firtool (CIRCT) → Verilog → Verilator → C++ simulator
