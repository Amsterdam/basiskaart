import shutil

import basiskaart_setup
from basiskaart.basiskaart import basiskaart


# Geen testen voor retrieval van files vanaf objectstore. Bestaande code....

def test_kbk10():
    shutil.rmtree(basiskaart.VALUES['kbk10'][0][1], ignore_errors=True)
    shutil.copytree(
        basiskaart_setup.SCRIPT_ROOT + '/basiskaart/tests/fixtures/ZeeExt',
        basiskaart.VALUES['kbk10'][0][1])
    basiskaart.fill_bk(basiskaart.VALUES['kbk10'][0][1], 'kbk10')


def test_kbk50():
    shutil.rmtree(basiskaart.VALUES['kbk50'][0][1], ignore_errors=True)
    shutil.copytree(
        basiskaart_setup.SCRIPT_ROOT + '/basiskaart/tests/fixtures/kbka50_plus',
        basiskaart.VALUES['kbk50'][0][1])
    basiskaart.fill_bk(basiskaart.VALUES['kbk50'][0][1], 'kbk50')
