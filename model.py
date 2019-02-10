import mongoengine as mdb


class Server(mdb.Document):
    name = name = mdb.StringField(required=True)

    last_processed_id = mdb.LongField(required=True, default=0)

    id = mdb.LongField(required=True, primary_key=True)

    last_posts = mdb.DictField(required=True, default={})
