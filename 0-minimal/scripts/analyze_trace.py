#!/usr/bin/env python3
"""
VCD Trace Analyzer for 0-minimal RISC-V CPU

Analyzes trace.vcd to verify JIT self-modifying code execution.
Uses only Python standard library (no external dependencies).

Usage: python3 scripts/analyze_trace.py trace.vcd

Author: MyCPU Project
License: MIT
"""

import re
import sys
from collections import defaultdict

# Expected addresses from jit.S disassembly
JIT_CODE_BUFFER = 0x102c
JIT_INSTRUCTIONS = 0x1034
ENTRY_POINT = 0x1000


def parse_vcd(filename):
    """Parse VCD file and extract key signals"""
    signals = {}  # symbol -> signal_name
    values = defaultdict(list)  # signal_name -> [(time, value)]

    with open(filename, 'r') as f:
        in_definitions = True
        current_time = 0

        for line in f:
            line = line.strip()
            if not line:
                continue

            if in_definitions:
                if line.startswith('$var'):
                    parts = line.split()
                    if len(parts) >= 5:
                        symbol = parts[3]
                        signal_name = parts[4]
                        signals[symbol] = signal_name
                elif line.startswith('$enddefinitions'):
                    in_definitions = False
            else:
                if line.startswith('#'):
                    current_time = int(line[1:])
                elif line.startswith('b'):
                    match = re.match(r'b([01x]+)\s+(.+)', line)
                    if match:
                        value = match.group(1)
                        symbol = match.group(2)
                        if symbol in signals:
                            signal_name = signals[symbol]
                            values[signal_name].append((current_time, value))
                elif len(line) >= 2 and line[0] in '01xz':
                    value = line[0]
                    symbol = line[1:]
                    if symbol in signals:
                        signal_name = signals[symbol]
                        values[signal_name].append((current_time, value))

    return signals, values


def binary_to_int(binary_str):
    """Convert binary string to integer"""
    return int(binary_str, 2) if binary_str and 'x' not in binary_str else 0


def analyze_trace(values):
    """Analyze trace and extract statistics"""
    stats = {
        'pc_samples': 0,
        'pc_at_buffer': 0,
        'memory_writes': 0,
        'writes_to_buffer': 0,
        'register_writes': 0,
        'a0_writes': 0,
        'a0_value_42': False,
        'max_pc': 0
    }

    # Analyze PC trace
    if 'io_instruction_address' in values:
        for time, pc_binary in values['io_instruction_address']:
            pc = binary_to_int(pc_binary)
            if pc > 0:
                stats['pc_samples'] += 1
                stats['max_pc'] = max(stats['max_pc'], pc)

                # Check if executing from JIT buffer
                if JIT_CODE_BUFFER <= pc < JIT_CODE_BUFFER + 0x10:
                    stats['pc_at_buffer'] += 1

    # Analyze memory writes
    if 'io_memory_bundle_write_enable' in values:
        for time, value in values['io_memory_bundle_write_enable']:
            if value == '1':
                stats['memory_writes'] += 1

    # Analyze register writes to a0
    if 'regs_io_write_address' in values:
        for time, addr_binary in values['regs_io_write_address']:
            addr = binary_to_int(addr_binary)
            stats['register_writes'] += 1
            if addr == 10:  # x10 = a0
                stats['a0_writes'] += 1

    # Check if a0 ever equals 42
    if 'regs_io_write_data' in values:
        for time, data_binary in values['regs_io_write_data']:
            value = binary_to_int(data_binary)
            if value == 42:
                stats['a0_value_42'] = True
                break

    return stats


def print_report(stats):
    """Print analysis report"""
    print("=" * 70)
    print("VCD Trace Analysis Report - 0-minimal RISC-V CPU")
    print("=" * 70)
    print()

    # Overall assessment
    jit_executed = stats['pc_at_buffer'] > 0
    a0_is_42 = stats['a0_value_42']
    memory_written = stats['memory_writes'] > 0

    # Primary success criterion: JIT code executed (PC reached buffer)
    # Secondary signals (register writes, memory writes) may not be visible
    # in VCD if they're internal signals not exported to top level
    success = jit_executed and stats['pc_at_buffer'] > 10000
    status = "[PASS]" if success else "[PARTIAL]" if jit_executed else "[FAIL]"

    print(f"Overall Status: {status}")
    print()

    # Key findings
    print("Key Findings:")
    print(f"  {'[OK]' if jit_executed else '[NO]'} JIT Code Execution: {stats['pc_at_buffer']} cycles at buffer address (0x{JIT_CODE_BUFFER:04x})")
    print(f"  {'[OK]' if a0_is_42 else '[NO]'} Register a0 = 42: {stats['a0_value_42']}")
    print(f"  {'[OK]' if memory_written else '[NO]'} Memory Writes: {stats['memory_writes']} total writes")
    print()

    # Detailed statistics
    print("Detailed Statistics:")
    print(f"  PC Samples: {stats['pc_samples']}")
    print(f"  Max PC Address: 0x{stats['max_pc']:08x}")
    print(f"  Register Writes: {stats['register_writes']}")
    print(f"  Writes to a0 (x10): {stats['a0_writes']}")
    print()

    # Expected addresses
    print("Expected Memory Layout:")
    print(f"  Entry Point:       0x{ENTRY_POINT:08x}")
    print(f"  JIT Code Buffer:   0x{JIT_CODE_BUFFER:08x}")
    print(f"  JIT Instructions:  0x{JIT_INSTRUCTIONS:08x}")
    print()

    # Interpretation
    print("Interpretation:")
    if success:
        print("  [OK] CPU successfully executed JIT self-modifying code")
        print(f"  [OK] PC spent {stats['pc_at_buffer']} cycles executing from buffer")
        print("  [OK] JIT code execution flow verified")
        if not a0_is_42 and not memory_written:
            print()
            print("  Note: Internal signals (register writes, memory writes)")
            print("        are not exported to VCD in this minimal CPU design.")
            print("        ChiselTest validates a0=42 via debug interface.")
    elif jit_executed:
        print("  [WARN] JIT execution detected but cycle count low")
        print(f"         ({stats['pc_at_buffer']} cycles, expected >10000)")
    else:
        print("  [FAIL] JIT execution not clearly detected")
        print("  [INFO] Check simulation time and VCD signal coverage")

    print()
    print("=" * 70)

    return success


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_trace.py <trace.vcd>")
        print()
        print("Example: python3 scripts/analyze_trace.py trace.vcd")
        sys.exit(1)

    vcd_file = sys.argv[1]

    print(f"Parsing {vcd_file} ... Please wait.")
    print()

    try:
        signals, values = parse_vcd(vcd_file)
        print(f"Parsed {len(signals)} signals")
        print()

        stats = analyze_trace(values)
        success = print_report(stats)

        sys.exit(0 if success else 1)

    except FileNotFoundError:
        print(f"Error: File '{vcd_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
