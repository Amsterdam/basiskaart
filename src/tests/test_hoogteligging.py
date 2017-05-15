# -*- coding: utf-8 -*-

import os
import shutil

import basiskaart.hoogteligging
from basiskaart import basiskaart_setup
from basiskaart.basiskaart import fill_basiskaart
from basiskaart.hoogteligging import create_views_based_on_workbook, create_indexes
from sql_utils import sql_utils

VIEWPATH = os.path.dirname(os.path.realpath(__file__)) + '/fixtures/views'
basiskaart.hoogteligging.XLS_VIEWDEF = os.path.join(VIEWPATH, 'wms_kaart_database.xlsx')
VALUES = basiskaart_setup.VALUES


def test_hoogteview():
    tmpdir = VALUES['bgt'][0][1]
    shutil.rmtree(tmpdir, ignore_errors=True)
    shutil.copytree(
        os.path.dirname(os.path.realpath(__file__)) + '/fixtures/views',
        tmpdir + '/1')
    fill_basiskaart(tmpdir, 'bgt', 1)

    create_views_based_on_workbook()
    sql = sql_utils.SQLRunner()
    for hoogte in ('_2', '_1', '0', '1', '2'):
        exists = sql.run_sql("select exists(select count(*) from bgt.spoor_lijn{})".format(hoogte))
        print('hoogte {} exists {}'.format(hoogte, exists))
        print(exists)
        assert (exists[0][0])

def test_create_indexes():
    tmpdir = VALUES['bgt'][0][1]
    shutil.rmtree(tmpdir, ignore_errors=True)
    shutil.copytree(
        os.path.dirname(os.path.realpath(__file__)) + '/fixtures/views',
        tmpdir + '/1')
    fill_basiskaart(tmpdir, 'bgt', 1)
    create_indexes()
