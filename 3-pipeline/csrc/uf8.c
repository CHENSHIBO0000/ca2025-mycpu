typedef unsigned int  uint32_t;
typedef unsigned char uint8_t;
typedef uint8_t       uf8;

/* CLZ: count leading zeros for 32-bit unsigned int */
static unsigned clz(uint32_t x)
{
    int n = 32;
    int c = 16;

    do {
        uint32_t y = x >> c;
        if (y) {
            n -= c;
            x = y;
        }
        c >>= 1;
    } while (c);

    return n - x;
}

/* Decode uf8 to uint32_t */
uint32_t uf8_decode(uf8 fl)
{
    uint32_t mantissa = (uint32_t)(fl & 0x0f);
    uint8_t  exponent = (uint8_t)(fl >> 4);
    uint32_t offset   = (0x7FFFu >> (15 - exponent)) << 4;
    return (mantissa << exponent) + offset;
}

/* Encode uint32_t to uf8 */
uf8 uf8_encode(uint32_t value)
{
    /* Use CLZ for fast exponent calculation */
    if (value < 16u)
        return (uf8)value;

    /* Find appropriate exponent using CLZ hint */
    int     lz  = (int)clz(value);
    int     msb = 31 - lz;
    uint8_t exponent = 0;
    uint32_t overflow = 0;

    if (msb >= 5) {
        /* Estimate exponent - the formula is empirical */
        exponent = (uint8_t)(msb - 4);
        if (exponent > 15u)
            exponent = 15u;

        /* Calculate overflow for estimated exponent */
        for (uint8_t e = 0; e < exponent; e++)
            overflow = (overflow << 1) + 16u;

        /* Adjust if estimate was off */
        while (exponent > 0u && value < overflow) {
            overflow = (overflow - 16u) >> 1;
            exponent--;
        }
    }

    /* Find exact exponent */
    while (exponent < 15u) {
        uint32_t next_overflow = (overflow << 1) + 16u;
        if (value < next_overflow)
            break;
        overflow = next_overflow;
        exponent++;
    }

    uint8_t mantissa = (uint8_t)((value - overflow) >> exponent);
    return (uf8)((exponent << 4) | mantissa);
}

//test
int main(void)
{

    *(int *)(4) = 1;

    for (int i = 0; i < 256; i++) {
        uint32_t d = uf8_decode((uf8)i);
        uf8 e = uf8_encode(d);
        if (e != (uf8)i) {
            *(int *)(4) = 0;
        }
    }
}
