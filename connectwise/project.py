import math

from decimal import Decimal

import constants
from .ticket import Ticket
from .system_report import SystemReport
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

    @classmethod
    def fetch_by_id(cls, _id):
        conditions = 'id={}'.format(_id)
        return [cls(**project) for project in Connectwise.submit_request('project/projects', conditions)][0]

    @classmethod
    def fetch_by_id_range(cls, low_id=None, high_id=None):
        conditions = []
        if low_id: conditions.append('id>={}'.format(low_id))
        if high_id: conditions.append('id<={}'.format(high_id))
        return [cls(**project) for project in Connectwise.submit_request('project/projects', conditions)]

    @classmethod
    def fetch_by_date_entered(cls, on_or_after=None, before=None):
        project_ids = [p['PM_Project_RecID'] for p in
                       SystemReport.fetch_project_headers_by_date_entered(on_or_after, before)]
        if project_ids:
            return cls.fetch_by_id_range(min(project_ids), max(project_ids))

    def budget_days(self):
        if not hasattr(self, 'budgetHours') or self.budgetHours == 0 or not self.budgetHours:
            return 0
        return round(self.budgetHours / 8, 2)

    def onsite_visits(self, tickets=[]):
        if not tickets:
            tickets = Ticket.fetch_by_project_id(self.id)
        return round(sum([math.ceil(ticket.budgetHours / 8) if ticket.budgetHours else 0 for ticket in tickets if ticket.serviceLocation['id'] == 1]), 2)

    def business_unit_name(self):
        business_unit_names = list(constants.BUSINESS_UNITS.keys())
        business_unit_values = list(constants.BUSINESS_UNITS.values())
        business_unit_index = business_unit_values.index(self.businessUnitId)
        return business_unit_names[business_unit_index]

    def estimated_revenue(self):
        return Decimal(self.estimatedTimeRevenue + self.estimatedExpenseRevenue + self.estimatedProductRevenue)

    def estimated_cost(self):
        return Decimal(self.estimatedTimeCost + self.estimatedExpenseCost + self.estimatedProductCost)

    def estimated_days(self, tickets=[]):
        if tickets:
            return Decimal(sum([t.budget_days() for t in tickets]))
        return Decimal(round(self.estimatedHours / 8, 2))

    def fetch_tickets(self, tickets=[]):
        if not tickets:
            self.tickets = Ticket.fetch_by_project_id(self.id)
        else:
            self.tickets = [t for t in tickets if t.project['id'] == self.id]
        return self.tickets

    # def fetch_time_entries(self, time_entries=[]):
    #     if not time_entries:
    #         self.time_entries = TimeEntry.fetch_by_charge_to_ids([self.id])
    #     else:
    #         self.time_entries = [t for t in time_entries if t.project['id'] == self.id]
    #     return self.time_entries
    #
    # def fetch_schedule_entries(self, schedule_entries=[]):
    #     if not schedule_entries:
    #         self.schedule_entries = TimeEntry.fetch_by_charge_to_ids([self.id])
    #     else:
    #         self.schedule_entries = [t for t in schedule_entries if t.project['id'] == self.id]
    #     return self.schedule_entries


class Phase:
    def __init__(self, description, **kwargs):
        self.description = description
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    def __repr__(self):
        return "<Phase {}>".format(self.description)

    @classmethod
    def fetch_by_project_id(cls, project_id):
        return [cls(**phase) for phase in Connectwise.submit_request('project/projects/{}/phases'.format(project_id))]

    def budget_days(self):
        return round(self.budgetHours / 8, 2)