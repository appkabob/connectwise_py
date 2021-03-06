from .connectwise import Connectwise


class Activity:
    def __init__(self, id, **kwargs):
        self.id = id
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    def __repr__(self):
        return "<Activity {}>".format(self.id)

    @classmethod
    def fetch_all(cls):
        return [cls(**activity) for activity in Connectwise.submit_request('sales/activities')]

    @classmethod
    def fetch_by_company_id(cls, company_id):
        conditions = 'company/id={}'.format(company_id)
        return [cls(**activity) for activity in Connectwise.submit_request('sales/activities', conditions)]

    @classmethod
    def fetch_by_id(cls, _id):
        conditions = 'id={}'.format(_id)
        return [cls(**activity) for activity in Connectwise.submit_request('sales/activities', conditions)][0]

    @classmethod
    def fetch_by_date_range(cls, on_or_after=None, before=None):
        conditions = []
        if on_or_after: conditions.append('dateStart>=[{}]'.format(on_or_after))
        if before: conditions.append('dateStart<[{}]'.format(before))
        return [cls(**activity) for activity in Connectwise.submit_request('sales/activities', conditions)]
