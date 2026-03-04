# piquillo 🌶️

**Make spicy bitmaps embedded with secrets using `piquillo.py`.** 

## Overview

`piquillo.py` is a **python script able to encrypt and embed, as well as extract and decrypt hidden messages (as files) in bitmap's pixel values.**

This respository contains updated code developed for my graduate thesis project: [Steganografija u digitalnim slikama](https://www.unirepository.svkri.uniri.hr/object/riteh:5406)

note: ***the script works with lossless image formats, such as PNG and BMP.***

## Disclaimer

This software is provided for educational and research purposes only. The author is not responsible for any misuse of this software.

## Features

- **Cover image capacity analysis**
- **Password-based pseudo-random embedding for enhanced security**
- **Encryption of file name, content, and size before embedding**
- **HMAC-based verification of decrypted data before writing output during extraction**
- **Default use of LSB +/- 1 embedding**
- **Use of syndrome coding when set binary block size *k* is > 1**

## Requirements

Additional packages are required to run `piquillo.py`:

- [`pillow`](https://pillow.readthedocs.io/en/stable/) and [`numpy`](https://numpy.org/doc/stable/) for image processing
- [`pycryptodome`](https://www.pycryptodome.org/) for cryptographic operations

These packages are listed in `requirements.txt`, which can be installed in a python virtual environment.

## Usage

The CLI is structured and defined using `argparse`, which allows for a simple access to helping manuals. To access the default help manual type:

**`python piquillo.py -h`**

Presented tasks are:

- **`check`**
- **`embed`**
- **`extract`**

To access help manual for each task and to list arguments type:

`python piquillo.py [task] -h`

Where `[task]` is replaced with one of the listed without brackets.

**Embedding example:**

`python piquillo.py embed -ci cover.png -mf message.txt -k 4`

*enter encryption (1) and embedding (2) passwords, following with stego image name (e.g. stego.png)...*

**Extraction example:**

```python piquillo.py extract -si stego.png -k 4```

*enter extraction (2) and decryption (1) passwords...*

**Note about the *k* binary block size number:**

Secret message file is encrypted and converted to bits, which are divided into equal *k* length blocks for syndrome coding with LSB +/- 1 embedding.

*Syndrome coding* (also referred to as *matrix embedding*) is an efficient method of embedding k bits of data by modifying a single pixel value. More about this method of embedding can be found on [Daniel Lerch's website](https://daniellerch.me/stego/codes/binary-hamming-en/), which explains in greater detail how it's applied for hiding information. The applied method in this project is based on the interpretation of Hamming codes from [3Blue1Brown's video](https://www.youtube.com/watch?v=b3NxrZOu_CE), which allows for a more flexible (length) application and helps avoid matrix definitions. 

## Acknowledgements
Main CLI structure is inspired by [`steghide`](https://steghide.sourceforge.net/) (a known piece of steganography software), as well as by aesthetics of [`tomato.py`](https://github.com/itsKaspar/tomato) (itsKaspar's python script to glitch AVI files).
