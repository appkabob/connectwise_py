import datetime
from decimal import Decimal

from .connectwise import Connectwise


class Ticket:
    def __init__(self, id, summary, **kwargs):
        self.id = id
        self.summary = summary
        self.schedule_entries = []
        self.time_entries = []
        self.expense_entries = []
        self.notes = []
        self.project = None
        self.phase = None
        self.budgetHours = 0
        self.estimatedStartDate = None
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    def __repr__(self):
        return "<Ticket {}>".format(self.id)

    def to_dict(self, include_self=False, schedule_entries=[], time_entries=[], expense_entries=[]):
        if schedule_entries:
            schedule_entries = [s for s in schedule_entries if s.objectId == self.id]
        if time_entries:
            time_entries = [t for t in time_entries if t.chargeToId == self.id and 'Ticket' in t.chargeToType]
        if expense_entries:
            expense_entries = [e for e in expense_entries if e.chargeToId == self.id and 'Ticket' in e.chargeToType]
        if schedule_entries:
            future_schedule = [s for s in schedule_entries if s.dateStart and s.dateStart >= datetime.datetime.now().strftime('%Y-%m-%d')]
        ticket_dict = {}
        ticket_dict['budget_days'] = self.budget_days()
        if schedule_entries: ticket_dict['schedule_days'] = sum([s.days() for s in schedule_entries])
        if schedule_entries: ticket_dict['future_schedule_days'] = sum([s.days() for s in future_schedule])
        if time_entries: ticket_dict['actual_days'] = self.actual_days(time_entries)
        if include_self: ticket_dict['self'] = self
        return {**vars(self), **ticket_dict}

    @classmethod
    def fetch_by_id(cls, id):
        conditions = 'id={}'.format(id)
        ticket = Connectwise.submit_request('service/tickets', conditions)
        if len(ticket) > 0:
            ticket = ticket[0]
            return cls(**ticket)
        return None

    @classmethod
    def fetch_by_ids(cls, ids):
        conditions = 'id={}'.format(' or id='.join('{}'.format(_id) for _id in ids))
        return [cls(**ticket) for ticket in Connectwise.submit_request('service/tickets/search', conditions, verb='POST')]

    @classmethod
    def fetch_by_project_id(cls, project_id):
        conditions = 'project/id={}'.format(project_id)
        return [cls(**ticket) for ticket in Connectwise.submit_request('service/tickets', conditions)]

    @classmethod
    def fetch_by_type_id(cls, type_id):
        conditions = 'type/id={}'.format(type_id)
        return [cls(**ticket) for ticket in Connectwise.submit_request('service/tickets', conditions)]

    @classmethod
    def fetch_by_type_name(cls, type_name):
        conditions = 'type/name="{}"'.format(type_name)
        return [cls(**ticket) for ticket in Connectwise.submit_request('service/tickets', conditions)]

    @classmethod
    def fetch_pd_tickets(cls):
        conditions = 'type/name="{}"'.format('Professional Development')
        return [cls(**ticket) for ticket in Connectwise.submit_request('service/tickets', conditions)]

    @classmethod
    def fetch_pd_tickets_by_member_identifier(cls, member_identifier):
        conditions = 'type/name="{}" and member/identifier="{}"'.format('Professional Development', member_identifier)
        return [cls(**ticket) for ticket in Connectwise.submit_request('service/tickets', conditions)]

    @classmethod
    def fetch_by_board_names(cls, board_names=[], on_or_after=None, before=None):
        conditions = ['board/name="' + '" or board/name="'.join(board_names) + '"']
        if on_or_after: conditions.append('estimatedStartDate>=[{}]'.format(on_or_after))
        if before: conditions.append('estimatedStartDate<[{}]'.format(before))
        return [cls(**ticket) for ticket in Connectwise.submit_request('service/tickets', conditions)]

    @classmethod
    def fetch_by_business_unit_id(cls, business_unit_id):
        conditions = 'businessUnitId={}'.format(business_unit_id)
        return [cls(**ticket) for ticket in Connectwise.submit_request('service/tickets', conditions)]

    @classmethod
    def fetch_by_member_identifier(cls, member_identifier):
        conditions = 'resources contains "{}"'.format(member_identifier)
        return [cls(**ticket) for ticket in Connectwise.submit_request('service/tickets', conditions)]

    @classmethod
    def fetch_by_last_updated(cls, on_or_after):
        conditions = 'lastUpdated>=[{}]'.format(on_or_after)
        return [cls(**ticket) for ticket in Connectwise.submit_request('service/tickets', conditions)]

    @classmethod
    def fetch_by_company_id(cls, company_id):
        conditions = 'company/id={}'.format(company_id)
        return [cls(**ticket) for ticket in Connectwise.submit_request('service/tickets', conditions)]

    @classmethod
    def fetch_all(cls):
        return [cls(**ticket) for ticket in Connectwise.submit_request('service/tickets')]

    @classmethod
    def fetch_by_record_type(cls, record_type):
        conditions = 'recordType="{}"'.format(record_type)
        return [cls(**ticket) for ticket in Connectwise.submit_request('service/tickets', conditions)]

    def fetch_notes(self, include_internal_analysis=False, include_detail_description=True):
        return [note for note in Connectwise.submit_request('service/tickets/{}/notes'.format(self.id))
                if note['internalAnalysisFlag'] == include_internal_analysis
                and note['detailDescriptionFlag'] == include_detail_description]

    def expense_cost(self):
        return '${}'.format(sum([expense.amount for expense in self.expense_entries]))

    def fetch_expense_entries(self, expense_entries=[]):
        if expense_entries:
            self.expense_entries = [e for e in expense_entries if e.chargeToId == self.id and 'Ticket' in e.chargeToType]
        else:
            from .expense import ExpenseEntry
            self.expense_entries = ExpenseEntry.fetch_by_charge_to_id(self.id)
        return self.expense_entries

    def fetch_time_entries(self, time_entries=[]):
        if time_entries:
            self.time_entries = [t for t in time_entries if t.chargeToId == self.id and 'Ticket' in t.chargeToType]
        else:
            from .time_entry import TimeEntry
            self.time_entries = TimeEntry.fetch_by_charge_to_id(self.id)
        return self.time_entries

    def actual_hours(self, time_entries=[]):
        if time_entries:
            self.time_entries = [t for t in time_entries if t.chargeToId == self.id]
        elif not self.time_entries:
            self.fetch_time_entries()
        return sum([time_entry.actualHours for time_entry in self.time_entries])

    def actual_days(self, time_entries=[]):
        return round(self.actual_hours(time_entries) / 8, 2)

    def budget_days(self):
        hours = self.budgetHours if hasattr(self, 'budgetHours') and self.budgetHours else 0
        return Decimal(round(hours / 8, 2))

    def fetch_schedule_entries(self, on_or_after=None, before=None):
        from .schedule import ScheduleEntry
        self.schedule_entries = ScheduleEntry.fetch_by_object_id(self.id, on_or_after, before)
        return self.schedule_entries

    def schedule_hours(self, schedule_entries=[]):
        if schedule_entries:
            self.schedule_entries = [s for s in schedule_entries if s.objectId == self.id]
        elif not self.schedule_entries:
            self.fetch_schedule_entries()
        return sum([schedule_entry.hours for schedule_entry in self.schedule_entries])

    def schedule_days(self, schedule_entries=[], on_or_after=None, before=None):
        if len(schedule_entries) > 0:
            schedule_entries = [s for s in schedule_entries if s.dateStart >= datetime.datetime.now().strftime('%Y-%m-%d')]
        else:
            schedule_entries = self.fetch_schedule_entries(on_or_after, before)
        return round(self.schedule_hours(schedule_entries) / 8, 2)

    def est_nbr_consultants(self):
        for field in self.customFields:
            if field['id'] == 2 and 'value' in field:
                return int(field['value']) if field['value'] else 1
        return 1
