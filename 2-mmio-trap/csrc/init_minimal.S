.section .text.init
.globl _start
_start:
  li sp, 0x400000
  call main
loop:
  j loop
