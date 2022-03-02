import argparse
import os
import struct

from lz77 import Lz77

def get_filepaths(directory):
    file_paths = []

    for root, directories, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            file_paths.append(filepath.replace(os.sep, '/'))

    return file_paths

def main() -> None:
    parser = argparse.ArgumentParser(description="A utility to create ARC files.")
    parser.add_argument(
        "file",
        help="ARC file to create.",
        type=str,
    )
    parser.add_argument(
        "-d",
        "--directory",
        help="Directory to create from. Defaults to data/.",
        default="data"
    )
    args = parser.parse_args()

    root = args.directory
    if root[-1] != '/':
        root = root + '/'
#    root = os.path.realpath(root)

    files = get_filepaths(root)
    numfiles = len(files)

    fp = open(args.file, 'wb')
    fp.write(b'\x20\x11\x75\x19')
    fp.write(struct.pack('<III', 1, numfiles, 2))

    hack = 0
    for fno in range(numfiles):
        nmna = files[fno]
        while not nmna.startswith('data'):
            nmna = nmna[1:]
            hack += 1

    nameoffset = 0x10 + (numfiles * 0x10)
    fileoffset = nameoffset + sum([len(x) for x in files])-hack + len(files)
    while fileoffset % 64 != 0:
        fileoffset += 1

    combinedfiles = bytearray(b'')
    for fno in range(numfiles):
        uncompressedsize = os.path.getsize(files[fno])
        with open (files[fno], 'rb') as fb:
            lz77 = Lz77()
            comp = lz77.compress(fb.read())
            compressedsize = len(comp)
            if compressedsize < uncompressedsize:
                combinedfiles.extend(comp)
                print(f"Writing {files[fno]} to {args.file} with compression...")
            else:
                compressedsize = uncompressedsize
                combinedfiles.extend(lz77.decompress(comp))
                print(f"Writing {files[fno]} to {args.file} without compression...")
        fp.write(struct.pack('<IIII', nameoffset, fileoffset, uncompressedsize, compressedsize))
        nameoffset += len(files[fno]) + 1
        fileoffset += compressedsize

    for fno in range(numfiles):
        nmna = files[fno]
        while not nmna.startswith('data'):
            nmna = nmna[1:]
        fp.write(nmna.encode('utf-8'))
        fp.write(b'\x00')
    while fp.tell() % 64 != 0:
        fp.write(b'\x00')

    fp.write(combinedfiles)


if __name__ == '__main__':
    main()
