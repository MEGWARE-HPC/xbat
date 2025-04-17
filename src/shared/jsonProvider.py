import json
import numpy as np
from datetime import date, datetime
from flask.json.provider import DefaultJSONProvider


class CustomEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super(CustomEncoder, self).default(obj)


class CustomJSONProvider(DefaultJSONProvider):

    sort_keys = False

    def dumps(self, obj, **kwargs):
        # overwrite connexion json cls
        kwargs["cls"] = CustomEncoder
        return json.dumps(obj, **kwargs)

    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)
