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
    def fetch_future(cls):
        return [d for d in cls.fetch_all() if d.Holiday_Date > datetime.datetime.now().strftime('%Y-%m-%d')]

    @classmethod
    def fetch_remaining_this_fy(cls):
        on_or_after, before = Connectwise.current_fy()
        return [d for d in cls.fetch_future() if d.Holiday_Date < before]

    @classmethod
    def fetch_this_fy(cls):
        on_or_after, before = Connectwise.current_fy()
        return [d for d in cls.fetch_all() if on_or_after <= d.Holiday_Date < before]
