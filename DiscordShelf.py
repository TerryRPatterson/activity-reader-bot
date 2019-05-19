from shelve import DbfilenameShelf

class DiscordShelf(DbfilenameShelf):
    def __contains__(self, key):
        key = str(key)
        return super().__contains__(key)

    def __getitem__(self, key):
        key = str(key)
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        key = str(key)
        return super().__setitem__(key, value)
    
    def __delitem__(self, key):
        key = str(key)
        return super().__delitem__(key)

    def get(self, key, default=None):
        key = str(key)
        return super().get(key, default)


def open(filename, flag='c', protocol=None, writeback=False):
    return DiscordShelf(filename, flag, protocol, writeback)