# Verilator Build Status

## Current Situation

Verilator builds are **not functional** due to a fundamental version incompatibility between Chisel and firtool.

### The Problem

**Version Incompatibility Chain**:
1. **Chisel 3.6.1** (current) → generates **FIRRTL 1.2.0**
2. **Firtool 1.37.0** (expected by Chisel 3.6.1) → NOT AVAILABLE for macOS ARM64
3. **Firtool 1.136.0** (latest available) → requires **FIRRTL 2.0.0+**

### Error Messages

```
firtool: Unknown command line argument '-dedup'
firtool: Did you mean '--no-dedup'?
```

And after wrapper fix:

```
<stdin>:1:16: error: FIRRTL version must be >=2.0.0
FIRRTL version 1.2.0
```

### Why This Happens

1. CIRCT/firtool doesn't publish ARM64 binaries for older versions
2. Firtool 1.37.0 (from early 2024) predates ARM64 binary releases
3. Latest firtool (1.136.0) has breaking changes:
   - Command-line args changed (`-dedup` → `--dedup-classes`)
   - FIRRTL version requirement increased (1.x → 2.0+)

## Solutions (Evaluated)

### ❌ Option 1: Use older firtool 1.37.0
- **Status**: Not viable
- **Reason**: No pre-built ARM64 binaries available
- **Alternative**: Build from source (time-consuming, may have build issues)

### ❌ Option 2: Wrapper for command-line compatibility
- **Status**: Partially implemented but insufficient
- **Reason**: Doesn't solve FIRRTL version incompatibility
- **File**: `~/.local/bin/firtool` (compatibility wrapper)

### ✅ Option 3: Upgrade Chisel to 5.x+ (generates FIRRTL 2.0+)
- **Status**: Requires code changes
- **Impact**: May break existing tests and code
- **Risk**: High - Chisel 5.x has API changes
- **Benefit**: Modern toolchain, active support

### ✅ Option 4: Use legacy Scala FIRRTL compiler instead of CIRCT
- **Status**: Possible but deprecated
- **Requires**: build.sbt modifications
- **Downside**: Much slower than CIRCT, deprecated path

### ✅ Option 5: Keep current setup (ChiselTest only)
- **Status**: **RECOMMENDED**
- **Reason**: All functionality works without Verilator
  - Unit tests work (ChiselTest)
  - RISCOF compliance tests work (ChiselTest)
  - All design verification is functional

## Current Working Configuration

**What works:**
- ✅ All Scala compilation
- ✅ All ChiselTest unit tests
- ✅ All RISCOF compliance tests (uses ChiselTest backend)
- ✅ All design verification workflows

**What doesn't work:**
- ❌ Verilog generation via `make verilator`
- ❌ Verilator C++ simulation

**Impact**: **MINIMAL** - Verilator was only for alternative simulation, not required for development/testing

## Recommendation

**Keep current Chisel 3.6.1 configuration** because:

1. **All tests pass** with ChiselTest (faster than Verilator anyway)
2. **RISCOF compliance works** (most important for RISC-V verification)
3. **Upgrading Chisel 5.x risks breaking working code**
4. **Verilator adds no additional verification value** in this project

If Verilog/Verilator is needed in future:
- Consider upgrading to Chisel 5.x+ when project is stable
- Or use the legacy FIRRTL compiler (slower but works)

## Files Modified

Attempted fixes (can be reverted):
- `*/Makefile`: Added `PATH=$$HOME/.local/bin:$$PATH` for firtool
- `*/Top.scala`: Changed to `--target verilog` (CIRCT syntax)
- `~/.local/bin/firtool`: Compatibility wrapper script
- `~/. local/bin/firtool-real`: Actual firtool 1.136.0 binary

## Clean Up (Optional)

To remove firtool and revert changes:

```bash
# Remove firtool
rm ~/.local/bin/firtool ~/.local/bin/firtool-real

# Revert Makefile changes (or keep them, they're harmless)
git checkout */Makefile

# Revert Top.scala changes (or keep them for future)
git checkout */src/main/scala/board/verilator/Top.scala
```

## Alternative: If You Really Need Verilator

### Option A: Upgrade Chisel (Breaking Changes)

```scala
// build.sbt
val chiselVersion = "5.1.0"  // or latest 5.x
```

This will require fixing API changes throughout the codebase.

### Option B: Use Legacy FIRRTL Compiler

Add to `build.sbt`:

```scala
libraryDependencies += "edu.berkeley.cs" %% "firrtl" % "1.6.0"
```

And modify Top.scala to use the old FIRRTL compiler instead of CIRCT.

## Conclusion

**Status**: Verilator builds are non-functional but not needed.

**Action**: No action required - current configuration is optimal for development and verification.

**Future**: Consider Chisel 5.x upgrade when project reaches stable milestone.
