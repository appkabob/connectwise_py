from decimal import Decimal

from lib.connectwise_py.connectwise.activity import Activity
from lib.connectwise_py.connectwise.ticket import Ticket
from .connectwise import Connectwise


class ExpenseEntry:
    def __init__(self, id, chargeToId, amount, **kwargs):
        self.id = id
        self.chargeToId = chargeToId
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
    def fetch_by_member_identifier(cls, member_identifier, on_or_after=None, before=None):
        conditions = ['member/identifier="{}"'.format(member_identifier)]
        if on_or_after:
            conditions.append('date>=[{}]'.format(on_or_after))
        if before:
            conditions.append('date<[{}]'.format(before))

        return [cls(**expense_entry) for expense_entry in
                Connectwise.submit_request('expense/entries', conditions)]

    def get_ticket(self, tickets=[]):
        if self.chargeToType == 'Activity':
            return Activity.fetch_by_id(self.chargeToId)
        elif self.chargeToType == 'ProjectTicket' or self.chargeToType == 'ServiceTicket':
            if tickets:
                return [ticket for ticket in tickets if self.chargeToId == ticket.id][0]
            return Ticket.fetch_by_id(self.chargeToId)
        return '{} {}'.format(self.chargeToType, self.chargeToId)

    def get_charge_to_info(self, tickets=[], activities=[], charge_codes=[]):
        if self.chargeToType == 'Activity':
            if activities:
                self.activity = [activity for activity in activities if self.chargeToId == activity][0]
            else:
                self.activity = Activity.fetch_by_id(self.chargeToId)
            output = self.company['name']
            output += ' / {}'.format(self.activity.opportunity['name'])
            output += ' / Activity #{}: {}'.format(self.activity.id, self.activity['name'])

        elif self.chargeToType == 'ProjectTicket' or self.chargeToType == 'ServiceTicket':
            if tickets:
                self.ticket = [ticket for ticket in tickets if self.chargeToId == ticket.id][0]
            else:
                self.ticket = Ticket.fetch_by_id(self.chargeToId)
            output = self.company['name']
            output += ' / {}'.format(self.ticket.project['name']) if self.ticket.project else ''
            output += ' / {}'.format(self.ticket.phase['name']) if self.ticket.phase else ''
            output += ' / Ticket #{}: {}'.format(self.ticket.id, self.ticket.summary)
        else:
            output = '{} {}'.format(self.chargeToType, self.chargeToId)

        return output


