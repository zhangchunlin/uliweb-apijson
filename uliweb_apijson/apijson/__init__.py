#coding=utf-8

def get_apijson_tables(role="UNKNOWN"):
    from uliweb import settings

    s = settings.APIJSON_TABLES
    if s:
        apijson_tables = dict(s.iteritems())
    else:
        return {}
    for n in apijson_tables:
        c = apijson_tables[n]
        editable = c.get("editable",False)
        _model_name = c.get("@model_name") or n
        if editable=="auto":
            editable = False
            POST = settings.APIJSON_MODELS.get(_model_name,{}).get("POST")
            if POST:
                roles = POST["roles"]
                if roles:
                    editable = role in roles
            c["editable"] = editable
    return apijson_tables

def get_apijson_table(role="UNKNOWN",name=None):
    from uliweb import settings

    if not name:
        return {}
    s = settings.APIJSON_TABLES
    if s:
        apijson_tables = dict(s.iteritems())
    else:
        return {}
    
    c = apijson_tables.get(name)
    if not c:
        return {}
    editable = c.get("editable",False)
    _model_name = c.get("@model_name") or n
    if editable=="auto":
        editable = False
        POST = settings.APIJSON_MODELS.get(_model_name,{}).get("POST")
        if POST:
            roles = POST["roles"]
            if roles:
                editable = role in roles
        c["editable"] = editable
    return c
