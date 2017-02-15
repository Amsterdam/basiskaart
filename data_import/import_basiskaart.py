"""
All commands to create a basiskaart
"""

import argparse
import logging

from data_import.basiskaart import process_bk

LOG = logging.getLogger(__name__)

parser = argparse.ArgumentParser(
    description='Process import of basiskaart 10/50')
parser.add_argument(
    '--basiskaart',
    action='store',
    default='all',
    help='Select which basiskaart to import',
    choices=['all', 'kbk10', 'kbk50', 'bgt'])
args = parser.parse_args()

process_bk(args.basiskaart)
