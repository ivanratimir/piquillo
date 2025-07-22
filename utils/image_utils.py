import numpy as np
from .syndrome_utils import get_syndrome


# LSB +/-1 embedding for pixel values
def match_lsb(pv):

    match pv:
        case 0:
            pv += np.uint8(1)
        case 255:
            pv -= np.uint8(1)
        case _:
            pv += np.random.choice([-1, 1])

    return pv


def embed_pixels(array, ids, bits, k):

    # LSB +/-1 embedding method (matching)
    if k == 1:
        for b, i in zip(bits, ids):

            pv = array[i]
            if pv%2 != int(b):
                    
                pv1 = match_lsb(pv)
                array[i] = pv1

    # syndrome coding method
    else:
        for b, i in zip(bits, ids):

            # cover array from pixel data
            c = array[i] % 2
            syn = get_syndrome(c)
            err = syn ^ int(b, 2)

            if err != 0:

                mod = i[err]
                pv = array[mod]
                pv1 = match_lsb(pv)
                array[mod] = pv1

    return array


def extract_pixels(array, ids, k):
        
    bits = []

    # LSB +/-1 embedding method
    if k == 1:
        for i in ids:

            pv = array[i]
            b = pv % 2
            bits.append(str(b))

    # syndrome coding method
    else:
        for i in ids:

            # cover array from DCT cf LSBs
            c = array[i] % 2
            syn = get_syndrome(c)
            b = bin(syn)[2:].zfill(k)
            bits.append(b)
        
    return bits



