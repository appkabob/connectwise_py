import constants
from lib.connectwise_py.connectwise.activity import Activity
from .ticket import Ticket
from .connectwise import Connectwise
from datetime import date, timedelta


class ScheduleEntry:
    def __init__(self, id, objectId, **kwargs):
        self.id = id
        self.objectId = objectId
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    def __repr__(self):
        return "<Schedule Entry {}>".format(self.id)

    @classmethod
    def fetch_all(cls):
        return [cls(**schedule_entry) for schedule_entry in Connectwise.submit_request('schedule/entries')]

    @classmethod
    def fetch_by_object_ids(cls, object_ids, on_or_after=None, before=None):

        schedule_entries = []
        conditions_start = []
        if on_or_after:
            conditions_start.append('dateStart>=[{}]'.format(on_or_after))
        if before:
            conditions_start.append('dateStart<[{}]'.format(before))

        if conditions_start:
            conditions_start = ' and '.join(conditions_start) + ' and '
        else:
            conditions_start = ''

        conditions = []
        for i, object_id in enumerate(object_ids):
            conditions.append('objectId={}'.format(object_id))
            if i > 0 and i % 100 == 0:  # fetch schedule entries for 100 tickets at a time; any more and the query becomes too long
                conditions = conditions_start + '(' + ' or '.join(conditions) + ')'
                print(conditions)
                schedule_entries.extend([cls(**schedule_entry) for schedule_entry in Connectwise.submit_request('schedule/entries', conditions)])
                conditions = []
        return schedule_entries

    @classmethod
    def fetch_by_object_id(cls, object_id):
        conditions = 'objectId={}'.format(object_id)
        return [cls(**schedule_entry) for schedule_entry in Connectwise.submit_request('schedule/entries', conditions)]

    @classmethod
    def fetch_by_date_range(cls, on_or_after, before):
        conditions = 'dateStart>=[{}] and dateStart<[{}]'.format(on_or_after, before)
        return [cls(**schedule_entry) for schedule_entry in Connectwise.submit_request('schedule/entries', conditions)]

    @classmethod
    def fetch_this_fy(cls, member_identifier=None):
        on_or_after, before = Connectwise.current_fy()
        conditions = 'dateStart>=[{}] and dateStart<[{}]'.format(on_or_after, before)
        if member_identifier: conditions += ' and member/identifier="{}"'.format(member_identifier)
        return [cls(**schedule_entry) for schedule_entry in Connectwise.submit_request('schedule/entries', conditions)]

    @classmethod
    def fetch_remaining_fy(cls):
        on_or_after, before = Connectwise.current_fy()
        on_or_after = date.today().strftime('%Y-%m-%d')
        conditions = 'dateStart>=[{}] and dateStart<[{}]'.format(on_or_after, before)
        return [cls(**schedule_entry) for schedule_entry in Connectwise.submit_request('schedule/entries', conditions)]

    @classmethod
    def fetch_upcoming(cls, days=30):
        on_or_after = date.today().strftime('%Y-%m-%d')
        before = date.today() + timedelta(days=days)
        conditions = 'dateStart>=[{}] and dateStart<[{}]'.format(on_or_after, before)
        return [cls(**schedule_entry) for schedule_entry in Connectwise.submit_request('schedule/entries', conditions)]

    @classmethod
    def fetch_upcoming_by_board_names(cls, board_names=[], days=30):
        schedule_entries = cls.fetch_upcoming(days)
        ticket_ids = set([schedule_entry.objectId for schedule_entry in schedule_entries])
        tickets = Ticket.fetch_by_ids(ticket_ids)
        board_ticket_ids = [ticket.id for ticket in tickets if ticket.board['name'] in board_names]
        return [schedule_entry for schedule_entry in schedule_entries if schedule_entry.objectId in board_ticket_ids]

    @classmethod
    def fetch_upcoming_by_project_ids(cls, project_ids=[], days=30):
        schedule_entries = cls.fetch_upcoming(days)
        ticket_ids = set([schedule_entry.objectId for schedule_entry in schedule_entries])
        tickets = Ticket.fetch_by_ids(ticket_ids)
        project_ticket_ids = [ticket.id for ticket in tickets if ticket.project and ticket.project['id'] in project_ids]
        return [schedule_entry for schedule_entry in schedule_entries if schedule_entry.objectId in project_ticket_ids]

    @classmethod
    def fetch_by_company_id(cls, company_id, on_or_after=None, before=None):
        conditions = []
        if on_or_after:
            conditions.append('dateStart>=[{}]'.format(on_or_after))
        if before:
            conditions.append('dateStart<[{}]'.format(before))
        conditions = ' and '.join(conditions)
        company_tickets = Ticket.fetch_by_company_id(company_id)
        company_activities = Activity.fetch_by_company_id(company_id)
        return [cls(**schedule_entry) for schedule_entry in Connectwise.submit_request('schedule/entries', conditions)
                if schedule_entry['objectId'] == company_id or
                schedule_entry['objectId'] in [ticket.id for ticket in company_tickets] or
                schedule_entry['objectId'] in [activity.id for activity in company_activities]
                ]
