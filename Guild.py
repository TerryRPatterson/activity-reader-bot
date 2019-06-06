import datetime

from box import Box

zero_date = datetime.datetime(year=2015, month=1, day=1)


class Guild(Box):
    def __init__(self, name, id):
        super().__init__()
        self.name = name
        self.id = id
        self.last_posts = Box()
        self.last_processed = zero_date

