# -*- coding: utf-8 -*-
import logging

import os
from openpyxl import load_workbook

from sql_utils.sql_utils import SQLRunner
from .basiskaart_setup import MAX_NR_OF_UNAVAILABLE_TABLES

log = logging.getLogger(__name__)

XLS_VIEWDEF = os.path.dirname(
    os.path.realpath(__file__)) + '/fixtures/wms_kaart_database.xlsx'

sql = SQLRunner()


def create_views_based_on_workbook():
    view_definitions = read_workbook()
    create_view(view_definitions)


def read_workbook():
    view_definitions = {}
    wb = load_workbook(XLS_VIEWDEF)
    startvalue = 1
    tables_unavailable = 0
    for idx, row in enumerate(wb['Blad1'].rows):
        schema, tabel, categorie, geotype, viewnm, vwattr, laag, grp, minhoogte, maxhoogte = [
            r.value for r in row
        ]

        if idx >= startvalue:
            viewname = '"{}"."{}_{}<hoogteligging>"'.format(schema.lower(),
                                                            categorie, geotype)
            if sql.table_exists(schema.lower(), tabel):
                if viewname not in view_definitions:
                    view_definitions[viewname] = []
                view_definitions[viewname] += [
                    [schema.lower(), tabel, vwattr, minhoogte, maxhoogte]]
            else:
                tables_unavailable += 1
                if tables_unavailable > MAX_NR_OF_UNAVAILABLE_TABLES:
                    raise Exception(
                        'More than {MAX_NR_OF_UNAVAILABLE_TABLES} unavailable tables, input is unreliable!')
                log.warning(
                    "Table {} in view {} does not exist, "
                    "processing continues".format(
                        tabel,
                        viewname))

    return view_definitions


def create_view(view_definitions):
    for viewname, viewdef in view_definitions.items():
        minvalue, maxvalue = high_lowvalue(viewdef)
        build_view_per_name(viewname, viewdef, minvalue, maxvalue)


def build_view_per_name(viewname, viewdef, minvalue, maxvalue):
    new_viewdef = []
    for schema, tabel, vwattr, minval, maxval in viewdef:
        new_viewdef.append([schema,
                            tabel,
                            define_fields(tabel, schema, vwattr),
                            minvalue,
                            maxvalue])

    create_views(viewname, new_viewdef, minvalue, maxvalue)


def high_lowvalue(viewdef):
    selects = []
    single_select = 'SELECT relatievehoogteligging FROM "{}"."{}"'
    for schema, tabel, vwattr, minval, maxval in viewdef:
        selects.append(single_select.format(schema, tabel))
    unionselect = ' UNION '.join(selects)
    result = sql.run_sql(
        'select min(relatievehoogteligging), '
        'max(relatievehoogteligging) from ({}) '
        'as subunion'.format(
            unionselect))
    return result[0][0], result[0][1]


def create_views(viewname, viewdef, minvalue, maxvalue):
    viewstmt = "CREATE OR REPLACE VIEW {} AS {}"
    single_select = 'SELECT {} FROM "{}"."{}" ' \
                    'WHERE relatievehoogteligging = {}'

    for hoogte in range(minvalue, maxvalue + 1):
        selects = []

        for schema, tabel, vwattr, minval, maxval in viewdef:
            selects.append(
                single_select.format(vwattr, schema, tabel, hoogte))

        real_viewname = viewname.replace('<hoogteligging>',
                                         str(hoogte).replace('-', '_'))
        sql.run_sql(viewstmt.format(real_viewname, " UNION ".join(selects)))


def create_table_indexes(schema, table, columns):
    """
    create table and geometrie index
    """
    log.info(f"Create GEO indexes and cluster table for {schema}.{table}")
    if 'geometrie' in columns:
        s = f"""
        SET SEARCH_PATH TO {schema};
        DROP INDEX IF EXISTS index_{table.lower()}_geo;
        DROP INDEX IF EXISTS index_{table.lower()}_gist;
        CREATE INDEX index_{table.lower()}_gist ON "{table}" USING gist(geometrie);
        CLUSTER "{table}" USING "index_{table.lower()}_gist";
        """
        sql.run_sql(s)
    # create field indexes
    for column in columns:
        log.info(f"Create column index on {table} for {column}")
        if column not in ['id', 'geometrie']:
            try:
                sql.run_sql(f"""
                SET SEARCH_PATH TO {schema};
                CREATE INDEX index_{table}_{column} ON "{table}" USING BTREE ({column});""")
            except:
                pass


def create_indexes():
    """
    Create GEO indexes and column btree indexes for all schemas
    """
    for schema in ['kbk10', 'kbk50', 'bgt']:
        table_names = [c[2] for c in sql.gettables_in_schema(schema)]
        for table_name in table_names:
            if sql.table_exists(schema, table_name):
                column_names = sql.get_columns_from_table(f'{schema}."{table_name}"')
                create_table_indexes(schema, table_name, column_names)


def define_fields(tabel, schema, vwattr):
    sql_table_name = '"{}"."{}"'.format(schema, tabel)
    foundcolumns = sql.get_columns_from_table(sql_table_name)
    required_columns = [field.strip() for field in vwattr.split(',')]
    columns_not_found = ['"' + column + '"' for column in required_columns if
                         column not in foundcolumns]
    required_columns = ['"' + column + '"' for column in required_columns]

    for not_found in columns_not_found:
        idx = required_columns.index(not_found)
        required_columns[idx] = 'NULL as ' + not_found
        log.warning(
            "Table {} column {} does not exist, processing continues".format(
                tabel,
                not_found))

    vwattr = ', '.join(required_columns)

    return vwattr
