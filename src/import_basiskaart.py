"""
All commands to create a basiskaart
"""

import argparse
import logging

from basiskaart.basiskaart import process_basiskaart
from basiskaart.hoogteligging import create_views_based_on_workbook, create_indexes

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

args = parser.parse_args()


def handle_import(args):

    if args.listsourcefiles:
        process_basiskaart(args.basiskaart, list_source_files=True)
        return

    if not args.viewsonly:
        process_basiskaart(args.basiskaart)
        create_indexes()

    if not args.no_views and (
            'bgt' in args.basiskaart or 'all' in args.basiskaart):
        LOG.info(" Views voor basiskaart worden gebouwd")
        create_views_based_on_workbook()
        create_indexes()

if __name__ == '__main__':
    LOG.info(" Basiskaart bouw gestart voor %s", args.basiskaart)
    handle_import(args)
