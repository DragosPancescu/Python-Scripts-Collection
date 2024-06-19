"""
.HEIC to .PNG converter, takes an input folder with .HEIC files from an Apple device and converts them to .PNG images
"""

import pillow_heif
import shutil, os
import sys
from datetime import datetime

from PIL import Image

if __name__ == "__main__":

    if len(sys.argv) != 4:
        print(
            "There are 3 parameters needed: input, output folder and file type.\n"
            "Example: python main.py input output png"
        )

    input = sys.argv[1]
    output = sys.argv[2]
    file_type = sys.argv[3]

    now = datetime.now()
    log_file = f'Logs_{now.strftime("%H_%M_%S")}.log'

    for filename in os.listdir(input):
        try:
            heif_file = pillow_heif.read_heif(os.path.join(input, filename))

            image = Image.frombytes(
                heif_file.mode,
                heif_file.size,
                heif_file.data,
                "raw",
            )

            new_filename = f'{filename.split(".")[0]}.{file_type}'
            image.save(os.path.join(output, new_filename), format=file_type)
        except Exception as e:
            with open(log_file, "a+") as f:
                f.write(f"Error while converting file: {filename}, reason: {str(e)}\n")
            print(f"Error while converting file: {filename}, reason: {str(e)}")

            if not os.path.exists("Not_converted"):
                os.mkdir("Not_converted")
            shutil.copy(os.path.join(input, filename), "Not_converted")

    print("Done converting")
    print("If any errors appeared during running the script check the logs file.")
