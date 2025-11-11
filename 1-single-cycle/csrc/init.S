# mycpu is freely redistributable under the MIT License. See the file                                                                                        
# "LICENSE" for information on usage and redistribution of this file.

.section .text.init
.global _start
_start:
    li sp, 4096 # Initialize stack pointer
    call main   # Jump to main function
loop:
    j loop      # Loop forever

