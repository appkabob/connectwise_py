from .connectwise import Connectwise
import constants

class Contact:
    def __init__(self, email, **kwargs):
        self.email = email
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    def __repr__(self):
        return "<Contact {}>".format(self.email)

    @classmethod
    def fetch_by_email(cls, email):
        child_conditions = 'communicationItems/value="{}"'.format(email)
        contact = Connectwise.submit_request('company/contacts', child_conditions=child_conditions)[0]
        return cls(email, **contact)

    @classmethod
    def fetch_all_internal(cls):
        conditions = 'company/id={}'.format(constants.CW_INTERNAL_COMPANY_ID)
        contacts = Connectwise.submit_request('company/contacts', conditions)
        return [
            cls(
                [item['value'] for item in contact['communicationItems'] if item['communicationType'] == "Email"][0],
                **contact
            ) for contact in contacts]

    @classmethod
    def fetch_by_company_id(cls, company_id, additional_conditions=None):
        conditions = 'company/id={}'.format(company_id)
        if additional_conditions:
            conditions += ' and {}'.format(additional_conditions)
        contacts = Connectwise.submit_request('company/contacts', conditions)
        return [
            cls(
                [item['value'] for item in contact['communicationItems'] if item['communicationType'] == "Email"][0],
                **contact
            ) for contact in contacts]