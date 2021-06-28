import logging


class Module:
    disabled: bool = False

    def __init__(self, bot):
        self.bot = bot
        self.log = logging.getLogger(self.__class__.__name__)
