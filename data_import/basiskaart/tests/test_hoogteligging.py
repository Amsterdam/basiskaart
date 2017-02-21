import os
import shutil

import basiskaart_setup
from basiskaart import fill_bk
import hoogteligging

VIEWPATH = os.path.dirname(os.path.realpath(__file__)) + '/fixtures/views'
hoogteligging.XLS_VIEWDEF = os.path.join(VIEWPATH, '20170216_wms_kaart_database.xlsx')
VALUES = basiskaart_setup.VALUES

def test_hoogteview():
    tmpdir = VALUES['bgt'][0][1]
    shutil.rmtree(tmpdir, ignore_errors=True)
    shutil.copytree(
        os.path.dirname(os.path.realpath(__file__)) + '/fixtures/views',
        tmpdir)
    fill_bk(tmpdir, 'bgt')

    hoogteligging.create_views_based_on_workbook()