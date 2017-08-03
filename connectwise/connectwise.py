import json
import os
import urllib.parse
from datetime import date, datetime

import requests
import constants

class Connectwise:

    @classmethod
    def submit_request(cls, endpoint, conditions='', filters=None, verb='GET', child_conditions='', fields=None):
        if verb == 'GET':
            return cls.__cw_submit_get_request(endpoint, conditions, filters, child_conditions, fields)
        elif verb == 'POST':
            return cls.__cw_submit_post_request(endpoint, conditions)

    @classmethod
    def __cw_submit_post_request(cls, endpoint, conditions):

        myconditions = {'conditions': conditions}
        r = requests.post(
            'https://{}{}{}'.format(constants.CW_SERVER, constants.CW_QUERY_URL, endpoint),
            headers=constants.CW_HEADERS,
            json=myconditions
        )

        if r.status_code == requests.codes.ok:
            # print('rjson post', r.json())
            return r.json()  # json_data.extend(r.json())
        else:
            # print('error with {}'.format(endpoint))
            raise RuntimeError(r.json()['message'])

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

        if 'system/reports/' in endpoint or 'system/documents/count' == endpoint:
            return json.loads(r.text)

        json_data = []
        page = 1

        while True:
            # print(r.links['next']['url'])
            if r.status_code == requests.codes.ok:
                # print('rjson get', r.json())
                json_data.extend(r.json())
            else:
                # print('error with {}'.format(endpoint))
                raise RuntimeError(r.json()['message'])

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
    def __get_filters_string(endpoint, conditions, filters, child_conditions, fields):
        if endpoint == 'system/documents/count':
            return '{}{}?{}'.format(constants.CW_QUERY_URL, endpoint, conditions)

        if not isinstance(conditions, str):
            conditions_string = ' and '.join(conditions)
        else:
            conditions_string = conditions

        filters_string = '{}{}?conditions={}'.format(constants.CW_QUERY_URL, endpoint,
                                                     urllib.parse.quote_plus(conditions_string))
        filters_string += '&page={}&pageSize={}'.format(filters['page'], filters['pageSize'])
        filters_string += '&childconditions={}'.format(child_conditions)
        if fields: filters_string += '&fields={}'.format(fields)

        if 'orderBy' in filters:
            filters_string += '&orderBy={}'.format(urllib.parse.quote_plus(filters['orderBy']))

        return filters_string

    @staticmethod
    def current_fy():
        return Connectwise.fy_of_date(date.today().strftime('%Y-%m-%d'))

    @staticmethod
    def fy_of_date(the_date):
        # print(the_date)
        the_date = datetime.strptime(the_date, '%Y-%m-%d')
        # print(the_date)
        # print(the_date.month)
        if the_date.month > 6:
            on_or_after = date(the_date.year, constants.FIRST_DAY_OF_FY['month'], constants.FIRST_DAY_OF_FY['day']).strftime('%Y-%m-%d')
            before = date(the_date.year + 1, constants.FIRST_DAY_OF_FY['month'], constants.FIRST_DAY_OF_FY['day']).strftime('%Y-%m-%d')
        else:
            on_or_after = date(the_date.year - 1, constants.FIRST_DAY_OF_FY['month'], constants.FIRST_DAY_OF_FY['day']).strftime('%Y-%m-%d')
            before = date(the_date.year, constants.FIRST_DAY_OF_FY['month'], constants.FIRST_DAY_OF_FY['day']).strftime('%Y-%m-%d')

        return on_or_after, before
