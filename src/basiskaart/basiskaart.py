# -*- coding: utf-8 -*-

import logging
import os
import shutil
import subprocess
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
    tables = sql.get_tables_in_schema(schema)
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

    if not os.path.exists(shape_dir):
        return

    counters = count_shapes(shape_dir, counters)
    sql.import_basiskaart(shape_dir, schema)

    if schema == 'bgt':
        renamefields()

    counters = count_rows_in_tables(schema, counters)
    report_counts(counters)


def renamefields():
    tables_in_schema = sql.get_tables_in_schema('bgt')
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

    filepath = metafile['name']

    for name_match in matchpatterns:

        if name_match not in filepath:
            continue

        if not filepath.endswith(endswith):
            continue

        log.info(
            "\n Match %s from objectstore: %s \n",
            name_match, metafile['name'])

        return True


def extract_source_files_basiskaart(sources, only_list_source_files=False):
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

    clear_output_dir(sources['target_dir'])

    store = ObjectStore(sources['container'], sources['objectstore'])
    dir_listing = store.get_store_objects(sources['source_path'])

    log.info("\nDownload shape files into '%s'", sources['target_dir'])

    file_count = 0
    for metafile in dir_listing:
        if metafile['content_type'] == "application/directory":
            continue

        if not is_name_match(metafile, sources['filters'], sources['suffix']):
            continue

        if only_list_source_files:
            continue

        file_count += 1
        get_source_file(store,
                        metafile,
                        sources['source_path'],
                        sources['target_dir'],
                        sources['is_zips'])

    # check if we actualy downloaded something
    if file_count == 0 and not only_list_source_files:
        raise Exception('Download directory left empty, no shapes imported')


def _fix_corrupt_zip(zip_content: bytes) -> bytes:
    """Returns zipfile bytes which is seekable by python's ZipFile."""
    return subprocess.run(
        ["zip", "-F", "--out -", "-"],
        input=zip_content,
        stdout=subprocess.PIPE,
        shell=True
    ).stdout


def get_source_file(store, metafile, source_path, target_dir, is_zips):
    """
    Download objectsore file and unzip it at shapedir
    """
    content = store.get_store_object(metafile['name'])
    content = BytesIO(_fix_corrupt_zip(content))

    if is_zips:
        log.info("make a zip metafile from: %s", metafile['name'])
        inzip = zipfile.ZipFile(content)
        del content

        log.info("Extract %s to temp directory %s",
                 metafile['name'], target_dir)

        inzip.extractall(target_dir)
    else:
        target_file = metafile['name'].replace(source_path, target_dir)
        directory = os.path.split(target_file)[0]
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(target_file, 'wb') as file:
            file.write(content.read())


def process_basiskaart(kbk_name, only_list_source_files=False):
    """
    Download objectstore bestanden en zet deze in de database

    param: list_source_items only show which files would be downloaded
    """
    for sources in SOURCE_DATA_MAP[kbk_name]:

        extract_source_files_basiskaart(
            sources, only_list_source_files=only_list_source_files
        )

        if only_list_source_files:
            continue

        fill_basiskaart(sources['target_dir'], sources['schema'])
