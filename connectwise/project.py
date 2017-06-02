from .connectwise import Connectwise


class Project:
    def __init__(self, name, **kwargs):
        self.name = name
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    def __repr__(self):
        return "<Project {}>".format(self.name)

    @classmethod
    def fetch_all(cls):
        return [cls(**project) for project in Connectwise.submit_request('project/projects')]

    @classmethod
    def fetch_by_company_id(cls, company_id):
        conditions = 'company/id={}'.format(company_id)
        return [cls(**project) for project in Connectwise.submit_request('project/projects', conditions)]