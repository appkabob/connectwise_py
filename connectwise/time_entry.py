from datetime import datetime
from decimal import Decimal

from lib.connectwise_py.connectwise.activity import Activity
from lib.connectwise_py.connectwise.member import Member
from lib.connectwise_py.connectwise.ticket import Ticket
from .connectwise import Connectwise


class TimeEntry:
    def __init__(self, **kwargs):
        self.chargeToId = None
        self.chargeToType = None
        self.estHourlyCost = 0
        self.estCost = 0
        self.invoice = None
        self.notes = None
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])
        self.actualHours = Decimal(kwargs['actualHours'])

    def __repr__(self):
        return "<Time Entry {}>".format(self.chargeToId)

    def to_dict(self, include_self=False, schedule_entries=[], tickets=[], activities=[], members=[]):
        """
        Get a representation of the TimeEntry object as a Python Dictionary,
        including calculated values from methods.

        If you can provide a list of schedule entries, tickets, activities, or members that
        contain records potentially relating to this TimeEntry, additional fields can
        be returned.

        :param include_self: when True, include the original object under the dictionary
        key 'self' so that you have it in case you need to reference it later
        """
        dict = {}
        dict['actual_days'] = self.actual_days()
        dict['daily_rate'] = self.daily_rate()
        dict['billable_amount'] = self.billable_amount()
        if members: dict['estimated_cost'] = self.fetch_estimated_cost(members)
        if schedule_entries or tickets or activities:
            dict['service_location'] = self.service_location(schedule_entries, tickets, activities)
        if include_self: dict['self'] = self
        return {**vars(self), **dict}

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
    def fetch_by_business_unit_id(cls, business_unit_id, on_or_after=None, before=None):
        conditions = ['businessUnitId={}'.format(business_unit_id)]
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

    def service_location(self, schedule_entries=[], tickets=[], activities=[]):
        if Connectwise.get_custom_field_value(self, 'Where'): return Connectwise.get_custom_field_value(self, 'Where')
        schedule_entry = [s.where['name'] for s in schedule_entries
                          if s.dateStart[:10] == self.timeStart[:10]
                          and s.objectId == self.chargeToId]
        if schedule_entry: return schedule_entry[0]

        ticket = [t.serviceLocation['name'] for t in tickets if t.id == self.chargeToId]
        if ticket: return ticket[0]

        activity = [a.where for a in activities if a.id == self.chargeToId]
        if activity: return activity[0]

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

    def get_schedule_entry(self, schedule_entries):
        schedule = [s for s in schedule_entries if
                    s.objectId == self.chargeToId and
                    s.member['identifier'] == self.member['identifier'] and
                    s.dateStart <= self.timeStart and s.dateEnd >= self.timeEnd]
        if schedule: return schedule[0]

    def get_schedule_duration_per_day(self, schedule_entries):
        schedule_entry = self.get_schedule_entry(schedule_entries)
        if schedule_entry:
            return schedule_entry.days() / schedule_entry.calendar_days()
        return 0

    def get_charge_to_info(self, tickets=[], activities=[], charge_codes=[], return_type='string', include_company=True,
                           include_project_name=True, include_phase=True, bold_first_item=False):
        """Optionally include a list of pre-fetched Tickets and/or Activities to prevent it from re-querying CW.
        return_type must be 'list' or 'string'"""
        return Connectwise.get_charge_to_info(self, tickets, activities, charge_codes, return_type, include_company,
                                              include_project_name, include_phase, bold_first_item)
