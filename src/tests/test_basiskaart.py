import os
import shutil

from sql_utils import sql_utils
from basiskaart.basiskaart import fill_basiskaart
from basiskaart.basiskaart_setup import VALUES


# Geen testen voor retrieval van files vanaf objectstore. Bestaande code....


def checktable(table, checkcolumns):
    sql = sql_utils.SQLRunner()
    foundcolumns = sql.get_columns_from_table(table)
    assert (len(foundcolumns) == len(checkcolumns))
    result = [col for col in checkcolumns if col in foundcolumns]
    assert (len(result) == len(checkcolumns))


def test_kbk10():
    shutil.rmtree(VALUES['kbk10'][0][1], ignore_errors=True)
    os.path.realpath(__file__)
    shutil.copytree(
        os.path.dirname(os.path.realpath(__file__)) + '/fixtures/kbk10',
        VALUES['kbk10'][0][1])
    fill_basiskaart(VALUES['kbk10'][0][1], 'kbk10')

    checkcolumns = ('ogc_fid', 'geom', 'WDL_bre_ID', 'AREA')
    checktable('kbk10."WDL_breed_water"', checkcolumns)


def test_kbk50():
    shutil.rmtree(VALUES['kbk50'][0][1], ignore_errors=True)
    shutil.copytree(
        os.path.dirname(os.path.realpath(__file__)) + '/fixtures/kbka50',
        VALUES['kbk50'][0][1])
    fill_basiskaart(VALUES['kbk50'][0][1], 'kbk50')

    checkcolumns = ('ogc_fid', 'geom', 'KRT_A_w_ID', 'AREA')
    checktable('kbk50."KRT_A_wegnummer_bord"', checkcolumns)


def test_bgt():
    shutil.rmtree(VALUES['bgt'][0][1], ignore_errors=True)
    shutil.copytree(
        os.path.dirname(os.path.realpath(__file__)) + '/fixtures/bgt',
        VALUES['bgt'][0][1])
    fill_basiskaart(VALUES['bgt'][0][1], 'bgt')

    checkcolumns = (
        'ogc_fid', 'geom', 'namespace', 'lokaalid', 'begintijd', 'einddtijd',
        'tijdreg', 'eindreg', 'lv_pubdat', 'bronhoud', 'inonderzk', 'hoogtelig',
        'bgtstatus', 'plusstatus', 'bgtfysvkn', 'optalud', 'plusfysvkn')
    checktable('bgt."BGT_BTRN_grasland_agrarisch"', checkcolumns)

    checkcolumns = (
        'ogc_fid', 'geom', 'namespace', 'lokaalid', 'begintijd', 'einddtijd',
        'tijdreg', 'eindreg', 'lv_pubdat', 'bronhoud', 'inonderzk', 'hoogtelig',
        'bgtstatus', 'plusstatus', 'bgttype', 'plustype')
    checktable('bgt."BGT_OWDL_transitie"', checkcolumns)

    checkcolumns = (
        'ogc_fid', 'geom', 'namespace', 'lokaalid', 'begintijd', 'einddtijd',
        'tijdreg', 'eindreg', 'lv_pubdat', 'bronhoud', 'inonderzk', 'hoogtelig',
        'bgtstatus', 'bgttype', 'plusstatus', 'plustype')
    checktable('bgt."BGT_WDL_transitie"', checkcolumns)
