import logging

from swiftclient.client import Connection

from basiskaart_setup import BASISKAART_OBJECTSTORE_PASSWORD
from basiskaart_setup import BGT_OBJECTSTORE_PASSWORD

log = logging.getLogger(__name__)

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("swiftclient").setLevel(logging.WARNING)

OBJECTSTORE = {
    'auth_version': '2.0',
    'authurl': 'https://identity.stack.cloudvps.com/v2.0',
    'user': None,
    'key': None,
    'tenant_name': 'BGE000081_BAG',
    'os_options': {
        'tenant_id': None,
        'region_name': 'NL'}
}


class ObjectStore:
    RESP_LIMIT = 10000  # serverside limit of the response

    def __init__(self, container, name):
        if name == 'bag_brk':
            OBJECTSTORE['user'] = 'bag_brk'
            OBJECTSTORE['key'] = BASISKAART_OBJECTSTORE_PASSWORD
            OBJECTSTORE['os_options'][
                'tenant_id'] = '4f2f4b6342444c84b3580584587cfd18'
            OBJECTSTORE['tenant_name'] = 'BGE000081_BAG'
        else:
            OBJECTSTORE['user'] = 'basiskaart'
            OBJECTSTORE['key'] = BGT_OBJECTSTORE_PASSWORD
            OBJECTSTORE['os_options'][
                'tenant_id'] = '1776010a62684386a08b094d89ce08d9'
            OBJECTSTORE['tenant_name'] = 'BGE000081_BGT'

        self.conn = Connection(**OBJECTSTORE)
        self.container = container

    def get_store_object(self, name):
        """
        Returns the object store
        :param name:
        :return:
        """
        return self.conn.get_object(self.container, name)[1]

    def get_store_objects(self, path):
        return self._get_full_container_list([], prefix=path)

    def _get_full_container_list(self, seed, **kwargs):

        kwargs['limit'] = self.RESP_LIMIT
        if len(seed):
            kwargs['marker'] = seed[-1]['name']

        _, page = self.conn.get_container(self.container, **kwargs)
        seed.extend(page)
        return seed if len(
            page) < self.RESP_LIMIT else self._get_full_container_list(seed,
                                                                       **kwargs)

    def folders(self, path):
        objects_from_store = self._get_full_container_list([], delimiter='/',
                                                           prefix=path)
        return [store_object['subdir'] for store_object in objects_from_store if
                'subdir' in store_object]

    def files(self, path, file_id):
        file_list = self._get_full_container_list(
            [], delimiter='/', prefix=path + file_id)

        for file_object in file_list:
            file_object['container'] = self.container
        return file_list

    def put_to_objectstore(self, object_name, object_content, content_type):
        return self.conn.put_object(self.container, object_name,
                                    contents=object_content,
                                    content_type=content_type)

    def delete_from_objectstore(self, object_name):
        return self.conn.delete_object(self.container, object_name)
