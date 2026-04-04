class Object:
    def __init__(self, dictionary):
        for k, v in dictionary.items():
            setattr(self, k, self._wrap(v))

    def _wrap(self, value):
        if isinstance(value, dict):
            return Object(value)
        if isinstance(value, list):
            return [self._wrap(v) for v in value]
        return value