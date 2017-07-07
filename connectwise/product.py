# import math
#
# import constants
# from lib.connectwise_py.connectwise.ticket import Ticket
# from lib.connectwise_py.connectwise.time_entry import TimeEntry
# from .system_report import SystemReport
from .connectwise import Connectwise


class Product:
    def __init__(self, **kwargs):
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    def __repr__(self):
        return "<Product {}>".format(self.description)

    @classmethod
    def fetch_all(cls):
        return [cls(**product) for product in Connectwise.submit_request('procurement/products')]

    @classmethod
    def fetch_by_id(cls, _id):
        conditions = ['id={}'.format(_id)]
        return [cls(**product) for product in Connectwise.submit_request('procurement/products', conditions)][0]

    @classmethod
    def fetch_by_description(cls, description):
        conditions = ['description contains "{}"'.format(description)]
        return [cls(**product) for product in Connectwise.submit_request('procurement/products', conditions)]

    @classmethod
    def fetch_by_catalog_item_id(cls, catalog_item_id):
        conditions = ['catalogItem/id={}'.format(catalog_item_id)]
        return [cls(**product) for product in Connectwise.submit_request('procurement/products', conditions)]

    @classmethod
    def fetch_by_subcategory_id(cls, subcategory_id):
        catalog_product_ids = [cp.id for cp in CatalogProduct.fetch_by_subcategory_id(subcategory_id)]
        products = []
        for catalog_product_id in catalog_product_ids:
            products.extend(cls.fetch_by_catalog_item_id(catalog_product_id))
        return products


class CatalogProduct:
    def __init__(self, **kwargs):
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    def __repr__(self):
        return "<Product {}>".format(self.identifier)

    @classmethod
    def fetch_all(cls):
        return [cls(**catalog_product) for catalog_product in Connectwise.submit_request('procurement/catalog')]

    @classmethod
    def fetch_by_id(cls, _id):
        conditions = ['id={}'.format(_id)]
        return [cls(**catalog_product) for catalog_product in
                Connectwise.submit_request('procurement/catalog', conditions)][0]

    @classmethod
    def fetch_by_description(cls, description):
        conditions = ['description contains "{}"'.format(description)]
        return [cls(**catalog_product) for catalog_product in
                Connectwise.submit_request('procurement/catalog', conditions)]

    @classmethod
    def fetch_by_category_id(cls, category_id):
        conditions = ['category/id={}'.format(category_id)]
        return [cls(**catalog_product) for catalog_product in
                Connectwise.submit_request('procurement/catalog', conditions)]

    @classmethod
    def fetch_by_subcategory_id(cls, subcategory_id):
        conditions = ['subcategory/id={}'.format(subcategory_id)]
        return [cls(**catalog_product) for catalog_product in
                Connectwise.submit_request('procurement/catalog', conditions)]