"""
All commands to create a basiskaart
"""

import argparse
import logging

from basiskaart.basiskaart import process_basiskaart
from basiskaart.hoogteligging import create_views_based_on_workbook
from basiskaart.hoogteligging import create_indexes

LOG = logging.getLogger(__name__)

parser = argparse.ArgumentParser(
    description='Process import of basiskaart 10/50')
parser.add_argument(
    '--basiskaart',
    action='store',
    default='all',
    help='Select which basiskaart to import',
    choices=['all', 'kbk10', 'kbk25', 'kbk50', 'bgt'])
parser.add_argument(
    '--no_views',
    action='store_true',
    default=False,
    help='Do not generate views')
parser.add_argument(
    '--viewsonly',
    action='store_true',
    default=False,
    help='Only generrate views')

parser.add_argument(
    '--listsourcefiles',
    action='store_true',
    default=False,
    help='list objectstore source files')

parser.add_argument(
    '--createindexes',
    action='store_true',
    default=False,
    help='create indexes on geometrie')

args = parser.parse_args()


def handle_import(userargs):

    if userargs.listsourcefiles:
        # show which zip files will be downloaded.
        process_basiskaart(userargs.basiskaart, only_list_source_files=True)
        return

    if userargs.createindexes:
        create_indexes()
        return

    if userargs.viewsonly:
        create_views_based_on_workbook()
        return

    if not userargs.no_views and (
            'bgt' in userargs.basiskaart or 'all' in userargs.basiskaart):
        # import specific dataset
        LOG.info(" Views voor basiskaart worden gebouwd")
        process_basiskaart(userargs.basiskaart)
        create_views_based_on_workbook()
        create_indexes()


if __name__ == '__main__':
    LOG.info(" Basiskaart bouw gestart voor %s", args.basiskaart)
    handle_import(args)
