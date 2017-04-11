from .connectwise import Connectwise


class TimeEntry:
    def __init__(self, chargeToId, chargeToType, **kwargs):
        self.chargeToId = chargeToId
        self.chargeToType = chargeToType
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    def __repr__(self):
        return "<Time Entry {}>".format(self.chargeToId)

    @classmethod
    def fetch_by_member_identifier(cls, member_identifier):
        conditions = ['member/identifier="{}"'.format(member_identifier)]
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
