from decimal import Decimal

from dateutil.relativedelta import relativedelta

from lib.connectwise_py.connectwise.activity import Activity
from lib.connectwise_py.connectwise.ticket import Ticket
from lib.connectwise_py.connectwise.connectwise import Connectwise
from datetime import date, timedelta, datetime


class ScheduleEntry:
    def __init__(self, id, objectId, **kwargs):
        self.id = id
        self.objectId = objectId
        self.member = {'identifier': None}
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    def __repr__(self):
        return "<Schedule Entry {}>".format(self.id)

    @classmethod
    def fetch_all(cls):
        return [cls(**schedule_entry) for schedule_entry in Connectwise.submit_request('schedule/entries')]

    @classmethod
    def fetch_by_object_ids(cls, object_ids, on_or_after=None, before=None):
        # i = 1
        # schedule_entries = []
        # print(ticket_ids)
        # while i < len(ticket_ids):
        #     print(ticket_ids[i-1:10])
        #     schedule_entries.extend(CWSchedule.fetch_by_object_ids(ticket_ids[i-1:10], on_or_after, before))
        #     i += 10
        # self.schedule_entries = schedule_entries
        if len(object_ids) > 10:
            raise IOError('Cannot lookup more than 10 chargeToIds at once')
        conditions = ['({})'.format(
            'objectId={}'.format(' or objectId='.join('{}'.format(_id) for _id in object_ids)))]
        if on_or_after: conditions.append('dateStart>=[{}]'.format(on_or_after))
        if before: conditions.append('dateStart<[{}]'.format(before))
        return [cls(**schedule_entry) for schedule_entry in
                Connectwise.submit_request('schedule/entries', conditions)]

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

    def days(self):
        return Decimal(round(self.hours / 8, 2))

    def each_calendar_date(self):
        start_date = datetime.strptime(self.dateStart[:10], '%Y-%m-%d')
        dates = []
        while start_date.strftime('%Y-%m-%d') <= self.dateEnd[:10]:
            dates.append(start_date.strftime('%Y-%m-%d'))
            start_date += relativedelta(days=1)
        return dates

    def calendar_days(self):
        return (datetime.strptime(self.dateEnd[:10], '%Y-%m-%d') - datetime.strptime(
            self.dateStart[:10], '%Y-%m-%d')).days + 1

    def duration_per_calendar_day(self):
        return self.days() / self.calendar_days()

    def get_charge_to_info(self, tickets=[], activities=[], charge_codes=[], return_type='string', include_company=True,
                           include_project_name=True, bold_first_item=False):
        """Optionally include a list of pre-fetched Tickets and/or Activities to prevent it from re-querying CW.
                return_type must be 'list' or 'string'"""
        return Connectwise.get_charge_to_info(self, tickets, activities, charge_codes, return_type, include_company,
                                              include_project_name, bold_first_item)
