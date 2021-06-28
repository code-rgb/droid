from pyrogram.types import Message


class Ctx:
    def __init__(self, message: Message) -> None:
        self.msg = message
