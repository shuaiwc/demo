import os
import zipfile
import shutil

def zip_folder(source_folder, output_zip):
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_folder):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), source_folder))

def unzip_folder(zip_file, extract_to):
    with zipfile.ZipFile(zip_file, 'r') as zipf:
        zipf.extractall(extract_to)
    os.remove(zip_file)  

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    source_folder = os.path.join(script_dir, 'test/')
    output_zip = os.path.join(script_dir, 'output/output.zip')
    extract_to = os.path.join(script_dir, 'extract/')

    zip_folder(source_folder, output_zip)
    unzip_folder(output_zip, extract_to)