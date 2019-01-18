#coding=utf-8
from uliweb import expose, functions

@expose('/tables')
class Tables(object):
    @expose('')
    def list(self):
        table_keys = settings.APIJSON_MODELS.keys()
        if request.user:
            if functions.has_role(request.user,"ADMIN"):
                role = "ADMIN"
            else:
                role = "OWNER"
        else:
            role = "UNKNOWN"
        apijson_tables = functions.get_apijson_tables(role)
        return {
            "table_keys_json":json_dumps(table_keys),
            "apijson_tables_json":json_dumps(apijson_tables),
            "role":role,
        }
