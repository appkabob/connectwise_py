from .connectwise import Connectwise
import constants

class Contact:
    def __init__(self, **kwargs):
        # self.id = _id
        self.title = None
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    def __repr__(self):
        return "<Contact {} {}>".format(self.id, self.get_email())

    @classmethod
    def fetch_by_email(cls, email):
        child_conditions = 'communicationItems/value="{}"'.format(email)
        contact = Connectwise.submit_request('company/contacts', child_conditions=child_conditions)[0]
        return cls(**contact)

    @classmethod
    def fetch_all_internal(cls):
        conditions = 'company/id={}'.format(constants.CW_INTERNAL_COMPANY_ID)
        contacts = Connectwise.submit_request('company/contacts', conditions)
        return [cls(**contact) for contact in contacts]

    @classmethod
    def fetch_by_company_id(cls, company_id, additional_conditions=None):
        conditions = 'company/id={}'.format(company_id)
        if additional_conditions:
            conditions += ' and {}'.format(additional_conditions)
        contacts = Connectwise.submit_request('company/contacts', conditions)
        return [cls(**contact) for contact in contacts]

    def get_phone(self, i=0):
        phones = [communicationItem['value']
                for communicationItem in self.communicationItems
                if communicationItem['communicationType'] == 'Phone']
        return phones[i] if phones else None

    def get_phone_extension(self, i=0):
        extensions = [communicationItem['extension']
                for communicationItem in self.communicationItems
                if communicationItem['communicationType'] == 'Phone']
        return extensions[i] if extensions else None

    def get_phone_formatted(self, i=0):
        phone = self.get_phone(i)
        if phone and len(phone) == 10:
            return '({}) {}-{} {}'.format(phone[:3], phone[3:6], phone[6:10], self.get_phone_extension())
        return phone

    def get_email(self, i=0):
        emails = [communicationItem['value']
                for communicationItem in self.communicationItems
                if communicationItem['communicationType'] == 'Email']
        return emails[i] if emails else None
