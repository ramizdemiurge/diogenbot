import supycache

from model.database_model import Groups, Settings


class GroupDAO:

    @staticmethod
    @supycache.supycache(cache_key='all_groups', max_age=10 * 60)
    def get_all_groups():
        return Groups.select()

    @staticmethod
    @supycache.supycache(cache_key='group_id_{0}', max_age=10 * 60)
    def get_group_by_id(id):
        group_query = Groups.select().where(Groups.chat_id == id).limit(1)
        if group_query.exists():
            return group_query.first()

    @staticmethod
    @supycache.supycache(cache_key='group_name_{0}', max_age=10 * 60)
    def get_group_by_name(name):
        group_query = Groups.select().where(Groups.group_name == name).limit(1)
        if group_query.exists():
            return group_query.first()

    @staticmethod
    def create_group(name, id):
        settings_obj = Settings.create()
        if name is None:
            import random
            import string
            name = ''.join(
                [random.choice(string.ascii_letters + string.digits) for n in range(4)]).lower()
        return Groups.create(group_name=name, chat_id=id, settings=settings_obj, force_insert=True)
