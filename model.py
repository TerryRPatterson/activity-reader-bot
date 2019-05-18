import datetime
from SpecialDict import IdDictField
from umongo import Document, fields, validate

zero_date = datetime.datetime(year=2015, month=1, day=1)


def get_model(instance):
    @instance.register
    class Guild(Document):
        name = fields.StringField(required=True)

        last_processed = fields.DateTimeField(required=True, default=zero_date)

        id = fields.IntegerField(required=True, attribute='_id')

        last_posts = IdDictField(required=True)

    return Guild
