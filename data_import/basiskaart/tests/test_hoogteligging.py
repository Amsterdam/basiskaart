import os
import shutil

import basiskaart.hoogteligging
import basiskaart_setup
import sql_utils
from basiskaart.basiskaart import fill_basiskaart
from basiskaart.hoogteligging import create_views_based_on_workbook

VIEWPATH = os.path.dirname(os.path.realpath(__file__)) + '/fixtures/views'
basiskaart.hoogteligging.XLS_VIEWDEF = os.path.join(VIEWPATH,
                                                    'wms_kaart_database.xlsx')
VALUES = basiskaart_setup.VALUES


def test_hoogteview():
    tmpdir = VALUES['bgt'][0][1]
    shutil.rmtree(tmpdir, ignore_errors=True)
    shutil.copytree(
        os.path.dirname(os.path.realpath(__file__)) + '/fixtures/views',
        tmpdir)
    fill_basiskaart(tmpdir, 'bgt')

    create_views_based_on_workbook()
    sql = sql_utils.SQLRunner()
    for hoogte in ('_2', '_1', '0', '1'):
        exists = sql.run_sql(
            "select exists(select * from information_schema.tables where "
            "table_name='spoor_lijn{}')".format(
                hoogte))
        assert (exists[0][0])
