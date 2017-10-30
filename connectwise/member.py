from datetime import datetime

import constants
from .connectwise import Connectwise


class Member:
    def __init__(self, identifier, **kwargs):
        self.officeEmail = None
        self.identifier = identifier
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    def __repr__(self):
        return "<Member {}>".format(self.identifier)

    @classmethod
    def fetch_member_by_office_email(cls, officeEmail):
        conditions = ['officeEmail="{}"'.format(officeEmail)]
        member = Connectwise.submit_request('system/members', conditions)[0]
        return cls(**member)

    @classmethod
    def fetch_member_by_identifier(cls, identifier):
        conditions = ['identifier="{}"'.format(identifier)]
        member = Connectwise.submit_request('system/members', conditions)[0]
        return cls(**member)

    @classmethod
    def fetch_all_members(cls):
        conditions = ['identifier!="APIMember"']
        filters = {'orderBy': 'lastName asc'}
        return [cls(**member) for member in Connectwise.submit_request('system/members', conditions, filters)]

    def hourly_cost(self, on_date='today'):
        if on_date.lower() == 'today' or on_date >= '2016-07-01':  # HARDCODED: NEEDS ADJUSTMENT
            return self.hourlyCost
        on_date = datetime.strptime(on_date, '%Y-%m-%d')
        if on_date.month >= 7:
            fy = '{}-{}'.format(on_date.year, on_date.year + 1)
        else:
            fy = '{}-{}'.format(on_date.year - 1, on_date.year)
        return constants.CONSULTANT_HOURLY_COSTS[self.identifier.lower()][fy]

    def daily_cost(self, on_date='today'):
        return round(self.hourly_cost(on_date) * 8, 2)
