import argparse
import textwrap
import sys
import os
import numpy as np
from PIL import Image
from getpass import getpass
from Crypto.Hash import HMAC, SHA256
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


def main():

    parser = argparse.ArgumentParser(description="... for bitmap steganography")
    subparsers = parser.add_subparsers(dest="task")
                     
    pcheck = subparsers.add_parser('check', help='check cover capacity')
    pcheck.add_argument('-ci', type=str, help='cover image path', required=True)
    pcheck.add_argument('-k', type=int, help='binary block size', choices=range(1,9), default=1)
        
    pembed = subparsers.add_parser('embed', help='embed file data')
    pembed.add_argument('-mf', type=str, help='embed file path', required=True)
    pembed.add_argument('-ci', type=str, help='cover image path', required=True)
    pembed.add_argument('-k', type=int, help='binary block size', choices=range(1,9), default=1)

    pextract = subparsers.add_parser('extract', help='extract file data')
    pextract.add_argument('-si', type=str, help='stego image path', required=True)
    pextract.add_argument('-k', type=int, help='binary block size', choices=range(1,9), default=1)

    args = parser.parse_args()

    match args.task:

        case 'check':
            
            k = args.k

            cover = Image.open(args.ci)
            c_arr = np.array(cover)
            c_arr1 = c_arr.flatten() 

            byte_cap = len(c_arr1) // 8
            
            n = 2**k - 1 # block length

            # capacity in n of blocks
            n_blocks = len(c_arr1) // n
            byte_cap = n_blocks * k // 8
            
            print(f"cover capacity: {byte_cap} B")

        case 'embed':

            fpath = args.mf
            fname = os.path.basename(fpath).encode()
            k = args.k

            if not os.path.exists(fpath):
                print(f"{fname} doesn't exist!")
                print("exiting...")
                sys.exit(1)
            
            with open(fpath, "rb") as f:
                fdata = f.read()

            pt2 = len(fname).to_bytes(1) + fname + fdata
            pt1 = len(pt2).to_bytes(3)
            plaintext = pt1 + pt2

            # encryption password prompt and hashing
            pw1 = getpass(prompt="password 1: ").encode()
            h1 = SHA256.new(data=pw1)
            key = h1.digest()
            mac = HMAC.new(key, plaintext, SHA256).digest()
            iv, ciphertext = encrypt(plaintext, key)

            # arrange bytes and convert to 1s and 0s
            mB1 = iv + ciphertext[:3]
            mB2 = ciphertext[3:] + mac
            mB = mB1 + mB2
            mb = ''.join(f"{B:08b}" for B in mB)
            mb = pad_wrap(mb, k)

            # load cover image
            cover = Image.open(args.ci) 
            # convert to a 1-D array
            c_arr = np.array(cover)
            c_arr1 = c_arr.flatten()

            # cover block length
            n = 2**k - 1 
            # capacity in num of blocks
            n_blocks = len(c_arr1) // n
            if len(mb) > n_blocks:
                print("not enough embedding capacity!")
                print("quitting... QQ")
                sys.exit(1)

            # embedding password prompt (for PRNG's seed)
            pw2 = getpass(prompt="password 2: ").encode()
            h2 = SHA256.new(data=pw2)
            seed = int.from_bytes(h2.digest())
            rng = np.random.default_rng(seed)

            # permutaded image indices
            ids = rng.permutation(len(c_arr1))
            
            # 1-D stego array with embedded data
            s_arr1 = embed(c_arr1, ids, mb, k)
            shape = c_arr.shape
            s_arr = s_arr1.reshape(shape)

            # saving output stego image
            oname = input("output name: ")
            print(f"saving as {oname}.png...")
            stego = Image.fromarray(s_arr)
            stego.save(oname+".png") 

        case 'extract':

            k = args.k

            # load stego image
            stego = Image.open(args.si)
            # convert to a 1-D array
            s_arr = np.array(stego)
            s_arr1 = s_arr.flatten() 

            # embedding password prompt (for PRNG's seed)
            pw2 = getpass(prompt="password 2: ").encode()
            h2 = SHA256.new(data=pw2)
            seed = int.from_bytes(h2.digest())
            rng = np.random.default_rng(seed)

            # permutated image indices
            ids = rng.permutation(len(s_arr1))

            n_blocks1 = np.ceil(19*8/k).astype(int)
            n1 = n_blocks1 * (2**k - 1)

            mb1 = extract(s_arr1, ids[:n1], k)
            mB1 = bits_to_bytes(merge_unpad(mb1))

            # nu: number of unpadded bits
            nu = (len(mb1) % 8)
            if nu > 0:
                mb2 = mb1[-nu:]
            else:
                mb2 = []
            
            # separate iv for decryption
            iv = mB1[:16]

            # decryption password prompt and hashing
            pw1 = getpass(prompt="password 1: ").encode()
            h1 = SHA256.new(data=pw1)
            key = h1.digest()

            # ciphertext: 3 B of data for 2nd extraction
            ciphertext = mB1[16:]
            pt1 = decrypt(iv, ciphertext, key)

            # n bytes 2 (fname_len + fname + fdata + MAC)
            nB2 = int.from_bytes(pt1) + 32
            n_blocks2 = np.ceil(nB2*8/k).astype(int)
            n2 = n_blocks2 * (2**k - 1)
            
            mb2 += extract(s_arr1, ids[n1:n1+n2], k)
            mB2 = bits_to_bytes(merge_unpad(mb2))[:nB2]

            ciphertext += mB2[:-32]
            mac = mB2[-32:]
            plaintext = decrypt(iv, ciphertext, key)

            h = HMAC.new(key, plaintext, SHA256)

            try:
                h.verify(mac)
                print("extracted bytes are authentic! \\o/")

                pt2 = plaintext[3:]
                fname_len = pt2[0]
                fname = pt2[1:1 + fname_len]
                fdata = pt2[1 + fname_len: ]

                print(f"writing extracted {fname} bytes...")
                with open(fname, "wb") as f:
    
                    f.write(fdata)

            except ValueError:
                print("invalid MAC. the message was tampered with or the key is wrong!")
                print("quitting... QQ")
                sys.exit(1)
            
        case _:

            parser.print_help()


