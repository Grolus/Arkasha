from typing import Any
import logers

class Base(BaseException):
    loger = logers.base_loger
    def __init__(self, msg: str=""):
        self.msg = msg
        self.loger.error(self.msg)


class ParsingError(Base):
    loger = logers.handle_loger
    def __init__(self, text_to_parse: str, expected_value: Any):
        msg = f'Can not parse `{expected_value!r}` from string "{text_to_parse}"'
        super().__init__(msg)

        
