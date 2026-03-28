class RaccoonError(Exception):
    default = "An error occurred, computers."
    fields = ()

    def __init__(self, *args, detail=None, **kwargs):
        for name, value in zip(self.fields, args):
            kwargs[name] = value
        
        base = self.default.format(**kwargs)
        final = f"{base} ({detail})" if detail else base
        
        self.context = kwargs
        super().__init__(final)




#registry

class BinNotFoundError(RaccoonError):
    default = "Bin '{bin}' not found."
    fields = ("bin",)


class FetcherNotFoundError(RaccoonError):
    default = "Fetcher '{fetcher}' not found."
    fields = ("fetcher",)


class ParserNotFoundError(RaccoonError):
    default = "Parser '{parser}' not found."
    fields = ("parser",)


class EndpointNotFoundError(RaccoonError):
    default = "Endpoint '{endpoint}' not found."
    fields = ("endpoint",)



#runtime

class FetchingError(RaccoonError):
    default = "Error while trying to fetch {url}."
    fields = ("url",)


class DiggingError(RaccoonError):
    default = "Error while digging."



#validation

class BinKeyError(RaccoonError):
    default = "Could not find expected '{key}' key in bin '{bin}'."


class SelectorSyntaxError(RaccoonError):
    default = "Invalid selector syntax."
    fields = ("selector",)