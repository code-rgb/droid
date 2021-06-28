from typing import Pattern, Union

from .core.base_decorator import BaseDecorator


class OnCmd(BaseDecorator):

    def __init__(self,
                 regex: Union[Pattern[str], str, None] = None,
                 group: int = 0,
                 *args,
                 **kwargs):
        super().__init__(regex=regex, group=group, *args, **kwargs)
