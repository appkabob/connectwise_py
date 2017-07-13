# import math
#
# import constants
# from lib.connectwise_py.connectwise.ticket import Ticket
# from lib.connectwise_py.connectwise.time_entry import TimeEntry
# from .system_report import SystemReport
from decimal import Decimal

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

    @classmethod
    def fetch_by_project_id(cls, project_id, ticket_ids=[], company_id=None, updated_on_or_after=None):
        conditions = [
            'chargeToId={}'.format(project_id),
            'chargeToType="Project"'
        ]
        products = [cls(**product) for product in Connectwise.submit_request('procurement/products', conditions)]
        ticket_products = [p for p in products if p.chargeToType == 'Ticket']
        ticket_product_ids = [p.id for p in ticket_products]
        ticket_products.extend([p for p in products if p.chargeToType == 'Project' and p.id not in ticket_product_ids])
        # if ticket_ids:
        #     ticket_products = cls.fetch_by_ticket_ids(ticket_ids, company_id, updated_on_or_after)
        # return [p for p in products if p.chargeToType == 'Project' or p.chargeToType == 'Ticket']
        return ticket_products

    @classmethod
    def fetch_by_ticket_ids(cls, ticket_ids, company_id=None, updated_on_or_after=None):
        conditions = ['chargeToType="Ticket"']
        if company_id:
            conditions.append('company/id={}'.format(company_id))
        if updated_on_or_after:
            conditions.append('lastUpdated>=[{}]'.format(updated_on_or_after))
        products = [cls(**product) for product in Connectwise.submit_request('procurement/products', conditions)]
        return [p for p in products if p.chargeToId in ticket_ids]

    def billable_amount(self):
        if self.billableOption == 'Billable':
            return Decimal(round(self.quantity * self.price, 2))
        return Decimal(0)

    def total_cost(self):
        return Decimal(round(self.quantity * self.cost, 2))


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
