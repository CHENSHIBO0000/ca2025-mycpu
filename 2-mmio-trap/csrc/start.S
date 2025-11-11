// SPDX-License-Identifier: MIT
// Minimal startup code for bare-metal RISC-V

.section .text.start
.global _start

_start:
    // Set up stack pointer
    li sp, 0x00400000  // Stack at top of 4MB RAM

    // Call main function
    call main

    // Halt loop if main returns
_halt:
    j _halt
