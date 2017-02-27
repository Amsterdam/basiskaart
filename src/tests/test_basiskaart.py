# -*- coding: utf-8 -*-
"""
Test de basiskaart
"""

import os
import shutil

from sql_utils import sql_utils
from basiskaart.basiskaart import fill_basiskaart
from basiskaart.basiskaart_setup import VALUES


# Geen testen voor retrieval van files vanaf objectstore. Bestaande code....


def checktable(table, checkcolumns):
    """

    :param table:
    :param checkcolumns:
    :return:
    """
    sql = sql_utils.SQLRunner()
    foundcolumns = sql.get_columns_from_table(table)
    assert (len(foundcolumns) == len(checkcolumns))
    result = [col for col in checkcolumns if col in foundcolumns]
    assert (len(result) == len(checkcolumns))


def test_kbk10():
    """
    Test kbk10
    :return:
    """
    shutil.rmtree(VALUES['kbk10'][0][1], ignore_errors=True)
    os.path.realpath(__file__)
    shutil.copytree(
        os.path.dirname(os.path.realpath(__file__)) + '/fixtures/kbk10',
        VALUES['kbk10'][0][1])
    fill_basiskaart(VALUES['kbk10'][0][1], 'kbk10')

    checkcolumns = ('ogc_fid', 'geom', 'WDL_bre_ID', 'AREA')
    checktable('kbk10."WDL_breed_water"', checkcolumns)


def test_kbk50():
    """
    Test kbk50
    :return:
    """
    shutil.rmtree(VALUES['kbk50'][0][1], ignore_errors=True)
    shutil.copytree(
        os.path.dirname(os.path.realpath(__file__)) + '/fixtures/kbka50',
        VALUES['kbk50'][0][1])
    fill_basiskaart(VALUES['kbk50'][0][1], 'kbk50')

    checkcolumns = ('ogc_fid', 'geom', 'KRT_A_w_ID', 'AREA')
    checktable('kbk50."KRT_A_wegnummer_bord"', checkcolumns)


def test_bgt():
    """
    test bgt
    :return:
    """
    shutil.rmtree(VALUES['bgt'][0][1], ignore_errors=True)
    tempdir = VALUES['bgt'][0][1]
    shutil.copytree(
        os.path.dirname(os.path.realpath(__file__)) + '/fixtures/bgt',
        tempdir)
    fill_basiskaart(tempdir, 'bgt')
    checkcolumns = (
        'ogc_fid', 'geometrie', 'identificatie_namespace',
        'identificatie_lokaalid', 'objectbegintijd', 'objecteindtijd',
        'tijdstipregistratie', 'eindregistratie', 'lv_publicatiedatum',
        'bronhouder', 'inonderzoek', 'relatievehoogteligging',
        'bgt_status', 'plus_status', 'bgt_fysiekvoorkomen', 'optalud',
        'plus_fysiekvoorkomen')
    checktable('bgt."BGT_BTRN_grasland_agrarisch"', checkcolumns)

    checkcolumns = (
        'ogc_fid', 'geometrie', 'identificatie_namespace',
        'identificatie_lokaalid', 'objectbegintijd', 'objecteindtijd',
        'tijdstipregistratie', 'eindregistratie', 'lv_publicatiedatum',
        'bronhouder', 'inonderzoek', 'relatievehoogteligging',
        'bgt_status', 'plus_status', 'bgt_type', 'plus_type')
    checktable('bgt."BGT_OWDL_transitie"', checkcolumns)

    checkcolumns = (
        'ogc_fid', 'geometrie', 'identificatie_namespace',
        'identificatie_lokaalid', 'objectbegintijd', 'objecteindtijd',
        'tijdstipregistratie', 'eindregistratie', 'lv_publicatiedatum',
        'bronhouder', 'inonderzoek', 'relatievehoogteligging',
        'bgt_status', 'plus_status', 'bgt_type', 'plus_type')
    checktable('bgt."BGT_WDL_transitie"', checkcolumns)
