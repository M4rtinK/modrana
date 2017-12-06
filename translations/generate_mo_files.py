#!/usr/bin/python3

import glob
import os
import subprocess

po_langs = [f.split(".")[0] for f in glob.glob("*.po")]
print("po files found for: %s" % po_langs)
print("generating mo files")
for lang in po_langs:
    print("processing %s" % lang)
    folder_path = os.path.join("mo", lang, "LC_MESSAGES")
    input_file = "%s.po" % lang
    output_file_path = os.path.join(folder_path, "%s.mo" % lang)
    # crete to containing folder first
    os.makedirs(folder_path, exist_ok=True)
    # create the mo file
    subprocess.run(["msgfmt", input_file, "-o", output_file_path])
print("done")
