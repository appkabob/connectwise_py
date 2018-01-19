import pandas as pd
import constants
from cec_api.models.data_util import DataUtil
from lib.connectwise_py.connectwise.connectwise import Connectwise


class SystemReport:
    def __init__(self, name, **kwargs):
        self.name = name
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    def __repr__(self):
        return "<System Report {}>".format(self.name)

    def to_dict(self):
        return vars(self)

    @staticmethod
    def fetch(name, conditions=[], filters={}):
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

    @classmethod
    def fetch_holiday_list(cls, filter_to_list=False):
        """
        Fetch holiday records from the Holiday Setup Table
        :param filter_to_list: Leave as default of False to return all holiday records.
        Otherwise, you can limit to a specific list as defined in the Holiday setup table,
        for example "Standard Holidays".
        :return: dict of holiday dates, one record per calendar day
        """
        conditions = []
        if filter_to_list: conditions = 'Holiday_List_Name="{}"'.format(filter_to_list)
        return cls.fetch('holiday', conditions)


class TimeReport(SystemReport):
    def __init__(self, **kwargs):
        self.name = 'time'
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    @classmethod
    def fetch_by_business_unit_name(cls, business_unit_name):
        conditions = ['BusGroup="{}"'.format(business_unit_name)]
        return [cls(**time, name='time') for time in cls.fetch('time', conditions)]

    @classmethod
    def fetch_by_time_entry_id(cls, _id):
        conditions = ['Time_RecID={}'.format(_id)]
        reports = [cls(**time, name='time') for time in cls.fetch('time', conditions)]
        if len(reports) > 0:
            return reports[0]
        return None


class SystemReportExpense(SystemReport):
    @classmethod
    def fetch_by_date_range(cls, on_or_after=None, before=None, as_dataframe=False):
        conditions = []
        if on_or_after:
            conditions.append('Date_Expense>=[{}]'.format(on_or_after))
        if before:
            conditions.append('Date_Expense<[{}]'.format(before))
        if as_dataframe:
            df = DataUtil.get_dataframe(cls.fetch('Expense', conditions))
            df['Date_Expense'] = pd.to_datetime(df['Date_Expense'])
            return df
        return [cls(**report, name='Expense') for report in cls.fetch('Expense', conditions)]


class SystemReportProduct(SystemReport):
    name = 'Product'
    date_field = 'Date_Entered'

    @classmethod
    def fetch_by_business_unit_name(cls, business_unit_name):
        conditions = ['BusGroup="{}"'.format(business_unit_name)]
        return [cls(**report, name='Product') for report in cls.fetch('Product', conditions)]

    @classmethod
    def fetch_by_date_range(cls, on_or_after=None, before=None, as_dataframe=False):
        conditions = []
        if on_or_after:
            conditions.append('{}>=[{}]'.format(cls.date_field, on_or_after))
        if before:
            conditions.append('{}<[{}]'.format(cls.date_field, before))
        if as_dataframe:
            df = DataUtil.get_dataframe(cls.fetch(cls.name, conditions))
            df[cls.date_field] = pd.to_datetime(df[cls.date_field])
            return df
        return [cls(**report, name=cls.name) for report in cls.fetch(cls.name, conditions)]

    @classmethod
    def fetch_by_business_unit_id(cls, business_unit_id, on_or_after=None, before=None, as_dataframe=False):
        conditions = ['BusGroup="{}"'.format(constants.BUSINESS_UNIT_NAMES[business_unit_id])]
        if on_or_after:
            conditions.append('{}>=[{}]'.format(cls.date_field, on_or_after))
        if before:
            conditions.append('{}<[{}]'.format(cls.date_field, before))
        data_dict = cls.fetch(cls.name, conditions)
        if as_dataframe:
            df = DataUtil.get_dataframe(data_dict)
            if len(df) > 0:
                df[cls.date_field] = pd.to_datetime(df[cls.date_field])
            return df
        return [cls(**report, name=cls.name) for report in data_dict] if len(data_dict) > 0 else []