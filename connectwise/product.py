# import math
#
# import constants
# from lib.connectwise_py.connectwise.ticket import Ticket
# from lib.connectwise_py.connectwise.time_entry import TimeEntry
# from .system_report import SystemReport
from decimal import Decimal
from pprint import pprint

from .connectwise import Connectwise


class Product:
    def __init__(self, **kwargs):
        self.purchaseDate = None
        self.internalNotes = None
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    def __repr__(self):
        return "<Product {} {} Qty {}>".format(self.id, self.description, self.quantity)

    @classmethod
    def create(cls, catalog_item_id, charge_to_id, charge_to_type, billable_option, description=None, internal_notes=None):
        conditions = {
            'catalogItem': {
                'id': catalog_item_id
            },
            'chargeToId': charge_to_id,
            'chargeToType': charge_to_type,
            'billableOption': billable_option
        }
        if description: conditions['description'] = description
        if internal_notes: conditions['internalNotes'] = internal_notes
        product = Connectwise.submit_request('procurement/products', conditions, verb='POST')
        return cls(**product)

    def to_dict(self, include_self=False, schedule_entries=[], tickets=[], activities=[]):
        """
        Get a representation of the Product object as a Python Dictionary,
        including calculated values from methods.

        If you can provide a list of schedule entries, tickets, or activities that
        contain records potentially relating to this Product, you can get a more
        accurate Service Location for relevant Products.

        :param include_self: when True, include the original object under the dictionary
        key 'self' so that you have it in case you need to reference it later
        """
        dict = {}
        dict['billable_amount'] = self.billable_amount()
        dict['total_cost'] = self.total_cost()
        dict['service_location'] = self.service_location(schedule_entries, tickets, activities)
        if include_self: dict['self'] = self
        return {**vars(self), **dict}

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
    def fetch_by_catalog_item_identifier(cls, catalog_item_identifier, identifier_operator='=', charge_to_type=None):
        conditions = ['catalogItem/identifier {} "{}"'.format(identifier_operator, catalog_item_identifier)]
        if charge_to_type: conditions.append('chargeToType="{}"'.format(charge_to_type))
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
    def fetch_by_category_name(cls, category_name, operator='='):
        catalog_product_ids = [cp.id for cp in CatalogProduct.fetch_by_category_name(category_name, operator)]
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

    @classmethod
    def fetch_by_business_unit_id(cls, business_unit_id, on_or_after=None, before=None):
        conditions = ['businessUnitId={}'.format(business_unit_id)]
        if on_or_after:
            conditions.append('purchaseDate>=[{}]'.format(on_or_after))
        if before:
            conditions.append('purchaseDate<[{}]'.format(before))

        return [cls(**product) for product in
                Connectwise.submit_request('procurement/products', conditions)]

    def billable_amount(self):
        if self.billableOption == 'Billable':
            return Decimal(round(self.quantity * self.price, 2))
        return Decimal(0)

    def total_cost(self):
        return Decimal(round(self.quantity * self.cost, 2))

    def service_location(self, schedule_entries=[], tickets=[], activities=[]):
        schedule_entry = [s.where['name'] for s in schedule_entries
                          if s.dateStart[:10] == self.purchaseDate
                          and s.objectId == self.chargeToId]
        if schedule_entry: return schedule_entry[0]

        ticket = [t.serviceLocation['name'] for t in tickets if t.id == self.chargeToId]
        if ticket: return ticket[0]

        activity = [a.where for a in activities if a.id == self.chargeToId]
        if activity: return activity[0]

        return 'On-Site'


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

    @classmethod
    def fetch_by_category_name(cls, category_name, operator='='):
        conditions = ['category/name {} "{}"'.format(operator, category_name)]
        return [cls(**catalog_product) for catalog_product in
                Connectwise.submit_request('procurement/catalog', conditions)]
