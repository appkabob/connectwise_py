from .connectwise import Connectwise


class ScheduleEntry:
    def __init__(self, id, objectId, **kwargs):
        self.id = id
        self.objectId = objectId
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    def __repr__(self):
        return "<Schedule Entry {}>".format(self.id)

    @classmethod
    def fetch_by_object_ids(cls, object_ids, on_or_after=None, before=None):

        schedule_entries = []
        conditions_start = []
        if on_or_after:
            conditions_start.append('dateStart>=[{}]'.format(on_or_after))
        if before:
            conditions_start.append('dateStart<[{}]'.format(before))

        if conditions_start:
            conditions_start = ' and '.join(conditions_start) + ' and '
        else:
            conditions_start = ''

        conditions = []
        for i, object_id in enumerate(object_ids):
            conditions.append('objectId={}'.format(object_id))
            if i > 0 and i % 100 == 0:  # fetch schedule entries for 100 tickets at a time; any more and the query becomes too long
                conditions = conditions_start + '(' + ' or '.join(conditions) + ')'
                schedule_entries.extend([cls(**schedule_entry) for schedule_entry in Connectwise.submit_request('schedule/entries', conditions)])
                conditions = []
        return schedule_entries

    @classmethod
    def fetch_by_object_id(cls, object_id):
        conditions = 'objectId={}'.format(object_id)
        return [cls(**schedule_entry) for schedule_entry in Connectwise.submit_request('schedule/entries', conditions)]