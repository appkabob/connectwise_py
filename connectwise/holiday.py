import datetime

from lib.connectwise_py.connectwise.connectwise import Connectwise
from lib.connectwise_py.connectwise.system_report import SystemReport


class Holiday:
    def __init__(self, **kwargs):
        self.Description = ''
        self.Holiday_Date = ''
        self.Holiday_List_Name = ''
        self.Holiday_List_RecID = ''
        self.Last_Update_UTC = ''
        self.Time_End = ''
        self.Time_Start = ''
        self.Time_Zone = ''
        self.Updated_By = ''
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    @classmethod
    def fetch_all(cls):
        return [cls(**holiday) for holiday in SystemReport.fetch_holiday_list()]

    @classmethod
    def fetch_passed(cls, before=None):
        if not before: before = datetime.datetime.now().strftime('%Y-%m-%d')
        return [h for h in cls.fetch_all() if h.Holiday_Date < before]

    @classmethod
    def fetch_passed_this_fy(cls, before=None):
        if not before: before = datetime.datetime.now().strftime('%Y-%m-%d')
        date_start_this_fy, date_start_next_fy = Connectwise.fy_of_date(before)
        return [h for h in cls.fetch_passed(before) if h.Holiday_Date >= date_start_this_fy]

    @classmethod
    def fetch_future(cls, on_or_after=None):
        if not on_or_after: on_or_after = datetime.datetime.now().strftime('%Y-%m-%d')
        return [h for h in cls.fetch_all() if h.Holiday_Date >= on_or_after]

    @classmethod
    def fetch_remaining_this_fy(cls, on_or_after=None):
        if not on_or_after: on_or_after = datetime.datetime.now().strftime('%Y-%m-%d')
        date_start_this_fy, date_start_next_fy = Connectwise.fy_of_date(on_or_after)
        return [h for h in cls.fetch_future(on_or_after) if h.Holiday_Date < date_start_next_fy]

    @classmethod
    def fetch_this_fy(cls, of_date=None):
        on_or_after, before = Connectwise.fy_of_date(of_date)
        return [h for h in cls.fetch_all() if on_or_after <= h.Holiday_Date < before]
