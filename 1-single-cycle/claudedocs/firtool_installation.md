# Firtool Installation Guide

## Current Situation

Verilator builds for MyCPU require `firtool` (CIRCT FIRRTL-to-Verilog compiler) which is not currently installed on this system.

### Error Message
```
[error] circt.stage.phases.Exceptions$FirtoolNonZeroExitCode: firtool returned a non-zero exit code.
[error] Note that this version of Chisel (3.6.1) was published against firtool version 1.37.0.
[error] ExitCode: -1
```

Exit code -1 indicates the `firtool` binary is missing or not in PATH.

## Installation Options

### Option 1: Homebrew (Recommended)

The simplest approach is to try installing CIRCT via Homebrew:

```bash
# Try tapping LLVM repository first
brew tap llvm/llvm

# Then install CIRCT (which includes firtool)
brew install circt
```

If that doesn't work, CIRCT may not be available in Homebrew for ARM64 macOS yet.

### Option 2: Manual Binary Download

1. Visit: https://github.com/llvm/circt/releases
2. Find the latest release (currently 1.136.0 as of Nov 2025)
3. Download the appropriate binary for macOS ARM64
4. Extract and add to PATH:

```bash
# Download (replace URL with correct asset URL from GitHub)
cd /tmp
curl -L -o circt.tar.gz [DOWNLOAD_URL]

# Extract
tar -xzf circt.tar.gz

# Create local bin directory if needed
mkdir -p ~/bin

# Copy firtool to local bin
cp circt-*/bin/firtool ~/bin/

# Add to PATH in your shell RC file (~/.zshrc or ~/.bashrc)
export PATH="$HOME/bin:$PATH"

# Reload shell configuration
source ~/.zshrc  # or source ~/.bashrc
```

### Option 3: Build from Source

If pre-built binaries aren't available:

```bash
git clone https://github.com/llvm/circt.git
cd circt
mkdir build && cd build
cmake -G Ninja .. -DLLVM_ENABLE_PROJECTS=mlir -DLLVM_TARGETS_TO_BUILD="host"
ninja
ninja install  # Or copy bin/firtool to ~/bin/
```

## Verification

After installation, verify firtool is accessible:

```bash
which firtool
firtool --version
```

Expected output should show firtool version (ideally 1.37.0 for Chisel 3.6.1, but newer versions should work).

## Alternative: Use Legacy FIRRTL Backend

If firtool installation is problematic, you could potentially configure Chisel to use the older Scala-based FIRRTL compiler instead of CIRCT, though this may require build.sbt modifications and is not the recommended path forward.

## Current Status

- Tests work fine with ChiselTest (no Verilog generation needed)
- RISCOF compliance tests work with ChiselTest
- Only `make verilator` target is blocked by missing firtool
- All Scala compilation and unit testing workflows function normally

## Why systemverilog vs verilog?

Both `--target systemverilog` and `--target verilog` are valid CIRCT targets:
- `systemverilog`: Modern SystemVerilog output (CIRCT default)
- `verilog`: Plain Verilog output (more conservative)

Both work with Verilator. The choice doesn't matter for this project - either generates `.v` files that Verilator can process.

## Current Configuration

All three projects (1-single-cycle, 2-mmio-trap, 3-pipeline) are configured with:
```scala
Array("--target", "verilog", "--target-dir", "verilog/verilator")
```

This will generate plain Verilog files once firtool is available.
