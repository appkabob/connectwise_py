from lib.connectwise_py.connectwise.connectwise import Connectwise


class SystemReport:
    def __init__(self, name, **kwargs):
        self.name = name
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    def __repr__(self):
        return "<System Report {}>".format(self.name)

    @staticmethod
    def fetch(name, conditions=''):
        filters = {
            'page': 1,
            'pageSize': 1000
            # 'orderBy': 'Holiday_Date asc'
        }

        report_data = Connectwise.submit_request('system/reports/{}'.format(name), conditions, filters)

        keys = [list(col.keys())[0] for col in report_data['column_definitions']]

        objects = []
        for object_values in report_data['row_values']:
            object = {}
            for key in keys:
                object[key] = object_values[keys.index(key)]
            objects.append(object)

        return objects

    @classmethod
    def fetch_project_headers_by_date_entered(cls, on_or_after=None, before=None):
        conditions = []
        if on_or_after: conditions.append('Date_Entered_UTC>=[{}]'.format(on_or_after))
        if before: conditions.append('Date_Entered_UTC<[{}]'.format(before))
        return cls.fetch('ProjectHeader', conditions)

    @classmethod
    def fetch_invoice_time_by_date_start(cls, on_or_after=None, before=None):
        conditions = []
        if on_or_after: conditions.append('Date_Start>=[{}]'.format(on_or_after))
        if before: conditions.append('Date_Start<[{}]'.format(before))
        return cls.fetch('InvoiceTime', conditions)

    @classmethod
    def fetch_timesheets_by_date_start(cls, on_or_after=None, before=None):
        conditions = []
        if on_or_after: conditions.append('Date_Start>=[{}]'.format(on_or_after))
        if before: conditions.append('Date_Start<[{}]'.format(before))
        return cls.fetch('TimeSheets', conditions)

    @classmethod
    def fetch_all_time_statuses(cls):
        return cls.fetch('TimeStatus')
