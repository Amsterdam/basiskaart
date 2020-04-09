# -*- coding: utf-8 -*-
import logging

import os
from openpyxl import load_workbook

from sql_utils.sql_utils import SQLRunner
from .basiskaart_setup import MAX_NR_OF_UNAVAILABLE_TABLES
from .basiskaart import fieldmapping

log = logging.getLogger(__name__)

XLS_VIEWDEF = os.path.dirname(
    os.path.realpath(__file__)) + '/fixtures/wms_kaart_database.xlsx'

sql = SQLRunner()


def create_views_based_on_workbook():
    view_definitions = validate_workbook()
    create_all_views(view_definitions)


def missing_table(tables_unavailable, table, viewname):
    """
    Handle missing table errors
    """

    tables_unavailable += 1

    if tables_unavailable > MAX_NR_OF_UNAVAILABLE_TABLES:
        raise Exception("""
            'More than {MAX_NR_OF_UNAVAILABLE_TABLES} unavailable
            'tables, input is unreliable!""")

    log.warning(
        "Table %s for view %s does not exist, "
        "processing continues", table, viewname)


def validate_workbook():
    """
    We check if all needed tables are created

    excel workbook with table <-> mapserver relations
    which defines what kind of views are needed.

    We return dict with viewnames mapped to table source data
    """
    validated_view_definitions = {}

    wb = load_workbook(XLS_VIEWDEF)
    startvalue = 1
    tables_unavailable = 0

    for idx, row in enumerate(wb['Blad1'].rows):

        # skip header lines
        if not idx >= startvalue:
            continue

        row_values = [r.value for r in row]

        schema, table, categorie, geotype,  \
            _viewname, viewattr, _laag, _grp,  \
            _minhoogte, _maxhoogte = row_values

        schema_lower = schema.lower()

        viewname = f'"{schema_lower}"."{categorie}_{geotype}<hoogteligging>"'

        log.debug(viewname)

        if sql.table_exists(schema_lower, table):

            if viewname not in validated_view_definitions:
                validated_view_definitions[viewname] = []

            validate_columns(viewname, schema_lower, table, viewattr)

            validated_view_definitions[viewname].append([
                schema_lower, table, [viewattr]
            ])

        else:
            missing_table(tables_unavailable, table, viewname)
            # table is missing...

    return validated_view_definitions


def create_all_views(view_definitions):
    """
    Geven validated defenitions from  xls sheet
    create views whitin 'hoogteligging'
    """

    for viewname, viewdef in view_definitions.items():
        # determine min and max hight values
        minvalue, maxvalue = high_lowvalue(viewdef)
        create_views(viewname, viewdef, minvalue, maxvalue)


def high_lowvalue(viewdef):
    """
    Determine min and max hoogte layers for
    """
    selects = []
    single_select = 'SELECT relatievehoogteligging FROM "{}"."{}"'

    for schema, table, _columnnames in viewdef:
        selects.append(single_select.format(schema, table))

    unionselect = ' UNION '.join(selects)

    result = sql.run_sql(
        'select min(relatievehoogteligging), '
        'max(relatievehoogteligging) from ({}) '
        'as subunion'.format(
            unionselect))

    return result[0][0], result[0][1]


def create_views(viewname, viewdef, minvalue, maxvalue):
    """
    For each viewname create a view for each 'hoogteligging'
    """

    viewstmt = """
    DROP MATERIALIZED VIEW IF EXISTS {} CASCADE;
    CREATE MATERIALIZED VIEW {} AS {} WITH DATA
    """

    single_select = 'SELECT {} FROM "{}"."{}" ' \
                    'WHERE relatievehoogteligging = {}'

    for hoogte in range(minvalue, maxvalue + 1):

        # create selects for involved tables
        selects = []
        for schema, tabel, columns in viewdef:

            if 'geometrie' not in columns:
                columns.append('geometrie')

            columns = ', '.join(columns)

            selects.append(
                single_select.format(columns, schema, tabel, hoogte))

        # determine the viewname with hoogte ligging
        real_viewname = viewname.replace('<hoogteligging>', str(hoogte))
        # replace -2 to _2
        real_viewname = real_viewname.replace('-', '_')

        # create the view with combined table data
        sql.run_sql_no_results(
            viewstmt.format(
                real_viewname, real_viewname, " UNION ".join(selects)))


