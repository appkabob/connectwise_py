from .connectwise import Connectwise


class Member:
    def __init__(self, identifier, officeEmail, **kwargs):
        self.officeEmail = officeEmail
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

