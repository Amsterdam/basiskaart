import os
import shutil

from basiskaart import fill_basiskaart
from basiskaart_setup import VALUES


# Geen testen voor retrieval van files vanaf objectstore. Bestaande code....

def test_kbk10():
    shutil.rmtree(VALUES['kbk10'][0][1], ignore_errors=True)
    os.path.realpath(__file__)
    shutil.copytree(
        os.path.dirname(os.path.realpath(__file__)) + '/fixtures/ZeeExt',
        VALUES['kbk10'][0][1])
    fill_basiskaart(VALUES['kbk10'][0][1], 'kbk10')


def test_kbk50():
    shutil.rmtree(VALUES['kbk50'][0][1], ignore_errors=True)
    shutil.copytree(
        os.path.dirname(os.path.realpath(__file__)) + '/fixtures/kbka50_plus',
        VALUES['kbk50'][0][1])
    fill_basiskaart(VALUES['kbk50'][0][1], 'kbk50')
