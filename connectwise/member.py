from datetime import datetime

import constants
from lib.connectwise_py.connectwise.agreement import Agreement
from lib.connectwise_py.connectwise.contact import Contact
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
        conditions = ['identifier!="APIMember" and identifier!="screenconnect" and identifier!="quosal"']
        filters = {'orderBy': 'lastName asc'}
        return [cls(**member) for member in Connectwise.submit_request('system/members', conditions, filters)]

    @classmethod
    def fetch_by_type_name(cls, type_name):
        """
        Return members filtered by type. For example, "Salaried Employee"
        :param type_name: str: member type, e.g. "Salaried Employee"
        :return: list of Members
        """
        conditions = 'type/name="{}"'.format(type_name)
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

    def fetch_internal_contact(self):
        return Contact.fetch_by_email(self.officeEmail)

    def fetch_vacation_agreements(self, agreements=[], contacts=[]):
        contact = None
        if len(contacts) > 0:
            contact = [c for c in contacts if self.officeEmail == c.get_email()]
            if len(contact) > 0: contact = contact[0]
        else:
            contact = self.fetch_internal_contact()
        if len(agreements) == 0:
            agreements = Agreement.fetch_vacation_agreements()
        agreements = [a for a in agreements if contact and contact.id == a.contact['id']]
        # print(self.identifier, contact, agreements)
        if contact:
            return [a for a in agreements if a.contact['id'] == contact.id]
        else:
            return []
