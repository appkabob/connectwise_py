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
