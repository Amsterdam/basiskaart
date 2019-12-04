# -*- coding: utf-8 -*-

import os
import shutil

import pytest

import basiskaart.hoogteligging
from basiskaart import basiskaart_setup
from basiskaart.basiskaart import fill_basiskaart
from basiskaart.hoogteligging import create_views_based_on_workbook
from basiskaart.hoogteligging import create_indexes
from sql_utils import sql_utils

VIEWPATH = os.path.dirname(os.path.realpath(__file__)) + '/fixtures/views'
basiskaart.hoogteligging.XLS_VIEWDEF = os.path.join(
    VIEWPATH, 'wms_kaart_database.xlsx')
SOURCE_DATA_MAP = basiskaart_setup.SOURCE_DATA_MAP


def setup_module():
    """
    Load the data
    """
    tmpdir = SOURCE_DATA_MAP['bgt'][0]['target_dir']
    shutil.rmtree(tmpdir, ignore_errors=True)
    shutil.copytree(
        os.path.dirname(os.path.realpath(__file__)) + '/fixtures/views',
        tmpdir)

    fill_basiskaart(tmpdir, 'bgt')

    create_views_based_on_workbook()

    create_indexes()


@pytest.mark.skip
def test_hoogteview():

    sql = sql_utils.SQLRunner()

    for hoogte in ('_2', '_1', '0', '1', '2'):
        exists = sql.run_sql(
            f"select exists(select count(*) from bgt.spoor_lijn{hoogte})")
        assert exists[0][0]


@pytest.mark.skip
def test_create_indexes():
    """
    Check that EVERY table has a 'gist' index
    """

    sql = sql_utils.SQLRunner()

    table_and_view_names = [
        "BGT_PND_pand",
        "BGT_OBW_opslagtank",
        "BGT_SPR_sneltram",
        "BGT_OBW_overkapping",
        "BGT_SPR_tram",
        "BGT_SPR_trein",
        "spoor_lijn1",
        "spoor_lijn_2",
        "spoor_lijn_1",
        "gebouw_vlak0",
        "spoor_lijn0",
        "spoor_lijn2",
        "gebouw_vlak1",
        "WDL_breed_water",
        "KRT_topografie",
        "KRT_brug_viaduct",
        "KRT_A_wegnummer_bord",
        "KBK25_LBL_gemeente",
        "KBK25_LBL_park",
        "KBK25_LBL_kunstwerk",
        "KBK25_LBL_gebied",
    ]

    indexen = sql.run_sql(
        """
        SELECT tablename, indexname FROM pg_indexes
        WHERE indexname NOT LIKE 'pg%'
        AND indexname LIKE '%_gist';
        """
    )
    assert len(indexen) == 17

    for row in indexen:
        assert row[0] in table_and_view_names
