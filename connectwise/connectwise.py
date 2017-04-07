import json
import urllib.parse
import requests
import constants


class Connectwise:

    @classmethod
    def submit_request(cls, endpoint, conditions='', filters=None, verb='GET'):
        if verb == 'GET':
            return cls.__cw_submit_get_request(endpoint, conditions, filters)

    @classmethod
    def __cw_submit_get_request(cls, endpoint, conditions, filters=None):
        if filters is None:
            filters = {
                'page': 1,
                'pageSize': 1000
            }

        filters_string = cls.__get_filters_string(endpoint, conditions, filters)
        r = requests.get('https://{}{}'.format(constants.CW_SERVER, filters_string), headers=constants.HEADERS)

        if endpoint == 'system/reports/holiday':
            return json.loads(r.text)

        json_data = []
        page = 1

        while True:
            # print(r.links['next']['url'])
            if r.status_code == requests.codes.ok:
                json_data.extend(r.json())
            else:
                raise RuntimeError(r.json()['message'])

            try:
                r.links['next']['url']
            except KeyError:
                break

            page += 1
            filters['page'] = page
            filters_string = cls.__get_filters_string(endpoint, conditions, filters)
            r = requests.get(r.links['next']['url'].replace('https://na.', 'https://api-na.', 1),
                             headers=constants.HEADERS)

        return json_data

    @staticmethod
    def __get_filters_string(endpoint, conditions, filters):
        if not isinstance(conditions, str):
            conditions_string = ' and '.join(conditions)
        else:
            conditions_string = conditions

        filters_string = '{}{}?conditions={}'.format(constants.CW_QUERY_URL, endpoint,
                                                     urllib.parse.quote_plus(conditions_string))
        filters_string += '&page={}&pageSize={}'.format(filters['page'], filters['pageSize'])

        if 'orderBy' in filters:
            filters_string += '&orderBy={}'.format(urllib.parse.quote_plus(filters['orderBy']))

        return filters_string
