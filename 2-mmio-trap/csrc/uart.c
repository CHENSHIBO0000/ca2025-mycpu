#include "mmio.h"

#define DONE_FLAG ((volatile unsigned int *) 0x100)

static inline void uart_putc(char c)
{
    *UART_SEND = (unsigned int) (unsigned char) c;
}

int main(void)
{
    const char message[] = "UART OK\n";

    *UART_BAUDRATE = 115200;
    *UART_ENABLE = 1;

    const char *p = message;
    while (*p)
        uart_putc(*p++);

    *DONE_FLAG = 0xCAFEF00D;
    while (1)
        ;
    return 0;
}
