#coding=utf-8
from uliweb import expose, functions
from json import dumps

@expose('/tables')
class Tables(object):
    @expose('')
    def list(self):
        table_keys = settings.APIJSON_MODELS.keys()
        if request.user and functions.has_role(request.user,"ADMIN"):
            role = "ADMIN"
        elif request.user:
            role = "LOGIN"
        else:
            role = "UNKNOWN"
        return {
            "table_keys_json":dumps(table_keys),
            "role":role
        }
