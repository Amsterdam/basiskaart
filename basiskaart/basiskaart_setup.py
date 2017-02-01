import json
import os.path

SCRIPT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'basiskaart'))
TEST_KEYS = os.path.expanduser('~/keys.env')

BASISKAART_OBJECTSTORE_PASSWORD = None
BGT_OBJECTSTORE_PASSWORD = None
if os.path.exists(TEST_KEYS):
    with open(TEST_KEYS, 'r') as testkeys:
        files = json.load(testkeys)
        if 'bag_brk' in files:
            BASISKAART_OBJECTSTORE_PASSWORD = files['bag_brk']
        if 'basiskaart' in files:
            BGT_OBJECTSTORE_PASSWORD = files['basiskaart']

if not BASISKAART_OBJECTSTORE_PASSWORD:
    BASISKAART_OBJECTSTORE_PASSWORD = os.getenv(
        'BASISKAART_OBJECTSTORE_PASSWORD', 'insecure')
if not BGT_OBJECTSTORE_PASSWORD:
    BGT_OBJECTSTORE_PASSWORD = os.getenv('BGT_OBJECTSTORE_PASSWORD', 'insecure')

DEBUG = os.getenv('DEBUG', False) == '1'
SCRIPT_SRC = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'src'))

BASISKAART_DBPASS = os.getenv('DB_PASSWORD', 'insecure')

BASISKAART_USER = os.getenv('DB_USER', 'basiskaart')
BASISKAART_HOST = os.getenv('DB_HOST', 'localhost')
BASISKAART_DBNAME = os.getenv('DB_NAME', 'basiskaart')
BASISKAART_PW = os.getenv('DB_PASSWORD', 'insecure')
BASISKAART_PORT = os.getenv('DB_PORT', '5402')
