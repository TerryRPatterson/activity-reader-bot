from umongo.data_objects import Dict as umongo_dict
from umongo.fields import DictField as umongo_dict_field


class IdDict(umongo_dict):
    def __getitem__(self, key):
        key = str(key)
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        key = str(key)
        super().set_modified()
        return super().__setitem__(key, value)

    def __contains__(self, key):
        key = str(key)
        return super().__contains__(key)


class IdDictField(umongo_dict_field):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', IdDict)
        super().__init__(*args, **kwargs)

    def _deserialize(self, value, attr, data):
        value = super()._deserialize(value, attr, data)
        return IdDict(value)

    def _deserialize_from_mongo(self, value):
        if value:
            return IdDict(value)
        else:
            return IdDict()
