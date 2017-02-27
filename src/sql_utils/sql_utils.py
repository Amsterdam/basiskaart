# -*- coding: utf-8 -*-

import logging
import os
import subprocess

import psycopg2
import psycopg2.extensions

from basiskaart import basiskaart_setup as bs

DATABASE = bs.DATABASE

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class SQLRunner(object):
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
        self.conn = psycopg2.connect(
            "host={} port={} dbname={} user={}  password={}".format(
                host, port, dbname, user, password))

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
        self.conn.set_isolation_level(
            psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        dbcur = self.conn.cursor()
        try:
            dbcur.execute(script)
            if dbcur.rowcount > 0:
                return dbcur.fetchall()
            return []

        except psycopg2.DatabaseError as e:
            log.debug("Database script exception: procedures :%s" % str(e))
            raise Exception(e)

    def rename_column(self, table, column_from, column_to):
        query = 'ALTER TABLE {} RENAME COLUMN "{}" TO "{}"'.format(table, column_from, column_to)
        dbcur = self.conn.cursor()
        dbcur.execute(query)

    def get_columns_from_table(self, table):
        dbcur = self.conn.cursor()
        dbcur.execute("SELECT * FROM {} WHERE 1=0".format(table))
        return [desc[0] for desc in dbcur.description]

    def gettables_in_schema(self, schema):
        query = """ SELECT * FROM information_schema.tables
                    WHERE table_schema = %s"""
        dbcur = self.conn.cursor()
        dbcur.execute(query, (schema, ))
        return dbcur.fetchall()

    def table_exists(self, schema, table):
        query = """SELECT EXISTS( SELECT 1 FROM pg_tables
                    WHERE schemaname = (%s) AND
                          tablename = (%s)
            );"""
        dbcur = self.conn.cursor()
        dbcur.execute(query, (schema, table))
        return dbcur.fetchone()[0]

    def run_sql_script(self, script_name) -> list:
        """
        Runs the sql script against the database
        :param script_name:
        :return:
        """
        return self.run_sql(open(script_name, 'r', encoding="utf-8").read())

    def get_ogr2_ogr_login(self, schema, dbname):
        log.info(
            'Logging into {}:{} db {}.{}'.format(self.host, self.port, dbname,
                                                 schema))
        return "host={} port={} ACTIVE_SCHEMA={} user={} " \
               "dbname={} password={}".format(self.host, self.port,
                                              schema, self.user, dbname,
                                              self.password)

    def import_basiskaart(self, path_to_shp, schema):
        os.putenv('PGCLIENTENCODING', 'UTF8')

        log.info('import schema {} in {}'.format(path_to_shp, schema))
        for root, dirs, files in os.walk(path_to_shp, topdown=False):
            log.info('Processing {} with dirs {}'.format(root, dirs))
            for file in files:
                if os.path.splitext(file)[1] == '.shp':
                    log.info('Importing {}'.format(root + '/' + file))
                    subprocess.call(
                        'ogr2ogr -nlt PROMOTE_TO_MULTI -progress -skipfailures '
                        '-overwrite -f "PostgreSQL" '
                        'PG:"{PG}" -gt 655360 -s_srs "EPSG:28992" -t_srs '
                        '"EPSG:28992" {LCO} {CONF} {FNAME}'.format(
                            PG=self.get_ogr2_ogr_login(schema, 'basiskaart'),
                            LCO='-lco SPATIAL_INDEX=OFF -lco PRECISION=NO -lco '
                                'LAUNDER=NO -lco GEOMETRY_NAME=geom',
                            CONF='--config PG_USE_COPY YES',
                            FNAME=root + '/' + file), shell=True)


def createdb():
    try:
        SQLRunner(host=DATABASE['HOST'],
                  port=DATABASE['PORT'],
                  dbname=DATABASE['NAME'],
                  user=DATABASE['USER'],
                  password=DATABASE['PASSWORD'])
    except psycopg2.OperationalError:

        sqlconn = SQLRunner(host=DATABASE['HOST'],
                            port=DATABASE['PORT'],
                            dbname=DATABASE['NAME'],
                            user=DATABASE['USER'],
                            password=DATABASE['PASSWORD'])

        sqlconn.run_sql('CREATE DATABASE basiskaart;')
        sqlconn.commit()
        sqlconn.close()
