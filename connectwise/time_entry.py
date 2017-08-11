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
    def fetch_by_charge_to_id(cls, charge_to_id, charge_to_type=None):
        conditions = ['chargeToId={}'.format(charge_to_id)]
        if charge_to_type: conditions.append('chargeToType="{}"'.format(charge_to_type))
        return [cls(**time_entry) for time_entry in
                Connectwise.submit_request('time/entries', conditions)]

    @classmethod
    def fetch_by_charge_to_ids(cls, charge_to_ids, on_or_after=None, before=None):
        if len(charge_to_ids) > 10:
            raise IOError('Cannot lookup more than 10 chargeToIds at once')
        conditions = ['({})'.format(
            'chargeToId={}'.format(' or chargeToId='.join('{}'.format(_id) for _id in charge_to_ids)))]
        if on_or_after: conditions.append('timeStart>=[{}]'.format(on_or_after))
        if before: conditions.append('timeStart<[{}]'.format(before))
        return [cls(**time_entry) for time_entry in
                Connectwise.submit_request('time/entries', conditions)]

    def service_location(self, schedule_entries=[], tickets=[]):
        if Connectwise.get_custom_field_value(self, 'Where'): return Connectwise.get_custom_field_value(self, 'Where')
        schedule_entry = [s.where['name'] for s in schedule_entries
                          if s.dateStart[:10] == self.timeStart[:10]
                          and s.objectId == self.chargeToId]
        if schedule_entry: return schedule_entry[0]

        ticket = [t.serviceLocation['name'] for t in tickets if t.id == self.chargeToId]
        if ticket: return ticket[0]

        return 'On-Site'

    def actual_days(self):
        return round(self.actualHours / 8, 2)

    def daily_rate(self):
        return Decimal(self.hourlyRate * 8)

    def billable_amount(self):
        if self.billableOption != 'Billable':
            return Decimal(0)
        return Decimal(self.hoursBilled * self.hourlyRate)

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

        self.estHourlyCost = Decimal(member.hourly_cost(self.timeStart[:10]))

        self.override_specific_member_hourly_cost(member)

        if self.workType['name'] == 'Professional Development':
            self.estHourlyCost = round(self.estHourlyCost / 2, 2)

        self.estCost = round(self.estHourlyCost * self.actualHours, 2)
        return self.estCost

    def override_specific_member_hourly_cost(self, member):
        # override this method in a child class in your own project if you need to override self.estHourlyCost
        # for certain Members under specific custom business logic, such as whether or not the Time Entry is
        # Billable and/or occurred during a specific time period
        pass

    def get_charge_to_info(self, tickets=[], activities=[], charge_codes=[], return_type='string'):
        if self.chargeToType == 'Activity':
            if activities:
                self.activity = [activity for activity in activities if self.chargeToId == activity.id]
                if self.activity:
                    self.activity = self.activity[0]
                else:
                    self.activity = Activity.fetch_by_id(self.chargeToId)
                # if not self.activity:
                #     self.activity = Activity.fetch_by_id(self.chargeToId)
            else:
                # print('about to get activity')
                self.activity = Activity.fetch_by_id(self.chargeToId)
                # print('just got activity')
            # print('activity', self.activity)
            output = [self.company['name']]
            if hasattr(self.activity, 'opportunity'): output.append('{}'.format(self.activity.opportunity['name']))
            output.append('Activity #{}: {}'.format(self.activity.id, self.activity.name))

        elif self.chargeToType == 'ProjectTicket' or self.chargeToType == 'ServiceTicket':
            if tickets:
                # print('about to check haystack for ticket')
                self.ticket = [ticket for ticket in tickets if self.chargeToId == ticket.id]
                if self.ticket:
                    self.ticket = self.ticket[0]
                    # print('just found ticket in the haystack')
                else:
                    # print('couldnt find ticket in haystack, so getting it separately')
                    self.ticket = Ticket.fetch_by_id(self.chargeToId)
            else:
                # print('about to get ticket')
                self.ticket = Ticket.fetch_by_id(self.chargeToId)
                # print('just got ticket')
            # print('ticket', self.ticket)
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
