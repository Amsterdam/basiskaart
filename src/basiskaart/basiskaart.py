# -*- coding: utf-8 -*-

import logging
import os
import shutil
import zipfile
from io import BytesIO

import shapefile

from basiskaart.basiskaart_setup import SOURCE_DATA_MAP
from objectstore.objectstore import ObjectStore
from sql_utils.sql_utils import SQLRunner, createdb

log = logging.getLogger(__name__)
sql = SQLRunner()

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
    'bgtfyskvkn': 'bgt_fysiekvoorkomen',
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
    'plusfyskvkn': 'plus_fysiekvoorkomen',
    'plusstatus': 'plus_status',
    'plustype': 'plus_type',
    'tijdreg': 'tijdstipregistratie',
}


def count_shapes_persubdir(counters, path, dbfs):
    for dbf in dbfs:
        sf = shapefile.Reader(os.path.join(path, dbf))
        shapename = dbf.split('.')[0]
        if shapename in counters:
            counters[shapename][0] += len(sf.shapes())
        else:
            counters[shapename] = [len(sf.shapes()), 0]
    return counters


def count_shapes(extra_shapedir, counters):
    for (path, _dirs, files) in os.walk(extra_shapedir):
        dbfs = [file for file in files if file.endswith('.dbf')]
        counters = count_shapes_persubdir(counters, path, dbfs)
    return counters


def count_rows_in_tables(schema, counters):
    tables = sql.gettables_in_schema(schema)
    for tab_info in tables:
        table_name = tab_info[2]
        cnt = sql.run_sql(f'select count(*) from "{schema}"."{table_name}"')
        counters[table_name][1] += cnt[0][0]
    return counters


def report_counts(counters):
    print('\n')
    print('{:<45} {:>15} {:>15}'.format('table', 'shapes', 'rows in table'))
    for tab, counts in counters.items():
        print('{:<45} {:>15} {:>15}'.format(tab, counts[0], counts[1]))
    print('\n\n')


def fill_basiskaart(shape_dir, schema):
    """
    Importeer 'basiskaart files' in Postgres
    schema 'basiskaart' mbv ogr2ogr
    :return:
    """

    createdb()
    os.makedirs(shape_dir, exist_ok=True)

    log.info("Clean existing schema %s", schema)
    sql.run_sql("DROP SCHEMA IF EXISTS {} CASCADE".format(schema))
    sql.run_sql("CREATE SCHEMA {}".format(schema))
    counters = {}

    for extra_dir_nr in range(10):
        extra_shapedir = os.path.join(shape_dir, str(extra_dir_nr+1))

        if not os.path.exists(extra_shapedir):
            continue

        counters = count_shapes(extra_shapedir, counters)
        sql.import_basiskaart(extra_shapedir, schema)

    # if len(counters.keys()) < 10 and not DEBUG:
    #     raise Exception('No or insufficient input shapefiles present')

    if schema == 'bgt':
        renamefields()

    counters = count_rows_in_tables(schema, counters)
    report_counts(counters)


def renamefields():
    tables_in_schema = sql.gettables_in_schema('bgt')
    for t in tables_in_schema:
        table = '"bgt"."{}"'.format(t[2])
        columns = sql.get_columns_from_table(table)
        renames = [(col, fieldmapping[col]) for col in columns
                   if col in fieldmapping]
        for fromcol, tocol in renames:
            sql.rename_column(table, fromcol, tocol)


def clear_output_dir(shapedir):

    try:
        shutil.rmtree(shapedir)
    except FileNotFoundError:
        pass
    else:
        log.info("Removed %s", shapedir)


def is_name_match(metafile, matchpatterns, endswith):
    """
    If filepath matches with file name conditions
    """

    filepath = os.path.split(metafile['name'])

    if len(filepath) != 2:
        return False

    for name_match in matchpatterns:

        if name_match not in filepath:
            return False

        if not filepath.endswith(endswith):
            return False

        log.info(
            "\n Match %s from objectstore: %s \n",
            name_match, metafile['name'])

        return True


def extract_source_files_basiskaart(
        object_store_name, name, shapedir, prefix,
        matchpatterns, endswith, list_source_files=False):
    """
    Get zip from either local disk (for testing purposes) or from Objectstore

    :param object_store_name: Username to objectstore
    :param name: Name of directory where zipfiles are
    :param shapedir: temporary storage where to extract
    :param prefix: Prefix in objectstore
    :param matchpatterns: First (glob) characters of names of zipfiles
    :param endswith: Name of the importfile endswith
    :return: None
    """

    clear_output_dir(shapedir)

    store = ObjectStore(prefix, object_store_name)
    dir_listing = store.get_store_objects(name)

    log.info("\nDownload shape files zip into '%s'", shapedir)

    extra_dir_nr = 0

    for metafile in dir_listing:
        # log.info("Found in objectstore: " + metafile['name'])

        if not is_name_match(metafile, matchpatterns, endswith):
            continue

        # store this on disk..
        # and skip if already there..
        if list_source_files:
            continue

        extra_dir_nr += 1
        extra_shapedir = os.path.join(shapedir, str(extra_dir_nr))
        unzip_source_file(store, metafile, extra_shapedir)

    # check if we actualy downloaded something
    if extra_dir_nr == 0 and not list_source_files:
        raise Exception('Download directory not found, no shapes imported')


def unzip_source_file(store, metafile, extra_shapedir):
    """
    Download objectsore file and unzip it at shapedir
    """
    content = BytesIO(store.get_store_object(metafile['name']))

    log.info("make a zip metafile from: %s", metafile['name'])
    inzip = zipfile.ZipFile(content)
    del content

    log.info("Extract %s to temp directory %s",
             metafile['name'], extra_shapedir)

    inzip.extractall(extra_shapedir)


def process_basiskaart(kbk_name, list_source_files=False):
    """
    Download objectstore bestanden en zet deze in de database

    param: list_source_items only show which files would be downloaded
    """
    for object_store_name, shapedir, path, prefix, \
            matchpaterns, endswith, schema in SOURCE_DATA_MAP[kbk_name]:

        extract_source_files_basiskaart(
            object_store_name, path, shapedir,
            prefix, matchpaterns, endswith,
            list_source_files=list_source_files
        )

        if list_source_files:
            continue

        fill_basiskaart(shapedir, schema)
