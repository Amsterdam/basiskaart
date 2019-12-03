# -*- coding: utf-8 -*-

import json
import os.path
import re
import logging

logging.basicConfig(level=logging.DEBUG)


def get_docker_host():
    """
    Looks for the DOCKER_HOST environment variable to find the VM
    running docker-machine.

    If the environment variable is not found, it is assumed that
    you're running docker on localhost.
    """
    d_host = os.getenv('DOCKER_HOST', None)
    if d_host:
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', d_host):
            return d_host

        return re.match(r'tcp://(.*?):\d+', d_host).group(1)
    return 'localhost'


def in_docker():
    """
    Checks pid 1 cgroup settings to check with reasonable certainty we're in a
    docker env.
    :return: true when running in a docker container, false otherwise
    """
    # noinspection PyBroadException
    try:
        return ':/docker/' in open('/proc/1/cgroup', 'r').read()
    except Exception:
        return False


OVERRIDE_HOST_ENV_VAR = 'DATABASE_HOST_OVERRIDE'
OVERRIDE_PORT_ENV_VAR = 'DATABASE_PORT_OVERRIDE'

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class LocationKey:
    local = 'local'
    docker = 'docker'
    override = 'override'


def get_database_key():
    if os.getenv(OVERRIDE_HOST_ENV_VAR):
        return LocationKey.override
    elif in_docker():
        return LocationKey.docker

    return LocationKey.local


DATABASE_OPTIONS = {
    LocationKey.docker: {
        'NAME': os.getenv('DATABASE_NAME', 'basiskaart'),
        'USER': os.getenv('DATABASE_USER', 'basiskaart'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'insecure'),
        'HOST': 'database',
        'PORT': '5432'
    },
    LocationKey.local: {
        'NAME': os.getenv('DATABASE_NAME', 'basiskaart'),
        'USER': os.getenv('DATABASE_USER', 'basiskaart'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'insecure'),
        'HOST': get_docker_host(),
        'PORT': '5402'
    },
    LocationKey.override: {
        'NAME': os.getenv('DATABASE_NAME', 'basiskaart'),
        'USER': os.getenv('DATABASE_USER', 'basiskaart'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'insecure'),
        'HOST': os.getenv(OVERRIDE_HOST_ENV_VAR),
        'PORT': os.getenv(OVERRIDE_PORT_ENV_VAR, '5432')
    },
}

DATABASE = DATABASE_OPTIONS[get_database_key()]

TEST_KEYS = os.path.expanduser('~/keys.env')

GOB_OBJECTSTORE_PASSWORD = None
BGT_OBJECTSTORE_PASSWORD = None
if os.path.exists(TEST_KEYS):
    with open(TEST_KEYS, 'r') as testkeys:
        files = json.load(testkeys)
        if 'bag_brk' in files:
            GOB_OBJECTSTORE_PASSWORD = files['bag_brk']
        if 'basiskaart' in files:
            BGT_OBJECTSTORE_PASSWORD = files['basiskaart']

if not GOB_OBJECTSTORE_PASSWORD:
    GOB_OBJECTSTORE_PASSWORD = os.getenv(
        'GOB_OBJECTSTORE_PASSWORD', 'insecure')
if not BGT_OBJECTSTORE_PASSWORD:
    BGT_OBJECTSTORE_PASSWORD = os.getenv(
        'BGT_OBJECTSTORE_PASSWORD', 'insecure')

DEBUG = os.getenv('DEBUG', False) == '1'

gob_env = os.getenv('GOB_OBJECTSTORE_ENV', "acceptatie")

KBK10 = {
    'objectstore': "gob",
    'container': "acceptatie",
    'source_path': "brt/kbka10",
    'target_dir': "/app/basiskaartdata/kbk10",
    'filters': ["Esri_Shape"],
    'suffix': "",
    'is_zips': False,
    'schema': "kbk10"
}

KBK50 = {
    'objectstore': "gob",
    'container': "acceptatie",
    'source_path': "brt/kbka50",
    'target_dir': "/app/basiskaartdata/kbk50",
    'filters': ["Esri_Shape"],
    'suffix': "",
    'is_zips': False,
    'schema': "kbk50"
}

KBK25 = {
    'objectstore': "gob",
    'container': "acceptatie",
    'source_path': "brt/kbka25",
    'target_dir': "/app/basiskaartdata/kbk50",
    'filters': ["Esri_Shape"],
    'suffix': "",
    'is_zips': False,
    'schema': "kbk25"
}

BGT = {
    'objectstore': "basiskaart",
    'container': "BGT",
    'source_path': "Basiskaart",
    'target_dir': "/app/basiskaartdata/bgt",
    'filters': ["Esri_Shape_totaal"],
    'suffix': "-latest.zip",
    'is_zips': True,
    'schema': "bgt"
}

SOURCE_DATA_MAP = {
    'kbk10': (KBK10,),
    'bgt': (BGT,),
    'kbk25': (KBK25,),
    'kbk50': (KBK50,),
    'all': (KBK25, KBK10, KBK50, BGT)
}

MAX_NR_OF_UNAVAILABLE_TABLES = 8
