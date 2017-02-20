from openpyxl import load_workbook

VIEWS = './fixtures/%s_wms_kaart_database.xlsx'


def create_views_based_on_workbook():
    work_list = []
    wb = load_workbook(VIEWS)
    for rows in wb['Blad1']:
        work_list.append(rows)

