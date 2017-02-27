# -*- coding: utf-8 -*-
import logging
import os

from openpyxl import load_workbook

from sql_utils.sql_utils import SQLRunner

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
    for idx, row in enumerate(wb['Blad1'].rows):
        rowvalues = [r.value for r in row]
        schema, tabel, categorie, geotype, viewnm, vwattr, laag, grp, minhoogte, maxhoogte = rowvalues

        if idx >= startvalue:
            viewname = '"{}"."{}_{}<hoogteligging>"'.format(schema.lower(),
                                                            categorie, geotype)
            if sql.table_exists(schema.lower(), tabel):
                if viewname not in view_definitions:
                    view_definitions[viewname] = []
                view_definitions[viewname] += [
                    [schema.lower(), tabel, vwattr, minhoogte, maxhoogte]]
            else:
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
                            minval,
                            maxval])

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
    single_select = 'SELECT {} FROM "{}"."{}" WHERE relatievehoogteligging = {}'

    for hoogte in range(minvalue, maxvalue):
        selects = []

        for schema, tabel, vwattr, minval, maxval in viewdef:
            selects.append(
                single_select.format(vwattr, schema, tabel, hoogte))

        real_viewname = viewname.replace('<hoogteligging>',
                                         str(hoogte).replace('-', '_'))
        sql.run_sql(viewstmt.format(real_viewname, " UNION ".join(selects)))


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
