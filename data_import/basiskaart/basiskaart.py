# packages
import logging
import os
import shutil
import zipfile
from io import BytesIO
import basiskaart_setup as bs

from objectstore.objectstore import ObjectStore
from sql_utils import SQLRunner, createdb

log = logging.getLogger(__name__)
VALUES=bs.VALUES


def fill_bk(tmpdir, schema):
    """
    Importeer 'basiskaart files' in Postgres
    schema 'basiskaart' mbv ogr2ogr
    :return:
    """

    createdb()
    os.makedirs(tmpdir, exist_ok=True)

    sql = SQLRunner()
    for schema_proc in VALUES[schema]:
        sql.run_sql("DROP SCHEMA IF EXISTS {} CASCADE".format(schema_proc))
        sql.run_sql("CREATE SCHEMA {}".format(schema_proc))
        sql.import_bk(tmpdir, schema_proc)


def process_bk(kbk_name):
    for object_store_name, tmpdir, path, prefix, importnames in VALUES[
            kbk_name]:
        schema = kbk_name
        get_bk(object_store_name, path, tmpdir, prefix, importnames)
        fill_bk(tmpdir, schema)


def get_bk(object_store_name, name, tmpdir, prefix, importnames):
    """
    Get zip from either local disk (for testing purposes) or from Objectstore

    :param object_store_name: Username to objectstore
    :param name: Name of directory where zipfiles are
    :param tmpdir: temporary storage where to extract
    :param prefix: Prefix in objectstore
    :param importnames: First (glob) characters of names of zipfiles
    :return: None
    """
    try:
        shutil.rmtree(tmpdir)
    except FileNotFoundError:
        pass
    store = ObjectStore(prefix, object_store_name)
    files = store.get_store_objects(name)
    log.info("Download shape files kbk10/kbk50/bgt zip")
    for file in files:
        fsplit = os.path.split(file['name'])
        if len(fsplit) == 2 and fsplit[0] == name and fsplit[1].startswith(
                importnames):
            content = BytesIO(store.get_store_object(file['name']))
            inzip = zipfile.ZipFile(content)
            log.info("Extract to temp directory %s", tmpdir)
            inzip.extractall(tmpdir)
    return
