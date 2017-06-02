from datetime import datetime, timedelta

from lib.connectwise_py.connectwise.contact import Contact
from lib.connectwise_py.connectwise.schedule import ScheduleEntry
from lib.connectwise_py.connectwise.time_entry import TimeEntry
from .connectwise import Connectwise


class Company:
    def __init__(self, identifier, **kwargs):
        self.identifier = identifier
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    def __repr__(self):
        return "<Company {}>".format(self.identifier)

    @classmethod
    def fetch_all(cls):
        return [cls(**company) for company in Connectwise.submit_request('company/companies')]

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
        print(schedule_and_time)
        return schedule_and_time
