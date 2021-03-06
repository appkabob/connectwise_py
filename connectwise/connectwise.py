import json
import urllib.parse
from datetime import date, datetime, timedelta
import requests
from dateutil.relativedelta import relativedelta
import constants


class Connectwise:

    @classmethod
    def submit_request(cls, endpoint, conditions='', filters=None, verb='GET', child_conditions='', fields=None):
        if conditions or conditions == []:
            if 'search' in endpoint or verb != 'POST': conditions = cls.conditions_to_str(conditions)
        if verb == 'GET':
            return cls.__cw_submit_get_request(endpoint, conditions, filters, child_conditions, fields)
        elif verb == 'POST':
            return cls.__cw_submit_post_request(endpoint, conditions)

    @staticmethod
    def update_record(endpoint, record_id, path, value, operation='replace'):
        conditions = json.dumps([{'op': operation, 'path': path, 'value': value}])
        r = requests.patch(
            'https://{}{}{}/{}'.format(constants.CW_SERVER, constants.CW_QUERY_URL, endpoint, record_id),
            headers=constants.CW_HEADERS,
            data=conditions
        )
        if r.status_code == requests.codes.ok or r.ok == True or r.status_code == 201:
            return r.json()  # json_data.extend(r.json())
        else:
            raise RuntimeError('\n{}\n{}\n{}\n{}'.format('{} {}'.format(r.status_code, r.reason), r.url, 'id: {}, op: {}, path: {}, value: {}'.format(record_id, operation, path, value), r.json()['message'] if hasattr(r, 'json') else ''))

    @classmethod
    def __cw_submit_post_request(cls, endpoint, conditions):
        if 'search' in endpoint:
            conditions = {'conditions': conditions}

        r = requests.post(
            'https://{}{}{}'.format(constants.CW_SERVER, constants.CW_QUERY_URL, endpoint),
            headers=constants.CW_HEADERS,
            json=conditions
        )

        if r.status_code == requests.codes.ok or r.ok == True or r.status_code == 201:
            return r.json()  # json_data.extend(r.json())
        else:
            raise RuntimeError('\n{}\n{}\n{}\n{}'.format('{} {}'.format(r.status_code, r.reason), r.url, conditions, r.json()['message'] if hasattr(r, 'json') else ''))

    @classmethod
    def __cw_submit_get_request(cls, endpoint, conditions, filters=None, child_conditions='', fields=None):
        if filters is None:
            filters = {'page': 1, 'pageSize': 1000}
        if 'page' not in filters:
            filters['page'] = 1
        if 'pageSize' not in filters:
            filters['pageSize'] = 1000

        filters_string = cls.__get_filters_string(endpoint, conditions, filters, child_conditions, fields)
        r = requests.get('https://{}{}'.format(constants.CW_SERVER, filters_string), headers=constants.CW_HEADERS)

        json_data = []
        page = 1

        while True:
            if r.status_code == requests.codes.ok or r.ok == True or r.status_code == 201:
                if 'system/reports/' in endpoint or 'system/documents/count' == endpoint:
                    json_data.extend(cls.__system_report_to_dict(json.loads(r.text)))
                else:
                    json_data.extend(r.json())
            else:
                raise RuntimeError('\n{}\n{}\n{}\n{}'.format('{} {}'.format(r.status_code, r.reason), r.url, conditions,
                                                             r.json()['message'] if hasattr(r, 'json') else ''))

            try:
                r.links['next']['url']
            except KeyError:
                break

            page += 1
            filters['page'] = page
            filters_string = cls.__get_filters_string(endpoint, conditions, filters, child_conditions, fields)
            r = requests.get(r.links['next']['url'].replace('https://na.', 'https://api-na.', 1),
                             headers=constants.CW_HEADERS)

        return json_data

    @staticmethod
    def __system_report_to_dict(report_data):
        keys = [list(col.keys())[0] for col in report_data['column_definitions']]

        objects = []
        for object_values in report_data['row_values']:
            object = {}
            for key in keys:
                object[key] = object_values[keys.index(key)]
            objects.append(object)

        return objects

    @staticmethod
    def __get_filters_string(endpoint, conditions, filters, child_conditions, fields):
        if endpoint == 'system/documents/count':
            return '{}{}?{}'.format(constants.CW_QUERY_URL, endpoint, conditions)

        filters_string = '{}{}?conditions={}'.format(constants.CW_QUERY_URL, endpoint,
                                                     urllib.parse.quote_plus(conditions))

        filters_string += '&page={}&pageSize={}'.format(filters['page'], filters['pageSize'])
        if child_conditions: filters_string += '&childconditions={}'.format(child_conditions)
        if fields: filters_string += '&fields={}'.format(fields)

        if 'orderBy' in filters:
            filters_string += '&orderBy={}'.format(urllib.parse.quote_plus(filters['orderBy']))

        return filters_string

    @staticmethod
    def conditions_to_str(conditions):
        if not isinstance(conditions, str):
            conditions_string = ' and '.join(conditions)
        else:
            conditions_string = conditions
        return conditions_string

    @staticmethod
    def current_fy(return_format='%Y-%m-%d'):
        """
        Return the start and end dates of the current Financial Year
        :param return_format: the format to return the dates in. Defaults to %Y-%m-%d. Set to 'date_object' for date objects
        :return: Tuple of dates as either strings or date objects
        """
        return Connectwise.fy_of_date(date.today().strftime('%Y-%m-%d'), return_format)

    @staticmethod
    def fy_of_date(the_date, return_format='%Y-%m-%d'):
        """
        Return the start and end dates of the Financial Year of the given date
        :param the_date: the date to return the FY for
        :param return_format: String format to return the dates in.
        Returns a date object if return_format == False or 'date_object'
        :return: Tuple of dates as either strings or date objects
        """
        # print(the_date)
        the_date = datetime.strptime(the_date, '%Y-%m-%d')
        # print(the_date)
        # print(the_date.month)
        if the_date.month > 6:
            on_or_after = datetime(the_date.year, constants.FIRST_DAY_OF_FY['month'], constants.FIRST_DAY_OF_FY['day'])
            before = datetime(the_date.year + 1, constants.FIRST_DAY_OF_FY['month'], constants.FIRST_DAY_OF_FY['day'])
        else:
            on_or_after = datetime(the_date.year - 1, constants.FIRST_DAY_OF_FY['month'], constants.FIRST_DAY_OF_FY['day'])
            before = datetime(the_date.year, constants.FIRST_DAY_OF_FY['month'], constants.FIRST_DAY_OF_FY['day'])

        if return_format == 'date_object' or return_format == 'date' or not return_format:
            return on_or_after, before
        else:  # return date object
            return on_or_after.strftime(return_format), before.strftime(return_format)

    @staticmethod
    def fy_start_dates(of_date=None):
        if of_date:
            first_day_this_fy, first_day_next_fy = Connectwise.fy_of_date(of_date)
        else:
            first_day_this_fy, first_day_next_fy = Connectwise.current_fy()
        first_day_3_fy_ago = (datetime.strptime(first_day_this_fy, '%Y-%m-%d') - relativedelta(years=3)).strftime(
            '%Y-%m-%d')
        first_day_2_fy_ago = (
            datetime.strptime(first_day_this_fy, '%Y-%m-%d') - relativedelta(years=2)).strftime(
            '%Y-%m-%d')
        first_day_last_fy = (
            datetime.strptime(first_day_this_fy, '%Y-%m-%d') - relativedelta(years=1)).strftime(
            '%Y-%m-%d')

        return [first_day_next_fy, first_day_this_fy, first_day_last_fy, first_day_2_fy_ago, first_day_3_fy_ago]

    @classmethod
    def workdays_remaining_in_fy(cls, on_or_after=None):
        """
        Returns the count of workdays (weekdays - holidays) from the on_or_after date (inclusive) to the end
        of the corresponding FY. Make sure Holidays setup table is up to date.
        :param on_or_after: date string in format '%Y-%m-%d'. If left blank, will default to current date
        :return: Count of workdays that remain from on_or_after date until the end of the FY
        """
        from lib.connectwise_py.connectwise.holiday import Holiday
        if not on_or_after: on_or_after = datetime.now().strftime('%Y-%m-%d')
        date_start_this_fy, date_start_next_fy = cls.fy_of_date(on_or_after, return_format='date_object')
        on_or_after = datetime.strptime(on_or_after, '%Y-%m-%d')
        future_day_generator = (on_or_after + timedelta(x + 1) for x in range((date_start_next_fy - on_or_after).days))
        return sum(day.weekday() < 5 for day in future_day_generator) - len(Holiday.fetch_remaining_this_fy(on_or_after.strftime('%Y-%m-%d')))

    @classmethod
    def workdays_passed_in_fy(cls, before=None):
        """
        Returns the count of workdays (weekdays - holidays) from the start of the FY that 'before' is in,
        up until (but not including) the 'before' date. Make sure Holidays setup table is up to date.
        :param before: date string in format '%Y-%m-%d'. If left blank, will default to current date.
        :return: Count of workdays that have elapsed from start of FY until the 'before' date
        """
        from lib.connectwise_py.connectwise.holiday import Holiday
        if not before: before = datetime.now().strftime('%Y-%m-%d')
        date_start_this_fy, date_start_next_fy = cls.fy_of_date(before, return_format='date_object')
        before = datetime.strptime(before, '%Y-%m-%d')
        past_day_generator = (date_start_this_fy + timedelta(x + 1) for x in range((before - date_start_this_fy).days))
        return sum(day.weekday() < 5 for day in past_day_generator) - len(Holiday.fetch_passed_this_fy(before.strftime('%Y-%m-%d')))

    @staticmethod
    def get_custom_field_value(cw_object, key):
        if hasattr(cw_object, 'customFields'):
            field = [field for field in cw_object.customFields if field['caption'] == key]
            if field: field = field[0]
            if 'value' in field and field['value']:
                return field['value']
        return None

    @staticmethod
    def get_custom_field_value_from_id(cw_object, _id):
        if hasattr(cw_object, 'customFields'):
            field = [field for field in cw_object.customFields if field['id'] == _id]
            if field: field = field[0]
            if 'value' in field and field['value']:
                return field['value']
        return None

    @staticmethod
    def get_charge_to_info(cw_object, tickets=[], activities=[], charge_codes=[], return_type='string', include_company=True, include_project_name=True, include_phase=True, bold_first_item=False):
        """cw_object can be Time Entry, Expense Entry, or Schedule Entry you want to get charge_to info for.
        You can return a string or a dict using the return_type parameter"""

        from lib.connectwise_py.connectwise.activity import Activity
        from lib.connectwise_py.connectwise.ticket import Ticket

        charge_to_id = None
        charge_to_type = None
        company_name = None

        if hasattr(cw_object, 'chargeToId'):
            charge_to_id = cw_object.chargeToId
            charge_to_type = cw_object.chargeToType
            company_name = cw_object.company['name']
        elif hasattr(cw_object, 'objectId'):
            charge_to_id = cw_object.objectId

            ticket = []
            if tickets: ticket = [ticket for ticket in tickets if ticket.id == charge_to_id]

            if len(ticket) > 0: ticket = ticket[0]
            else: ticket = Ticket.fetch_by_id(charge_to_id)

            if ticket:
                charge_to_type = ticket.recordType
                company_name = ticket.company['name']
            else:
                activity = []
                if activities: activity = [activity for activity in activities if activity.id == charge_to_id]

                if len(activity) > 0: activity = activity[0]
                else: activity = Activity.fetch_by_id(charge_to_id)

                if activity:
                    charge_to_type = 'Activity'
                    company_name = activity.company['name']
                else:
                    charge_to_type = 'Charge Code'
                    company_name = 'CEC'

        if charge_to_type == 'Activity':
            if activities:
                activity = [activity for activity in activities if charge_to_id == activity.id]
                if len(activity) > 0:
                    activity = activity[0]
                else:
                    activity = Activity.fetch_by_id(charge_to_id)
            else:
                activity = Activity.fetch_by_id(charge_to_id)
            output = []
            if hasattr(activity, 'opportunity'): output.append('{}'.format(activity.opportunity['name']))
            output.append('Activity #{}: {}'.format(activity.id, activity.name))

        elif charge_to_type == 'ProjectTicket' or charge_to_type == 'ServiceTicket':
            if tickets:
                ticket = [ticket for ticket in tickets if charge_to_id == ticket.id]
                if len(ticket) > 0:
                    ticket = ticket[0]
                else:
                    ticket = Ticket.fetch_by_id(charge_to_id)
            else:
                ticket = Ticket.fetch_by_id(charge_to_id)
            output = []
            if include_project_name and ticket.project: output.append('{}'.format(ticket.project['name']))
            if include_phase and ticket.phase: output.append('{}'.format(ticket.phase['name']))
            output.append('Ticket #{}: {}'.format(ticket.id, ticket.summary))

        else:
            output = [charge_to_type, '{}'.format(charge_to_id)]

        if include_company:
            output.insert(0, company_name)

        if bold_first_item:
            first_item = output.pop(0)
            output.insert(0, '<strong>{}</strong>'.format(first_item))

        if return_type == 'string':
            return ' / '.join(output)
        elif return_type == 'list':
            return output

        return output
