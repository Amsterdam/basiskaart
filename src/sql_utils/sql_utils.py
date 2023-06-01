# -*- coding: utf-8 -*-

import logging
import os
import subprocess

import psycopg2
import psycopg2.extensions

from multiprocessing import Pool

from basiskaart import basiskaart_setup as bs

DATABASE = bs.DATABASE

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def parallelize(importjob, tasks, processes):
    """
    Call `importjob` for each file in `tasks`, using
    up to `processes` parallel processes.
    Wait for them all to complete.
    """
    Pool(processes).starmap(importjob, tasks, chunksize=1)
    return


class SQLRunner(object):
    """
    A homebrew sql executing class
    because using a proper ORM is not handy.
    ( I do not approve..)
    """
    def __init__(self, host=DATABASE['HOST'],
                 port=DATABASE['PORT'],
                 dbname=DATABASE['NAME'],
                 user=DATABASE['USER'],
                 password=DATABASE['PASSWORD']):
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password
        self.conn = None

    def connect(self):
        """
        Create connection
        """

        self.conn = psycopg2.connect(
            "host={} port={} dbname={} user={}  password={}".format(
                self.host, self.port,
                self.dbname, self.user, self.password))

    def clone(self):
        return SQLRunner(
            self.host, self.port, self.dbname, self.user,
            self.password)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def run_sql(self, script) -> list:
        """
        Runs the sql script against connected database
        :param script:
        :return:
        """
        if not self.conn:
            self.connect()

        self.conn.set_isolation_level(
            psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        dbcur = self.conn.cursor()

        try:
            dbcur.execute(script)
            if dbcur.rowcount > 0:
                return dbcur.fetchall()
            return []

        except psycopg2.Error as e:
            log.debug(script)
            log.debug("Database script exception: :%s", str(e))
            raise Exception(e)

    def run_sql_no_results(self, script):

        log.debug(script)

        if not self.conn:
            self.connect()

        dbcur = self.conn.cursor()

        dbcur.execute(script)

    def rename_column(self, table, column_from, column_to):

        if not self.conn:
            self.connect()

        query = 'ALTER TABLE {} RENAME COLUMN "{}" TO "{}"'.format(
            table, column_from, column_to)
        dbcur = self.conn.cursor()
        dbcur.execute(query)

    def get_columns_from_table(self, table):
        if not self.conn:
            self.connect()

        dbcur = self.conn.cursor()
        dbcur.execute("SELECT * FROM {} WHERE 1=0".format(table))
        return [desc[0] for desc in dbcur.description]

    def get_tables_in_schema(self, schema):

        if not self.conn:
            self.connect()

        query = """ SELECT * FROM information_schema.tables
                    WHERE table_schema = %s"""
        dbcur = self.conn.cursor()
        dbcur.execute(query, (schema, ))

        return dbcur.fetchall()

    def get_views_in_schema(self, schema):

        if not self.conn:
            self.connect()

        query = """SELECT * FROM pg_catalog.pg_matviews
                   WHERE schemaname = %s"""
        dbcur = self.conn.cursor()
        dbcur.execute(query, (schema, ))
        return dbcur.fetchall()

    def table_exists(self, schema, table):

        if not self.conn:
            self.connect()

        query = f"""SELECT EXISTS( SELECT 1 FROM pg_tables
                    WHERE schemaname = '{schema}' AND
                          tablename = '{table}'
            );"""

        dbcur = self.conn.cursor()
        dbcur.execute(query)

        return dbcur.fetchone()[0]

    def run_sql_script(self, script_name) -> list:
        """
        Runs the sql script against the database
        :param script_name:
        :return:
        """
        return self.run_sql(open(script_name, 'r', encoding="utf-8").read())

    def import_basiskaart(self, path_to_shp, schema):
        os.putenv('PGCLIENTENCODING', 'UTF8')

        log.info('import schema %s in %s', path_to_shp, schema)

        tasks = []

        for root, dirs, files in os.walk(path_to_shp, topdown=False):
            log.info('Processing %s with dirs %s', root, dirs)
            for filename in files:
                if os.path.isdir(filename):
                    continue
                sqldata = self.clone()
                tasks.append((sqldata, filename, schema, root))
                # process_shp_file(self, filename, schema, root)

        parallelize(process_shp_file, tasks, 4)
        # wait for the tasks to finish..
        # pool.join()

    def get_ogr2_ogr_login(self, schema, dbname):
        log.info(
            'Logging into %s:%s db %s.%s',
            self.host, self.port, dbname, schema)

        return f"host={self.host} port={self.port} user={self.user} dbname={dbname} password={self.password}"


def process_shp_file(sql, filename, schema, root):
    """
    load shapre file into database
    """
    filename, filetype = os.path.splitext(filename)
    if filetype == '.shp':
        appendtext = ''
        if sql.table_exists(schema, filename):
            appendtext = '-append'

        log.info('Importing %s/%s%s', root, filename, filetype)
        run_subprocess_ogr(sql, appendtext, schema, root, filename)


def run_subprocess_ogr(sql, appendtext, schema, root, filename):
    """
    OGR subprocess

    *NOTE* *IGNORE THIS WARNING*

    PQconnectdb failed: invalid connection option "active_schema"

    """
    command = (
        'ogr2ogr -nlt PROMOTE_TO_MULTI -progress '
        '-skipfailures {APND} -f "PostgreSQL" '
        'PG:"{PG}" -gt 655360 -s_srs "EPSG:28992" -t_srs '
        '"EPSG:28992" {LCO} {CONF} {FNAME}'.format(
            PG=sql.get_ogr2_ogr_login(schema, 'basiskaart'),
            LCO='-lco SPATIAL_INDEX=OFF -lco PRECISION=NO -lco '
                f'LAUNDER=NO -lco GEOMETRY_NAME=geom -lco SCHEMA={schema}',
            CONF='--config PG_USE_COPY YES',
            FNAME=root + '/' + filename + '.shp',
            APND=appendtext)
    )

    subprocess.call(command, shell=True)


def createdb():
    try:
        SQLRunner(
            host=DATABASE['HOST'],
            port=DATABASE['PORT'],
            dbname=DATABASE['NAME'],
            user=DATABASE['USER'],
            password=DATABASE['PASSWORD'])

    except psycopg2.OperationalError:

        sqlconn = SQLRunner(
            host=DATABASE['HOST'],
            port=DATABASE['PORT'],
            dbname=DATABASE['NAME'],
            user=DATABASE['USER'],
            password=DATABASE['PASSWORD'])

        sqlconn.run_sql('CREATE DATABASE basiskaart;')
        sqlconn.commit()
        sqlconn.close()
