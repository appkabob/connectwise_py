from decimal import Decimal

from lib.connectwise_py.connectwise.activity import Activity
from lib.connectwise_py.connectwise.member import Member
from lib.connectwise_py.connectwise.ticket import Ticket
from .connectwise import Connectwise


class TimeEntry:
    def __init__(self, chargeToId, chargeToType, **kwargs):
        self.chargeToId = chargeToId
        self.chargeToType = chargeToType
        self.estHourlyCost = 0
        self.estCost = 0
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])
        self.actualHours = Decimal(kwargs['actualHours'])

    def __repr__(self):
        return "<Time Entry {}>".format(self.chargeToId)

    @classmethod
    def fetch_by_member_identifier(cls, member_identifier, on_or_after=None, before=None):
        conditions = ['member/identifier="{}"'.format(member_identifier)]
        if on_or_after:
            conditions.append('timeStart>=[{}]'.format(on_or_after))
        if before:
            conditions.append('timeStart<[{}]'.format(before))
        return [cls(**time_entry) for time_entry in Connectwise.submit_request('time/entries', conditions)]

    @classmethod
    def fetch_vacation_by_member_identifier(cls, member_identifier):
        conditions = ['member/identifier="{}"'.format(member_identifier), 'workType/id=7']  # Vacation work type
        return [cls(**time_entry) for time_entry in Connectwise.submit_request('time/entries', conditions)]

    @classmethod
    def fetch_pd(cls):
        conditions = ['workType/id=29']  # PD work type
        return [cls(**time_entry) for time_entry in Connectwise.submit_request('time/entries', conditions)]

    @classmethod
    def fetch_pd_by_member_identifier(cls, member_identifier):
        conditions = ['member/identifier="{}"'.format(member_identifier), 'workType/id=29']  # PD work type
        return [cls(**time_entry) for time_entry in Connectwise.submit_request('time/entries', conditions)]

    @classmethod
    def fetch_by_date_range(cls, on_or_after=None, before=None, fields=None):
        conditions = []
        if on_or_after:
            conditions.append('timeStart>=[{}]'.format(on_or_after))
        if before:
            conditions.append('timeStart<[{}]'.format(before))

        return [cls(**time_entry) for time_entry in
                Connectwise.submit_request('time/entries', conditions, fields=fields)]

    @classmethod
    def fetch_by_company_id(cls, company_id, on_or_after=None, before=None):
        conditions = ['company/id={}'.format(company_id)]
        if on_or_after:
            conditions.append('timeStart>=[{}]'.format(on_or_after))
        if before:
            conditions.append('timeStart<[{}]'.format(before))

        return [cls(**time_entry) for time_entry in
                Connectwise.submit_request('time/entries', conditions)]

    @classmethod
    def fetch_by_charge_to_ids(cls, charge_to_ids, on_or_after=None, before=None):

        time_entries = []
        conditions_start = []
        if on_or_after:
            conditions_start.append('timeStart>=[{}]'.format(on_or_after))
        if before:
            conditions_start.append('timeStart<[{}]'.format(before))

        if conditions_start:
            conditions_start = ' and '.join(conditions_start) + ' and '
        else:
            conditions_start = ''

        conditions = []
        for i, charge_to_id in enumerate(charge_to_ids):
            conditions.append('chargeToId={}'.format(charge_to_id))
            if i > 0 and i % 50 == 0:  # fetch time entries for 100 tickets at a time; any more and the query becomes too long
                conditions = conditions_start + '(' + ' or '.join(conditions) + ')'
                time_entries.extend([cls(**schedule_entry) for schedule_entry in
                                     Connectwise.submit_request('time/entries', conditions)])
                conditions = []
        return time_entries

    def actual_days(self):
        return round(self.actualHours / 8, 2)

    def fetch_estimated_cost(self, members=None):

        if members:
            try:
                member = [member for member in members if member.identifier == self.member['identifier']][0]
            except IndexError:
                return 0
        else:
            try:
                member = Member.fetch_member_by_identifier(self.member['identifier'])
            except IndexError:
                return 0

        if member.identifier == 'JEngel':
            member

        self.estHourlyCost = Decimal(member.hourlyCost)

        if self.workType['name'] == 'Professional Development':
            self.estHourlyCost = round(self.estHourlyCost / 2, 2)

        self.estCost = round(self.estHourlyCost * self.actualHours, 2)
        return self.estCost

    def get_charge_to_info(self, tickets=[], activities=[], charge_codes=[], return_type='string'):
        if self.chargeToType == 'Activity':
            if activities:
                self.activity = [activity for activity in activities if self.chargeToId == activity][0]
            else:
                self.activity = Activity.fetch_by_id(self.chargeToId)
            output = [self.company['name']]
            output.append('{}'.format(self.activity.opportunity['name']))
            output.append('Activity #{}: {}'.format(self.activity.id, self.activity['name']))

        elif self.chargeToType == 'ProjectTicket' or self.chargeToType == 'ServiceTicket':
            if tickets:
                self.ticket = [ticket for ticket in tickets if self.chargeToId == ticket.id][0]
            else:
                self.ticket = Ticket.fetch_by_id(self.chargeToId)
            output = [self.company['name']]
            if self.ticket.project: output.append(self.ticket.project['name'])
            if self.ticket.phase: output.append(self.ticket.phase['name'])
            output.append('Ticket #{}: {}'.format(self.ticket.id, self.ticket.summary))
        else:
            output = [self.company['name'], self.chargeToType, '{}'.format(self.chargeToId)]

        if return_type == 'string':
            return ' / '.join(output)
        elif return_type == 'list':
            return output

        return output
