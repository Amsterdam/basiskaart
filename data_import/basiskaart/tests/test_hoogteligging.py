import os
import shutil

import basiskaart_setup as bs
from basiskaart import fill_bk
from hoogteligging import create_views_based_on_workbook


# Geen testen voor retrieval van files vanaf objectstore. Bestaande code....
VALUES = bs.VALUES

def test_hoogteview():
    tmpdir = VALUES['bgt'][0][1]
    shutil.rmtree(tmpdir, ignore_errors=True)
    shutil.copytree(
        os.path.dirname(os.path.realpath(__file__)) + '/fixtures/views',
        tmpdir)
    fill_bk(tmpdir, 'bgt')

    create_views_based_on_workbook()