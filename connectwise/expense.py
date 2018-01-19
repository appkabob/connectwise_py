from decimal import Decimal, ROUND_DOWN
from pprint import pprint

from lib.connectwise_py.connectwise.activity import Activity
from lib.connectwise_py.connectwise.ticket import Ticket
from .connectwise import Connectwise


class ExpenseEntry:
    def __init__(self, **kwargs):
        self.chargeToId = None
        self.chargeToType = None
        self.notes = None
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])
        self.amount = Decimal(kwargs['amount']) if hasattr(kwargs, 'amount') else Decimal(0)

    def __repr__(self):
        return "<Expense Entry {}>".format(self.id)

    def to_dict(self, include_self=False, expense_types=[]):
        expense_dict = {}
        expense_dict['billable_amount'] = self.billable_amount()
        if expense_types: expense_dict['reimbursable_amount'] = self.reimbursable_amount(expense_types)
        if include_self: expense_dict['self'] = self
        return {**vars(self), **expense_dict}

    @classmethod
    def fetch_by_charge_to_ids(cls, charge_to_ids, on_or_after=None, before=None):

        expense_entries = []
        conditions_start = []
        if on_or_after:
            conditions_start.append('date>=[{}]'.format(on_or_after))
        if before:
            conditions_start.append('date<[{}]'.format(before))

        if conditions_start:
            conditions_start = ' and '.join(conditions_start) + ' and '
        else:
            conditions_start = ''

        conditions = []
        for i, charge_to_id in enumerate(charge_to_ids):
            conditions.append('chargeToId={}'.format(charge_to_id))
            if i > 0 and i % 50 == 0:  # fetch time entries for 100 tickets at a time; any more and the query becomes too long
                conditions = conditions_start + '(' + ' or '.join(conditions) + ')'
                expense_entries.extend([cls(**expense_entry) for expense_entry in
                                     Connectwise.submit_request('expense/entries', conditions)])
                conditions = []
        return expense_entries

    @classmethod
    def fetch_by_charge_to_id(cls, _id):
        conditions = 'chargeToId={}'.format(_id)
        return [cls(**expense_entry) for expense_entry in Connectwise.submit_request('expense/entries', conditions)]

    @classmethod
    def fetch_by_date_range(cls, on_or_after=None, before=None):
        conditions = []
        if on_or_after:
            conditions.append('date>=[{}]'.format(on_or_after))
        if before:
            conditions.append('date<[{}]'.format(before))

        return [cls(**expense_entry) for expense_entry in
                                     Connectwise.submit_request('expense/entries', conditions)]

    @classmethod
    def fetch_by_business_unit_id(cls, business_unit_id, on_or_after=None, before=None):
        conditions = ['businessUnitId={}'.format(business_unit_id)]
        if on_or_after:
            conditions.append('date>=[{}]'.format(on_or_after))
        if before:
            conditions.append('date<[{}]'.format(before))

        return [cls(**expense_entry) for expense_entry in
                Connectwise.submit_request('expense/entries', conditions)]

    @classmethod
    def fetch_by_member_identifier(cls, member_identifier, on_or_after=None, before=None):
        conditions = ['member/identifier="{}"'.format(member_identifier)]
        if on_or_after:
            conditions.append('date>=[{}]'.format(on_or_after))
        if before:
            conditions.append('date<[{}]'.format(before))

        return [cls(**expense_entry) for expense_entry in
                Connectwise.submit_request('expense/entries', conditions)]

    @classmethod
    def fetch_by_company_id(cls, company_id, on_or_after=None, before=None):
        conditions = ['company/id={}'.format(company_id)]
        if on_or_after:
            conditions.append('date>=[{}]'.format(on_or_after))
        if before:
            conditions.append('date<[{}]'.format(before))
        return [cls(**expense_entry) for expense_entry in
                Connectwise.submit_request('expense/entries', conditions)]

    def fetch_doc_count(self):
        conditions = 'recordId={}&recordType=Expense'.format(self.id)
        return Connectwise.submit_request('system/documents/count', conditions)['count']

    def get_ticket(self, tickets=[]):
        if self.chargeToType == 'Activity':
            return Activity.fetch_by_id(self.chargeToId)
        elif self.chargeToType == 'ProjectTicket' or self.chargeToType == 'ServiceTicket':
            if tickets:
                return [ticket for ticket in tickets if self.chargeToId == ticket.id][0]
            return Ticket.fetch_by_id(self.chargeToId)
        return '{} {}'.format(self.chargeToType, self.chargeToId)

    def get_charge_to_info(self, tickets=[], activities=[], charge_codes=[], return_type='string', include_company=True,
                           include_project_name=True, bold_first_item=False):
        """Optionally include a list of pre-fetched Tickets and/or Activities to prevent it from re-querying CW.
                return_type must be 'list' or 'string'"""
        return Connectwise.get_charge_to_info(self, tickets, activities, charge_codes, return_type, include_company,
                                              include_project_name, bold_first_item)

    def billable_amount(self):
        if self.billableOption == 'Billable':
            return Decimal(self.invoiceAmount)
        return Decimal(0)

    def reimbursable_amount(self, expense_types=[]):
        if self.classification['id'] != 2:  # if not reimbursable
            return Decimal(0)
        if expense_types:
            expense_type = [et for et in expense_types if et.id == self.type['id']][0]
        else:
            expense_type = ExpenseType.fetch_by_id(self.type['id'])
        if expense_type.mileageFlag:
            return Decimal(self.invoiceAmount)  # .quantize(Decimal('.01'), ROUND_DOWN)
        return self.amount


class ExpenseType:
    def __init__(self, **kwargs):
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    def __repr__(self):
        return "<Expense Type {}>".format(self.name)

    @classmethod
    def fetch_all(cls):
        return [cls(**expense_type) for expense_type in Connectwise.submit_request('expense/types')]

    @classmethod
    def fetch_mileage_types(cls):
        conditions = ['mileageFlag=true']
        return [cls(**expense_type) for expense_type in Connectwise.submit_request('expense/types', conditions)]

    @classmethod
    def fetch_by_id(cls, _id):
        conditions = ['id={}'.format(_id)]
        return [cls(**expense_type) for expense_type in Connectwise.submit_request('expense/types', conditions)][0]
