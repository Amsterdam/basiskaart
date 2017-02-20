from openpyxl import load_workbook
import os

VIEWS = '../fixtures/20170216_wms_kaart_database.xlsx'


def create_views_based_on_workbook():
    work_list = []
    wb = load_workbook(VIEWS)
    startvalue = 1
    for idx, row in enumerate(wb['Blad1'].rows):
        if idx >= startvalue:
            viewname = row[4]
            if viewname in work_list:
                work_list[viewname],append(row)
            else:
                work_list[viewname] = [row]

    for viewname, viewdef in work_list.items():
        print(r)