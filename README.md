# piquillo

Applied steganography scripts to embed and extract secret message files within image pixels, developed as a part of an image and signal processing course project and thesis. These scripts work for lossless image formats (like PNG and BMP) by modifying pixel values in the spatial domain.

## Disclaimer

This software is provided for educational and research purposes only. The author is not responsible for any misuse of this software.

## Features

- checking image capacity
- key (password) based pseudo random embedding 
- reading file bytes directly and embedding with file name (file agnostic)
- encryption of file name, content and size using AES in CFB mode before embedding
- HMAC based verification of decrypted file before writing at extraction
- default use of LSB +/- 1 embedding, use of syndrome coding when set binary block size is > 1

## Requirements

The scripts rely on **numpy** and **Pillow** for image processing, as well as **pycryptodome** for file encryption. To install them use:

```pip install numpy Pillow pycryptodome```

## Usage

Main processing script with defined *steghide* (known steganography tool) inspired CLI interface using argparse is **piquillo.py**. To access the default help manual type:

```python piquillo.py -h```

Presented tasks are:

- **info**
- **embed**
- **extract**

To access help manual for each task and list arguments type:

- ```python piquillo.py info -h```
- ```python piquillo.py embed -h```
- ```python piquillo.py extract -h```

In order for the file to be successfuly extracted it has to use the right:
- stego image
- set passwords
- set *k* binary block size number

**Embedding example:**

```python piquillo.py embed -ci cover.png -sf message.txt -k 4```

*enter encryption and embedding passwords...*

*Output **stego.png** will be created...*

**Extraction example:**

```python piquillo.py extract -si stego.png -k 4```

*enter encryption and embedding passwords...*

*Output **message.txt** will be created...*

**Note about the *k* binary block size number:**

The default value for k is 1 for use with LSB +/- 1 embedding, which does not have to be specified. IF the k is set to be higher, syndrome coding will be used. Read file when encrypted and converted to bits will be divided into equal *k* length blocks for syndrome coding. This also means it is no longer neccessery to modify one pixel for storing a secret bit (if the LSB doesn't match), but by modifying one pixel LSB k bits can be stored. This reduces the number of modifications (inserting less noise into image), but also reduces the capacity of image.


