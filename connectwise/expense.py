from decimal import Decimal, ROUND_DOWN
from pprint import pprint

from lib.connectwise_py.connectwise.activity import Activity
from lib.connectwise_py.connectwise.ticket import Ticket
from .connectwise import Connectwise


class ExpenseEntry:
    def __init__(self, id, chargeToId, amount, **kwargs):
        self.id = id
        self.chargeToId = chargeToId
        self.notes = None
        if not amount:
            amount = 0
        self.amount = round(Decimal(amount), 2)
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    def __repr__(self):
        return "<Expense Entry {}>".format(self.id)

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

    # def cost(self):
    #     if self.paymentMethod['id'] ==  2 and self.classification['id'] == 2:  # if it's Paid by employee and Reimbursable
    #         return self.invoiceAmount
    #     return 0

    def get_charge_to_info(self, tickets=[], activities=[], charge_codes=[], return_type='string', include_company=True, bold_first_item=False):
        if self.chargeToType == 'Activity':
            if activities:
                self.activity = [activity for activity in activities if self.chargeToId == activity.id][0]
            else:
                self.activity = Activity.fetch_by_id(self.chargeToId)
            output = []
            output.append('{}'.format(self.activity.opportunity['name']))
            output.append('Activity #{}: {}'.format(self.activity.id, self.activity['name']))

        elif self.chargeToType == 'ProjectTicket' or self.chargeToType == 'ServiceTicket':
            if tickets:
                self.ticket = [ticket for ticket in tickets if self.chargeToId == ticket.id][0]
            else:
                self.ticket = Ticket.fetch_by_id(self.chargeToId)
            output = []
            if self.ticket.project: output.append('{}'.format(self.ticket.project['name']))
            if self.ticket.phase: output.append('{}'.format(self.ticket.phase['name']))
            output.append('Ticket #{}: {}'.format(self.ticket.id, self.ticket.summary))
        else:
            output = [self.chargeToType, '{}'.format(self.chargeToId)]

        if include_company:
            output.insert(0, self.company['name'])

        if bold_first_item:
            first_item = output.pop(0)
            output.insert(0, '<strong>{}</strong>'.format(first_item))

        if return_type == 'string':
            return ' / '.join(output)
        elif return_type == 'list':
            return output

        return output

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
