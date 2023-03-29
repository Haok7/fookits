import subprocess
import re
from b2sdk.v2 import *
from PIL import Image
from pillow_heif import register_heif_opener, register_avif_opener
import os

bucket_name = 'your_bucket_name'
application_key_id = 'your_key_id'
application_key = 'your_key'
b2_file_folder = 'your_bucket_folder'
hosting_url = 'https://hosting.domain'
file_info = {'how': 'good-file'}

def convert_to_avif(source, target):
    register_heif_opener()
    register_avif_opener()
    im = Image.open(source)
    im.save(target)

    source_size = os.path.getsize(source)
    target_size = os.path.getsize(target)
    rate = target_size / source_size * 100
    print("[|] %s\n[|]\t[%d ===> %d]\t%.1f%%" % (source, source_size, target_size, rate))

def main():

    print("[*] Running [fooimg.py] ...")

    # generate list of modified/untracked files
    md_list = re.findall("\S*\.md", subprocess.getoutput(["git status"]))

    # connect to b2
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    b2_api.authorize_account("production", application_key_id, application_key)
    bucket = b2_api.get_bucket_by_name(bucket_name)

    # modify related files
    for md_path in md_list:
        print("[+] Checking %s" % md_path)
        content = ""
        with open(md_path, 'r') as f:
            content = f.read()
            img_list = re.findall("!\[[^!]*\]\([^!]+\)", content)
            for img_info in img_list:        
                img_path = re.findall("\([^ ]*\)", img_info)[-1][1:-1]
                if img_path.startswith("https"): continue
                avif_path = img_path.split('.')[0] + '.avif'
                img_name = avif_path.split('/')[-1]
                # convert image to avif
                convert_to_avif(img_path, avif_path)
                # upload avif
                img_url = hosting_url + img_name
                print("[|] uploading to: %s" % img_url)
                bucket.upload_local_file(
                    local_file = avif_path,
                    file_name = b2_file_folder + img_name,
                    file_infos = file_info,
                )
                # replace image path
                print("[|] replacing image path ...")
                content = content.replace(img_path, img_url)
        with open(md_path, 'w') as f:            
            f.write(content)
        print("[-] Done.")

        print("[*] [fooimg.py] finished.")

if __name__ == "__main__":
    main()
