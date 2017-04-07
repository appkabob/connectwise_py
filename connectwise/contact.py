from .connectwise import Connectwise


class Contact:
    def __init__(self, email, **kwargs):
        self.email = email
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    @classmethod
    def fetch_by_email(cls, email):
        child_conditions = 'communicationItems/value="{}"'.format(email)
        contact = Connectwise.submit_request('company/contacts', child_conditions=child_conditions)[0]
        return cls(email, **contact)
