import constants
from .connectwise import Connectwise


class Agreement:
    def __init__(self, name, **kwargs):
        self.name = name
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    def __repr__(self):
        return "<Agreement {}>".format(self.name)

    @classmethod
    def fetch_vacation_agreements(cls):
        conditions = 'company/id = {} and type/name contains "vacation" and cancelledFlag = false'\
            .format(constants.CW_INTERNAL_COMPANY_ID)
        filters = {'orderBy': 'startDate desc'}
        return [Agreement(**agreement) for agreement in
                Connectwise.submit_request('finance/agreements', conditions, filters)]