def geo_index(schema, table, geo_field):
    """
    Create index on geo_field
    """

    table_lower = table.lower()

    s = f"""
    SET SEARCH_PATH TO {schema};
    CREATE INDEX IF NOT EXISTS index_{table_lower}_gist ON "{table}"
    USING gist({geo_field});
    CLUSTER "{table}" USING "index_{table_lower}_gist";
    """

    sql.run_sql(s)


def create_geo_indexes(schema, table, columns):
    """
    Create geo indexes on geometrie fields
    """

    for geo_field in ['geometrie', 'geom']:
        if geo_field in columns:
            geo_index(schema, table, geo_field)


def create_table_indexes(schema, table, columns):
    """
    create table and geometrie index
    """
    log.info("Create GEO indexes for %s.%s", schema, table)
    log.info("ON columns  %s", columns)

    create_geo_indexes(schema, table, columns)

    # create field indexes (who needs those..)
    for column in columns:
        log.info(f"Create column index on {table} for {column}")

        if column in ['id', 'geometrie', 'geom']:
            continue

        sql.run_sql(f"""
        SET SEARCH_PATH TO {schema};
        CREATE INDEX IF NOT EXISTS index_{table}_{column} ON "{table}"
        USING BTREE ("{column}");""")


def make_indexes_on_all_tables(schema):

    table_names = [c[2] for c in sql.get_tables_in_schema(schema)]

    for table_name in table_names:
        table = table_name.replace('-', '_')

        if not sql.table_exists(schema, table):
            # should never happen..
            continue

        column_names = sql.get_columns_from_table(f'{schema}."{table}"')

        create_table_indexes(schema, table, column_names)


def make_geoindexes_on_all_matviews(schema):
    """
    Create geo indexes on views
    """

    view_names = [c[1] for c in sql.get_views_in_schema(schema)]

    for view_name in view_names:
        column_names = sql.get_columns_from_table(f'{schema}."{view_name}"')
        create_geo_indexes(schema, view_name, column_names)


def create_indexes():
    """
    Create GEO indexes and column btree indexes for all schemas
    """
    for schema in ['kbk10', 'kbk25', 'kbk50', 'bgt']:
        make_indexes_on_all_tables(schema)
        make_geoindexes_on_all_matviews(schema)


# Keep track of columns, views and counts to
# be able to report errors..
COLUMN_VIEW_TRACKER = {}
COLUMN_LEN_TRACKER = {}


def validate_columns(viewname, schema, table, columnnames):
    """
    Check if column names defined in xls sheet do actualy
    exists and have equal amount of columns on all unionized tables
    """

    sql_table_name = '"{}"."{}"'.format(schema, table)
    found_columns = sql.get_columns_from_table(sql_table_name)

    columns_in_xls = [
        field.strip() for field in columnnames.split(',')]

    table_key = f'{schema}.{table}'
    len_columns = len(columns_in_xls)

    if table_key not in COLUMN_LEN_TRACKER:
        COLUMN_LEN_TRACKER[table_key] = len_columns
        COLUMN_VIEW_TRACKER[table_key] = columns_in_xls

    if len_columns != COLUMN_LEN_TRACKER[table_key]:
        raise ValueError(
            "WRONG NUMBER OF COLUMNS:",
            viewname,
            len_columns, COLUMN_LEN_TRACKER[table_key],
            COLUMN_VIEW_TRACKER[table_key],
            schema, table, columns_in_xls)

    for needed_column in columns_in_xls:
        if needed_column == 'null':
            continue
        if needed_column not in found_columns:
            raise ValueError(
                "WRONG COLUMNS:",
                schema, table, columnnames)


def define_fields(tabel, schema, vwattr):
    sql_table_name = '"{}"."{}"'.format(schema, tabel)
    vwattr += ', geometrie'
    foundcolumns = sql.get_columns_from_table(sql_table_name)
    required_columns_input = [field.strip() for field in vwattr.split(',')]
    required_columns = [fieldmapping.get(c, c) for c in required_columns_input]

    columns_not_found = ['"' + column + '"' for column in required_columns if
                         column not in foundcolumns]
    required_columns = ['"' + column + '"' for column in required_columns]

    for not_found in columns_not_found:
        idx = required_columns.index(not_found)
        required_columns[idx] = 'NULL as ' + not_found
        log.warning(
            "Table %s column %s does not exist, processing continues",
            tabel,
            not_found)

    vwattr = ', '.join(required_columns)

    return vwattr
