import mimetypes
import os
import os.path

import pytest

from objectstore.objectstore import ObjectStore


@pytest.fixture
def objectstore():
    return ObjectStore('BAG', 'basiskaart')


@pytest.mark.skip(reason='no tests to objectstore, copied from other project')
def test_objects(objectstore):
    # clean up
    stored_objects = objectstore._get_full_container_list([])
    for ob in stored_objects:
        if ob['name'].startswith('bgttest/'):
            objectstore.delete_from_objectstore(ob['name'])

    res = objectstore._get_full_container_list([], prefix='bgttest/')
    assert len(res) == 0

    objects = []
    for filename in os.listdir(
            os.path.join(os.path.dirname(__file__), 'fixtures')):
        objects.append(filename)
    assert len(objects) == 5

    for ob in objects:
        ob_name = ob.split('/')[-1]
        content = open(os.path.join(os.path.dirname(__file__), 'fixtures', ob),
                       'rb').read()
        content_type = mimetypes.MimeTypes().guess_type(ob)[0]
        if not content_type:
            content_type = "application/octet-stream"
        objectstore.put_to_objectstore('bgttest/{}'.format(ob_name), content,
                                       content_type)

    res = objectstore._get_full_container_list([], prefix='bgttest/')
    assert len(res) == 5
