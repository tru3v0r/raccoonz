from ..constants.config import DEFAULT_PARSER
from ..errors import ParserNotFoundError



def build_parser(name=DEFAULT_PARSER, **kwargs):

    match name:
        
        case "bs4":
            from .models.bs4 import BS4Parser
            return BS4Parser(**kwargs)
        
        case _:
            raise ParserNotFoundError(name)