import logging
import zipfile
from io import BytesIO

import os

from objectstore.objectstore import ObjectStore

log = logging.getLogger(__name__)

tmpdir = '/tmp/os_connection_test'
store = ObjectStore('Diva', 'bag_brk')


def fetch_files_from_objectstore():
    files = store.get_store_objects('Zip_bestanden')
    print("\nDownload files into '{}'".format(tmpdir))
    os.makedirs(tmpdir, mode=0o777, exist_ok=True)
    extra_dir_nr = 0

    for file in files:
        # print("write file: " + file['name'].split('/')[-1])
        # with open(f"{tmpdir}/{file['name'].split('/')[-1]}", 'wb') as f:
        #     f.write(store.get_store_object(file['name']))
        # extra_dir_nr += 1

        fsplit = os.path.split(file['name'])
        if len(fsplit) == 2 and 'Zip_bestanden' in fsplit[0]:  # and fsplit[1].endswith('part'):
            print("Retrieving from objectstore: " + file['name'])
            content = BytesIO(store.get_store_object(file['name']))
            print("make a zip file from: " + file['name'])
            inzip = zipfile.ZipFile(content)
            extra_dir_nr += 1
            extra_tmpdir = os.path.join(tmpdir, str(extra_dir_nr))
            print("Extract %s to temp directory %s", file['name'], extra_tmpdir)
            inzip.extractall(extra_tmpdir)

    if extra_dir_nr == 0:
        raise Exception('Download directory not found, no files downloaded')


    return extra_dir_nr

for a in range(10):
    print("pass {} of fetch files".format(a))
    nr_files = fetch_files_from_objectstore()
