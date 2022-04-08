#coding=utf-8
from uliweb import expose, functions, settings

@expose('/tables')
class Tables(object):
    @expose('')
    def list(self):
        if request.user:
            role = "ADMIN" if functions.has_role(request.user,"ADMIN") else "OWNER"
        else:
            role = "UNKNOWN"
        apijson_tables = functions.get_apijson_tables()
        def _get_model(i):
            model_name = i.model_name
            return settings.APIJSON_MODELS.get(model_name,{})
        models = [_get_model(i) for i in apijson_tables]
        def _get_request(i):
            request_tag = i.request_tag or i.model_name
            return settings.APIJSON_REQUESTS.get(request_tag,{})
        requests = [_get_request(i) for i in apijson_tables]
        return {
            "apijson_tables_json":json_dumps([d.to_dict() for d in apijson_tables]),
            "models_json": json_dumps(models),
            "requests_json": json_dumps(requests),
            "role":role,
        }
