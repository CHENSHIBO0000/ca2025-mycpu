/* RISC-V linker script for bare-metal VGA programs */
ENTRY(_start)

MEMORY
{
    RAM (rwx) : ORIGIN = 0x00001000, LENGTH = 4M - 0x1000
}

SECTIONS
{
    .text : {
        *(.text.start)  /* _start must be first */
        *(.text*)
    } > RAM

    .rodata : {
        *(.rodata*)
    } > RAM

    .data : {
        *(.data*)
    } > RAM

    .bss : {
        *(.bss*)
        *(COMMON)
    } > RAM
}
