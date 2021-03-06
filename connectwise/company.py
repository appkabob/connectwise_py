from datetime import datetime, timedelta

from lib.connectwise_py.connectwise.contact import Contact
from lib.connectwise_py.connectwise.schedule import ScheduleEntry
from lib.connectwise_py.connectwise.time_entry import TimeEntry
from lib.connectwise_py.connectwise.invoice import Invoice
from .connectwise import Connectwise


class Company:
    def __init__(self, identifier, **kwargs):
        self.addressLine1 = None
        self.city = None
        self.state = None
        self.zip = None
        self.identifier = identifier
        self.invoices = []
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    def __repr__(self):
        return "<Company {}>".format(self.identifier)

    def to_dict(self, include_self=False):
        company_dict = {}
        company_dict['phone_formatted'] = self.phone_formatted()
        if include_self: company_dict['self'] = self
        return {**vars(self), **company_dict}

    @classmethod
    def fetch_all(cls, fields=None):
        return [cls(**company) for company in Connectwise.submit_request('company/companies', fields=fields)]

    @classmethod
    def fetch_by_state(cls, state):
        conditions = 'state="{}"'.format(state)
        return [cls(**company) for company in Connectwise.submit_request('company/companies', conditions)]

    @classmethod
    def fetch_all_active(cls):
        conditions = 'status/id=1'
        return [cls(**company) for company in Connectwise.submit_request('company/companies', conditions)]

    @classmethod
    def fetch_by_id(cls, _id):
        conditions = 'id={}'.format(_id)
        return [cls(**company) for company in Connectwise.submit_request('company/companies', conditions)][0]

    def fetch_active_contacts(self):
        conditions = 'inactiveFlag=false'
        return Contact.fetch_by_company_id(self.id, conditions)

    def fetch_schedule_entries(self, on_or_after=None, before=None):
        return ScheduleEntry.fetch_by_company_id(self.id, on_or_after, before)

    def fetch_time_entries(self, on_or_after=None, before=None):
        return TimeEntry.fetch_by_company_id(self.id, on_or_after, before)

    def phone_formatted(self):
        if len(self.phoneNumber) == 10:
            return '({}) {}-{}'.format(self.phoneNumber[:3], self.phoneNumber[3:6], self.phoneNumber[6:10])
        return self.phoneNumber

    def fetch_time_this_quarter(self, time_entries=None):
        first_day_of_quarter = '2017-04-01T00:00:00Z'
        if not time_entries:
            return TimeEntry.fetch_by_company_id(self.id, first_day_of_quarter)
        else:
            # for time_entry in time_entries:
            #     print(time_entry.company['id'])
            #     print(self.id)
            #     print(time_entry.timeStart)
            #     print(first_day_of_quarter)
            return [time_entry for time_entry in time_entries
                            if time_entry.company['id'] == self.id]

    def fetch_recent_schedule_and_time(self, days=None, by=None):
        on_or_after = None
        if days:
            on_or_after = datetime.today() - timedelta(days=days)
            on_or_after = on_or_after.strftime('%Y-%m-%d')
        before = datetime.today().strftime('%Y-%m-%d')

        schedule_entries = self.fetch_schedule_entries(on_or_after, before)
        time_entries = self.fetch_time_entries(on_or_after, before)

        oldest_schedule_date = datetime.strptime(sorted(schedule_entries, key=lambda x: x.dateStart)[0].dateStart[:10], '%Y-%m-%d')
        oldest_time_date = datetime.strptime(sorted(time_entries, key=lambda x: x.timeStart)[0].timeStart[:10], '%Y-%m-%d')
        oldest_date = oldest_schedule_date if oldest_schedule_date < oldest_time_date else oldest_time_date

        schedule_and_time = []
        while oldest_date < datetime.today():
            this_days_schedule_entries = [schedule_entry for schedule_entry in schedule_entries if datetime.strptime(schedule_entry.dateStart[:10], '%Y-%m-%d') == oldest_date]
            this_days_time_entries = [time_entry for time_entry in time_entries if datetime.strptime(time_entry.timeStart[:10], '%Y-%m-%d') == oldest_date]

            # print(oldest_date)
            # print(this_days_schedule_entries)
            # print(this_days_time_entries)
            # print('--')
            this_days_members = []
            if by == 'member':
                if this_days_time_entries:
                    this_days_members.extend([time_entry.member['identifier'] for time_entry in this_days_time_entries])
                if this_days_schedule_entries:
                    this_days_members.extend([schedule_entry.member['identifier'] for schedule_entry in this_days_schedule_entries])
                this_days_members = set(this_days_members)

                member_schedule_and_time = []
                if this_days_members:
                    for member_identifier in this_days_members:
                        member_schedule_and_time.append({
                            'member_identifier': member_identifier,
                            'schedule_entries': [schedule_entry for schedule_entry in this_days_schedule_entries if
                                                 schedule_entry.member['identifier'] == member_identifier],
                            'time_entries': [time_entry for time_entry in this_days_time_entries if
                                                 time_entry.member['identifier'] == member_identifier]
                        })

                    schedule_and_time.append({
                        'date': oldest_date,
                        'members': member_schedule_and_time
                    })
            else:
                if this_days_schedule_entries or this_days_time_entries:
                    schedule_and_time.append({
                        'date': oldest_date,
                        'schedule_entries': this_days_schedule_entries,
                        'time_entries': this_days_time_entries
                    })
            oldest_date += timedelta(days=1)
        # print(schedule_and_time)
        return schedule_and_time

    def fetch_invoices(self, invoices=None, on_or_after=None, before=None):
        if invoices:
            self.invoices = [i for i in invoices if i.company['id'] == self.id and on_or_after <= i.date[:10] < before]
        else:
            self.invoices = Invoice.fetch_by_company(self.id, on_or_after, before)
        return self.invoices

    def fetch_invoiced_amount(self, invoices=None, on_or_after=None, before=None):
        invoices = self.fetch_invoices(invoices, on_or_after, before)
        return sum([i.total for i in invoices])

    def fetch_time_entries_by_date_range(self, time_entries=[], on_or_after=None, before=None):
        if time_entries:
            self.time_entries = [t for t in time_entries if t.company['id'] == self.id and on_or_after <= t.timeStart[:10] < before]
        else:
            self.time_entries = TimeEntry.fetch_by_company_id(self.id, on_or_after, before)
        return self.time_entries

    def fetch_actual_days_by_date_range(self, time_entries=[], on_or_after=None, before=None):
        time_entries = self.fetch_time_entries_by_date_range(time_entries, on_or_after, before)
        return sum([t.actual_days() for t in time_entries])