# ------------------------------------------ #
# ------- IMAGE PROCESSING FUNCTIONS ------- #
# ------------------------------------------ #


# LSB +/-1 embedding
def PM_1(pv):

    match pv:
        case 0:
            pv += np.uint8(1)
        case 255:
            pv -= np.uint8(1)
        case _:
            pv += np.random.choice([-1, 1])

    return pv


# S(y): determine syndrome of binary block y
def S(y):
    
    s = 0
    for i, b in enumerate(y):
        if b:
            s ^= i+1
            
    return s


def embed(c_arr1, ids, m, k):

    s_arr1 = c_arr1
    
    n = 2**k - 1 # block length

    for i in range(len(m)):

        # block of indices
        block = ids[i*n : i*n + n]
        # binary cover block
        c = c_arr1[block] % 2
        # error index
        e = S(c) ^ int(m[i], 2)
        if e > 0:

            mod = block[e-1]
            pv = c_arr1[mod]
            pv1 = PM_1(pv)
            s_arr1[mod] = pv1

    return s_arr1


def extract(s_arr1, ids, k):

    n = 2**k - 1 # block length

    m = []
    for i in range(0, len(ids), n):

        # block of indices
        block = ids[i: i+n]
        # binary stego block
        s = s_arr1[block] % 2
        m += bin(S(s))[2:].zfill(k)
        
    return m


# ------------------------------------------ #
# ------ MESSAGE PROCESSING FUNCTIONS ------ #
# ------------------------------------------ #


def bits_to_bytes(bits):

    val = int(bits, 2)
    n_B = len(bits) // 8

    return val.to_bytes(n_B, byteorder="big")


# zero pad and wrap to equal k length blocks
def pad_wrap(bits, k):

    mod = len(bits) % k
    if mod != 0:
        bits += "0" * (k-mod)
    
    return textwrap.wrap(bits, k)


# merge binary blocks to string and unpad 0s
def merge_unpad(bits):

    bits = "".join(bits)
    mod = len(bits) % 8

    return bits[:len(bits) - mod]


def encrypt(plaintext, key):

    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CFB, iv)
    ciphertext = cipher.encrypt(plaintext)

    return iv, ciphertext


def decrypt(iv, ciphertext, key):

    cipher = AES.new(key, AES.MODE_CFB, iv)
    plaintext = cipher.decrypt(ciphertext)
    
    return plaintext


if __name__ == '__main__':

    hello = r"""
       _             _ _ _                    
 _ __ (_) __ _ _   _(_) | | ___   _ __  _   _ 
| '_ \| |/ _` | | | | | | |/ _ \ | '_ \| | | |
| |_) | | (_| | |_| | | | | (_) || |_) | |_| |
| .__/|_|\__, |\__,_|_|_|_|\___(_) .__/ \__, |
|_|         |_|                  |_|    |___/ 

        """
    print(hello)

    main()


