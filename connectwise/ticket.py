from decimal import Decimal

from .connectwise import Connectwise
# from lib.connectwise_py.connectwise.schedule import ScheduleEntry
# from lib.connectwise_py.connectwise.time_entry import TimeEntry


class Ticket:
    def __init__(self, id, summary, **kwargs):
        self.id = id
        self.summary = summary
        self.schedule_entries = []
        self.time_entries = []
        self.expense_entries = []
        self.notes = []
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    def __repr__(self):
        return "<Ticket {}>".format(self.id)

    @classmethod
    def fetch_by_id(cls, id):
        conditions = 'id={}'.format(id)
        ticket = Connectwise.submit_request('service/tickets', conditions)[0]
        return cls(**ticket)

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
    def fetch_by_board_names(cls, board_names=[]):
        conditions = 'board/name="' + '" or board/name="'.join(board_names) + '"'
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

    def fetch_notes(self, include_internal_analysis=False, include_detail_description=True):
        return [note for note in Connectwise.submit_request('service/tickets/{}/notes'.format(self.id))
                if note['internalAnalysisFlag'] == include_internal_analysis
                and note['detailDescriptionFlag'] == include_detail_description]

    def expense_cost(self):
        return '${}'.format(sum([expense.amount for expense in self.expense_entries]))

    def actual_hours(self, time_entries=[]):
        # if not time_entries:
        #     self.time_entries = TimeEntry.fetch_by_charge_to_ids([self.id])
        # else:
        self.time_entries = [t for t in time_entries if t.chargeToId == self.id]
        return sum([time_entry.actualHours for time_entry in self.time_entries])

    def budget_days(self):
        hours = self.budgetHours if hasattr(self, 'budgetHours') and self.budgetHours else 0
        return Decimal(round(hours / 8, 2))

    def actual_days(self):
        return round(self.actual_hours() / 8, 2)

    def schedule_hours(self, schedule_entries=[]):
        # if not schedule_entries:
        #     self.schedule_entries = ScheduleEntry.fetch_by_object_id(self.id)
        # else:
        self.schedule_entries = [s for s in schedule_entries if s.objectId == self.id]
        return sum([schedule_entry.hours for schedule_entry in self.schedule_entries])

    def schedule_days(self):
        return round(self.schedule_hours() / 8, 2)

    def est_nbr_consultants(self):
        for field in self.customFields:
            if field['id'] == 2 and 'value' in field:
                return int(field['value']) if field['value'] else 1
        return 1
