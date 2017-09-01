from decimal import Decimal

from lib.connectwise_py.connectwise.connectwise import Connectwise


class Invoice:
    def __init__(self, **kwargs):
        self.applyToType = None
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])
        self.total = round(Decimal(kwargs['total']), 2)

    def __repr__(self):
        return "<Invoice {}>".format(self.invoiceNumber)

    @classmethod
    def fetch_by_invoice_number(cls, invoice_number):
        conditions = ['invoiceNumber="{}"'.format(invoice_number)]
        return [cls(**invoice) for invoice in
                Connectwise.submit_request('finance/invoices', conditions)][0]

    @classmethod
    def fetch_by_date_range(cls, on_or_after=None, before=None):
        conditions = []
        if on_or_after:
            conditions.append('date>=[{}]'.format(on_or_after))
        if before:
            conditions.append('date<[{}]'.format(before))

        return [cls(**invoice) for invoice in
                Connectwise.submit_request('finance/invoices', conditions)]

    @classmethod
    def fetch_by_company(cls, company_id, on_or_after=None, before=None):
        conditions = ['company/id={}'.format(company_id)]
        if on_or_after:
            conditions.append('date>=[{}]'.format(on_or_after))
        if before:
            conditions.append('date<[{}]'.format(before))

        return [cls(**invoice) for invoice in
                Connectwise.submit_request('finance/invoices', conditions)]

    @classmethod
    def fetch_by_project_id(cls, project_id):
        conditions = ['applyToId={}'.format(project_id), 'applyToType="Project"']
        return [cls(**invoice) for invoice in
                Connectwise.submit_request('finance/invoices', conditions)]
