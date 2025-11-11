// SPDX-License-Identifier: MIT
// MyCPU is freely redistributable under the MIT License. See the file
// "LICENSE" for information on usage and redistribution of this file.

#define VRAM_BASE 0x20000000
#define VRAM ((volatile unsigned char *) VRAM_BASE)

#define TIMER_BASE 0x80000000
#define TIMER_LIMIT ((volatile unsigned int *) (TIMER_BASE + 4))
#define TIMER_ENABLED ((volatile unsigned int *) (TIMER_BASE + 8))

#define UART_BASE 0x40000000
#define UART_BAUDRATE ((volatile unsigned int *) (UART_BASE + 4))
#define UART_ENABLE ((volatile unsigned int *) (UART_BASE + 8))
#define UART_RECV ((volatile unsigned int *) (UART_BASE + 12))
#define UART_SEND ((volatile unsigned int *) (UART_BASE + 16))
