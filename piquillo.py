import sys
import argparse
import numpy as np
from PIL import Image
from Crypto.Hash import HMAC, SHA256
from image_utils import *
from file_processing_utils import *
from syndrome_utils import calculate_points_dir, calculate_points_inv


def main():

    parser = argparse.ArgumentParser(description="piquillo: pixel steganography")
    subparsers = parser.add_subparsers(dest="task")
                     
    info = subparsers.add_parser('info', help='prints image capacity')
    info.add_argument('-ci', type=str, help='cover image path', required=True)
    info.add_argument('-k', type=int, help='binary block size', default=1)
        
    embed = subparsers.add_parser('embed', help='embed a secret file')
    embed.add_argument('-sf', type=str, help='secret file path', required=True)
    embed.add_argument('-ci', type=str, help='cover image path', required=True)
    embed.add_argument('-k', type=int, help='binary block size', default=1)

    extract = subparsers.add_parser('extract', help='extract a secret file')
    extract.add_argument('-si', type=str, help='stego image path', required=True)
    extract.add_argument('-k', type=int, help='binary block size', default=1)

    args = parser.parse_args()


    match args.task:

        case 'info':

            k = np.abs(args.k)
            im_path = args.ci

            # load image array
            cover = Image.open(im_path)
            c_arr = np.array(cover)
            c_arr1 = c_arr.flatten() 

            # n of image pixel points
            n_pts = len(c_arr1)

            if k == 1:
                byte_cap = n_pts // 8
            
            else:
                b_len = 2 ** k
                # cap in n of blocks
                n_b = n_pts // b_len
                byte_cap = k*n_b // 8

            print(f"\ncover capacity: {byte_cap} B\n")

    
        case 'embed':

            sf_path = args.sf
            im_path = args.ci
            k = np.abs(args.k)

            if not os.path.exists(sf_path):
                print(f"error: {sf_path} doesn't exist!")
                sys.exit(1)
                
            aes_passw = input("\nenter file encryption password: ")
            p1_b, p2_b = process_file_to_binary(sf_path, k, aes_passw)

            # k=1: n of bits (=embedding pts); k>1: n of bin blocks
            n1_b = len(p1_b)
            n2_b = len(p2_b)

            # for LSB method
            if k == 1:
                n_pts1 = n1_b
                n_pts2 = n2_b

            # for syndrome coding method
            else:
                out = calculate_points_dir(k, n1_b, n2_b)
                n_pts1 = out[0]
                n_pts2 = out[1]
                shape_ids1 = out[2]
                shape_ids2 = out[3]

            # load cover image array
            cover = Image.open(im_path)
            c_arr = np.array(cover)

            # flat cover pixels array
            c_arr1 = c_arr.flatten()

            # n of image pixel points
            n_pts = len(c_arr1)
            ids_arr0 = np.arange(n_pts)

            if (n_pts1+n_pts2) > n_pts:
                print("error: exceeded image embedding capacity")
                sys.exit(1)

            rng_passw = input("enter image embedding password: ")
            key = hash_digest(rng_passw)
            seed = int.from_bytes(key)
            rng = np.random.default_rng(seed)

            # indices selection for p1_b and p2_b embedding
            sel1 = rng.choice(ids_arr0, n_pts1, 0)
            mask = ~np.isin(ids_arr0, sel1)
            ids_arr1 = ids_arr0[mask]
            sel2 = rng.choice(ids_arr1, n_pts2, 0)

            # for syndrome coding method
            if k > 1:
                sel1 = np.reshape(sel1, shape_ids1)
                sel2 = np.reshape(sel2, shape_ids2)

            # flat stego pixels array s_arr1
            s_arr1 = embed_pixels(c_arr1, sel1, p1_b, k)
            s_arr1 = embed_pixels(c_arr1, sel2, p2_b, k)

            shape = c_arr.shape
            s_arr = s_arr1.reshape(shape)

            stego = Image.fromarray(s_arr)
            print("\nsaving stego image...")
            stego.save("stego.png")

        case 'extract':

            k = np.abs(args.k)
            im_path = args.si

            # load stego image array
            im = Image.open(im_path)
            im_arr = np.array(im)
            s_arr = im_arr.flatten() 

            stego = Image.open(im_path)
            s_arr = np.array(im)
            
            s_arr1 = s_arr.flatten() 

            # n of image pixel points
            n_pts = len(s_arr1)
            ids_arr0 = np.arange(n_pts)

            rng_passw = input("enter image embedding password: ")
            key = hash_digest(rng_passw)
            seed = int.from_bytes(key)
            rng = np.random.default_rng(seed)

            # part 1: 19 bytes = 16 B (iv) + 3 B (encrypted size)
            # for LSB method
            if k == 1:
                n_pts1 = 19 * 8
            # for syndrome coding method
            else:
                n_pts1, shape_ids1 = calculate_points_inv(k, 19)

            # indices selection with embedded p1_b
            sel1 = rng.choice(ids_arr0, n_pts1, 0)

            if k > 1:
                sel1 = np.reshape(sel1, shape_ids1)

            p1_b = extract_pixels(s_arr1, sel1, k)
            p1_B = bits_to_bytes(merge_unpad(p1_b))

            iv = p1_B[:16]
        
            aes_passw = input("enter file encryption password: ")
            key = hash_digest(aes_passw)

            ciphertext = p1_B[16:]
            size = decrypt(iv, ciphertext, key)
            size = int.from_bytes(size)

            # part 2: excracted "size" number of B + 32 B (for mac)
            if k == 1:
                n_pts2 = (size+32) * 8
            else:
                n_pts2, shape_ids2 = calculate_points_inv(k, size+32)

            if (n_pts1+n_pts2) > n_pts:
                print("error: extracted size exceeded capacity")
                sys.exit(1)

            # indices selection with embedded p2_b
            mask = ~np.isin(ids_arr0, sel1)
            ids_arr1 = ids_arr0[mask]
            sel2 = rng.choice(ids_arr1, n_pts2, 0)

            if k > 1:
                sel2 = np.reshape(sel2, shape_ids2)

            p2_b = extract_pixels(s_arr1, sel2, k)
            p2_B = bits_to_bytes(merge_unpad(p2_b))

            ciphertext += p2_B[:-32]
            mac = p2_B[-32:]

            print("")
            plaintext = decrypt(iv, ciphertext, key)
            try:
                HMAC.new(key, plaintext, SHA256).verify(mac)

                data = plaintext[3:]

                f_name = data[1:1+data[0]].decode()
                f_data = data[1+data[0]: ]
        

                print(f"saving exctracted {f_name} file...")
                with open(f_name, "wb") as f:
    
                    f.write(f_data)
            except:
                print("error: plaintext failed authentication!")
                sys.exit(1)
                

        case _:

            parser.print_help()


if __name__ == '__main__':

    welcome_ascii = r"""
       _             _ _ _                    
 _ __ (_) __ _ _   _(_) | | ___   _ __  _   _ 
| '_ \| |/ _` | | | | | | |/ _ \ | '_ \| | | |
| |_) | | (_| | |_| | | | | (_) || |_) | |_| |
| .__/|_|\__, |\__,_|_|_|_|\___(_) .__/ \__, |
|_|         |_|                  |_|    |___/ 

        """
    print(welcome_ascii)

    main()

