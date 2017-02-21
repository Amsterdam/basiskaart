from openpyxl import load_workbook

from sql_utils import SQLRunner

XLS_VIEWDEF = '../fixtures/20170216_wms_kaart_database.xlsx'


def create_views_based_on_workbook():
    view_definitions = read_workbook()
    min_max_values = get_min_max_value(view_definitions)
    create_view(view_definitions, min_max_values)


def read_workbook():
    view_definitions = {}
    wb = load_workbook(XLS_VIEWDEF)
    startvalue = 1
    for idx, row in enumerate(wb['Blad1'].rows):
        rowvalues = [r.value for r in row]
        schema, tabel, categorie, geotype, viewnm, vwattr, laag, grp, minhoogte, maxhoogte = rowvalues
        if idx >= startvalue:
            viewname = '"{}"."{}_{}<hoogteligging>"'.format(schema.lower(), categorie, geotype)
            if viewname not in view_definitions:
                view_definitions[viewname] = []
            view_definitions[viewname] += [[schema.lower(), tabel, vwattr, minhoogte, maxhoogte]]
    return view_definitions


def get_min_max_value(view_definitions):
    min_max_values = {}
    for viewname, viewdef in view_definitions.items():
        for viewrow in viewdef:
            minvalue = viewrow[3]
            maxvalue = viewrow[4]
            if viewname not in min_max_values:
                min_max_values[viewname] = [0, 0]
            if min_max_values[viewname][0] > minvalue:
                min_max_values[viewname][0] = minvalue
            if min_max_values[viewname][1] < maxvalue:
                min_max_values[viewname][1] = maxvalue
    return min_max_values


def create_view(view_definitions, min_max_values):
    sql = SQLRunner()

    viewstmt = 'CREATE OR REPLACE VIEW {} AS {}'
    single_select = 'SELECT {} FROM "{}"."{}" WHERE hoogtelig = {}'

    for viewname, viewdef in view_definitions.items():
        minvalue = min_max_values[viewname][0]
        maxvalue = min_max_values[viewname][1]

        for hoogte in range(minvalue, maxvalue):
            selects = []

            for schema, tabel, vwattr, minval, maxval in viewdef:
                selects.append(single_select.format(vwattr, schema, tabel, hoogte))

            real_viewname = viewname.replace('<hoogteligging>', str(hoogte).replace('-','_'))
            sql.run_sql(viewstmt.format(real_viewname, " UNION ".join(selects)))
