#coding=utf-8

def get_apijson_tables(role="UNKNOWN"):
    from uliweb import settings
    apijson_tables = dict(settings.APIJSON_TABLES.iteritems())
    for n in apijson_tables:
        c = apijson_tables[n]
        editable = c["editable"]
        if editable=="auto":
            editable = False
            POST = settings.APIJSON_MODELS[n]["POST"]
            if POST:
                roles = POST["roles"]
                if roles:
                    editable = role in roles
            c["editable"] = editable
    return apijson_tables
