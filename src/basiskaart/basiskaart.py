# -*- coding: utf-8 -*-

import logging
import os
import shutil
import zipfile
from io import BytesIO

import shapefile

from basiskaart.basiskaart_setup import VALUES, DEBUG
from objectstore.objectstore import ObjectStore
from sql_utils.sql_utils import SQLRunner, createdb

log = logging.getLogger(__name__)
sql = SQLRunner()


def count_shapes_persubdir(counters, path, dbfs):
    for dbf in dbfs:
        sf = shapefile.Reader(os.path.join(path, dbf))
        shapename = dbf.split('.')[0]
        if shapename in counters:
            counters[shapename][0] += len(sf.shapes())
        else:
            counters[shapename] = [len(sf.shapes()), 0]
    return counters


def count_shapes(extra_tmpdir, counters):
    for (path, dirs, files) in os.walk(extra_tmpdir):
        dbfs = [file for file in files if file.endswith('.dbf')]
        counters = count_shapes_persubdir(counters, path, dbfs)
    return counters


def count_rows_in_tables(schema, counters):
    tables = sql.gettables_in_schema(schema)
    for tab_info in tables:
        table_name = tab_info[2]
        cnt = sql.run_sql('select count(*) from "{}"."{}"'.format(schema, table_name))
        counters[table_name][1] += cnt[0][0]
    return counters


def report_counts(counters):
    print('\n')
    print('{:<45} {:>15} {:>15}'.format('table', 'shapes', 'rows in table'))
    for tab, counts in counters.items():
        print('{:<45} {:>15} {:>15}'.format(tab, counts[0], counts[1]))
    print('\n\n')


def fill_basiskaart(tmpdir, schema, max_extra_dir_nr):
    """
    Importeer 'basiskaart files' in Postgres
    schema 'basiskaart' mbv ogr2ogr
    :return:
    """

    createdb()
    os.makedirs(tmpdir, exist_ok=True)

    log.info("Clean existing schema {}".format(schema))
    sql.run_sql("DROP SCHEMA IF EXISTS {} CASCADE".format(schema))
    sql.run_sql("CREATE SCHEMA {}".format(schema))
    counters = {}
    for extra_dir_nr in range(max_extra_dir_nr):
        extra_tmpdir = os.path.join(tmpdir, str(extra_dir_nr+1))
        counters = count_shapes(extra_tmpdir, counters)
        sql.import_basiskaart(extra_tmpdir, schema)

    if len(counters.keys()) < 10 and not DEBUG:
        raise Exception('No or insufficient input shapefiles present')
    if schema == 'bgt':
        renamefields()
    counters = count_rows_in_tables(schema, counters)
    report_counts(counters)


def renamefields():
    fieldmapping = {
        'bagbolgst': 'id_bagvbolaagste_huisnummer',
        'bagid': 'BAG_identificatie',
        'bagoprid': 'identificatieBAGOPR',
        'bagpndid': 'identificatieBAGPND',
        'bagvbohgst': 'identificatieBAGVBOHoogsteHuisnummer',
        'bagvbolgst': 'identificatieBAGVBOLaagsteHuisnummer',
        'begintijd': 'objectbegintijd',
        'bgtfunctie': 'bgt_functie',
        'bgtfysvkn': 'bgt_fysiekvoorkomen',
        'bgtnagid': 'bgt_nummeraanduidingreeks_id',
        'bgtorlid': 'bgt_openbareruimtelabel_id',
        'bgtpndid': 'bgt_pand_id',
        'bgtstatus': 'bgt_status',
        'bgttype': 'bgt_type',
        'bij_object': 'hoortbij',
        'bronhoud': 'bronhouder',
        'eindreg': 'eindregistratie',
        'eindtijd': 'objecteindtijd',
        'einddtijd': 'objecteindtijd',
        'geom': 'geometrie',
        'hm_aand': 'hectometeraanduiding',
        'hoogtelig': 'relatievehoogteligging',
        'hoortbij': 'hoortbijtypeoverbrugging',
        'inonderzk': 'inonderzoek',
        'isbeweegb': 'overbruggingisbeweegbaar',
        'labeltekst': 'label_tekst',
        'lokaalid': 'identificatie_lokaalid',
        'lv_pubdat': 'lv_publicatiedatum',
        'namespace': 'identificatie_namespace',
        'oprtype': 'openbareruimtetype',
        'plusfunct': 'plus_functie',
        'plusfysvkn': 'plus_fysiekvoorkomen',
        'plusstatus': 'plus_status',
        'plustype': 'plus_type',
        'tijdreg': 'tijdstipregistratie',
    }
    tables_in_schema = sql.gettables_in_schema('bgt')
    for t in tables_in_schema:
        table = '"bgt"."{}"'.format(t[2])
        columns = sql.get_columns_from_table(table)
        renames = [(col, fieldmapping[col]) for col in columns
                   if col in fieldmapping]
        for fromcol, tocol in renames:
            sql.rename_column(table, fromcol, tocol)


def get_basiskaart(object_store_name, name, tmpdir, prefix, importnames,
                   endswith):
    """
    Get zip from either local disk (for testing purposes) or from Objectstore

    :param object_store_name: Username to objectstore
    :param name: Name of directory where zipfiles are
    :param tmpdir: temporary storage where to extract
    :param prefix: Prefix in objectstore
    :param importnames: First (glob) characters of names of zipfiles
    :param endswith: Name of the importfile endswith
    :return: None
    """
    try:
        shutil.rmtree(tmpdir)
    except FileNotFoundError:
        pass
    else:
        log.info("Removed {}".format(tmpdir))

    store = ObjectStore(prefix, object_store_name)
    files = store.get_store_objects(name)
    log.info("Download shape files zip into '{}'".format(tmpdir))

    extra_dir_nr = 0
    for file in files:
        fsplit = os.path.split(file['name'])
        if len(fsplit) == 2 and importnames in fsplit[1] and \
                fsplit[1].endswith(endswith):
            content = BytesIO(store.get_store_object(file['name']))
            inzip = zipfile.ZipFile(content)
            extra_dir_nr += 1
            extra_tmpdir = os.path.join(tmpdir, str(extra_dir_nr))
            log.info("Extract %s to temp directory %s",
                     file['name'], extra_tmpdir)
            inzip.extractall(extra_tmpdir)
    if extra_dir_nr == 0:
        raise Exception('Download directory not found, no shapes imported')
    return extra_dir_nr


def process_basiskaart(kbk_name):
    for object_store_name, tmpdir, path, prefix, importnames, schema, endswith \
            in VALUES[kbk_name]:
        max_extra_dir_nr = get_basiskaart(object_store_name, path, tmpdir,
                                          prefix, importnames, endswith)

        fill_basiskaart(tmpdir, schema, max_extra_dir_nr)
