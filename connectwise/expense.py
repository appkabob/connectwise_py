from decimal import Decimal
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
                expense_entries.extend([cls(**schedule_entry) for schedule_entry in
                                     Connectwise.submit_request('expense/entries', conditions)])
                conditions = []
        return expense_entries