#coding=utf-8

from uliweb import settings, models, request, functions, UliwebError
from uliweb.orm import ModelNotFound
from json import dumps as json_dumps
import logging

log = logging.getLogger('apijson')


class ApijsonTable(object):
    def __init__(self, model_name, request_tag=None, role=None, tableui_name=None, table_name=None):
        self.model_name = model_name
        self.request_tag = request_tag or self.model_name
        self.role = role
        self.tableui_name = tableui_name or self.model_name
        self.table_name = table_name
        self._get_tableui()
        self._apply_auto()

    def _get_tableui(self):
        self.tableui = settings.APIJSON_TABLE_UI.get(self.tableui_name, {})
        if not self.tableui:
            log.warn("cannot find setting for {} in settings.APIJSON_TABLE_UI".format(self.tableui_name))

    def _apply_auto(self):
        editable = self.tableui.get("editable", False)
        if editable == "auto":
            editable = False
            POST = settings.APIJSON_MODELS.get(self.model_name, {}).get("POST")
            if POST:
                roles = POST["roles"]
                if roles:
                    editable = self.role in roles
            self.tableui["editable"] = editable

    def to_dict(self):
        return dict(model_name=self.model_name,
                    request_tag=self.request_tag,
                    role=self.role,
                    tableui_name=self.tableui_name,
                    table_name=self.table_name,
                    tableui=self.tableui)


def get_apijson_tables():
    def iter_table():
        s = settings.APIJSON_TABLES
        apijson_tables = dict(s.iteritems()) if s else {}
        if apijson_tables:
            for k in apijson_tables:
                v = apijson_tables[k]
                model_name = v.get("model_name") or k
                tableui_name = v.get("tableui_name") or model_name
                if not model_name:
                    model_name = tableui_name
                if model_name and tableui_name:
                    request_tag = v.get("request_tag")
                    role = v.get("role")
                    yield(ApijsonTable(model_name=model_name, request_tag=request_tag, role=role, tableui_name=tableui_name, table_name=k))
        else:
            apison_table_ui = dict(
                settings.APIJSON_TABLE_UI.iteritems())
            for tableui_name in apison_table_ui:
                tableui = apison_table_ui[tableui_name]
                model_name = tableui.get("@model_name") or tableui_name
                request_tag = model_name
                role = None
                yield(ApijsonTable(model_name=model_name, request_tag=request_tag, role=role, tableui_name=tableui_name))
    return list(iter_table())


def get_apijson_table(*args, **kwargs):
    return ApijsonTable(*args, **kwargs)

class ApiJsonModelQuery(object):
    def __init__(self,name,params,parent,key):
        self.name = name
        self.params = params
        self.parent = parent
        self.key = key
        self.query_params = self.parent.request_data[key]

        try:
            self.model = getattr(models,name)
        except ModelNotFound as e:
            log.error("try to find model '%s' but not found: '%s'"%(name,e))
            raise UliwebError("model '%s' not found"%(name))

        self.setting = settings.APIJSON_MODELS.get(name,{})
        self.secret_fields = self.setting.get("secret_fields")
        self.column = params.get("@column")
        if self.column:
            self.column_set = set(self.column.split(","))
            if self.secret_fields:
                self.column_set -= set(self.secret_fields)
            self.column_set &= set(self.model.columns.keys())
        else:
            self.column_set = None
        
        self.permission_check_ok = False

    def _check_GET_permission(self):
        GET = self.setting.get("GET")
        if not GET:
            raise UliwebError("'%s' not accessible by apijson"%(self.name))
    
        roles = GET.get("roles")
        params_role = self.params.get("@role")
        user = getattr(request, "user", None)

        if roles:
            if not params_role:
                if user:
                    params_role = "LOGIN"
                else:
                    params_role = "UNKNOWN"
            elif params_role != "UNKNOWN":
                if not user:
                    raise UliwebError("no login user for role '%s'" % (params_role))
            if params_role not in roles:
                raise UliwebError("'%s' not accessible by role '%s'" % (self.name, params_role))
            if params_role == "UNKNOWN":
                self.permission_check_ok = True
            elif functions.has_role(user, params_role):
                self.permission_check_ok = True
            else:
                raise UliwebError("user doesn't have role '%s'" % (params_role))
        if not self.permission_check_ok:
            perms = GET.get("permissions")
            if perms:
                if params_role:
                    role, msg = functions.has_permission_as_role(user, params_role, *perms)
                    if role:
                        self.permission_check_ok = True
                else:
                    role = functions.has_permission(user, *perms)
                    if role:
                        role_name = getattr(role, "name")
                        if role_name:
                            self.permission_check_ok = True
                            params_role = role_name

        if not self.permission_check_ok:
            raise UliwebError("no permission")
        
        self.params_role = params_role

    def _get_array_params(self):
        query_count = self.query_params.get("@count")
        if query_count:
            try:
                query_count = int(query_count)
            except ValueError as e:
                log.error("bad param in '%s': '%s'"%(query_count,self.query_params))
                raise UliwebError("@count should be an int, but get '%s'"%(query_count))
        self.query_count = query_count

        query_page = self.query_params.get("@page")
        if query_page:
            #@page begin from 0
            try:
                query_page = int(query_page)
            except ValueError as e:
                log.error("bad param in '%s': '%s'"%(query_page,self.query_params))
                raise UliwebError("@page should be an int, but get '%s'"%(query_page))
            if query_page<0:
                raise UliwebError("page should >0, but get '%s'"%(query_page))
        self.query_page = query_page

        #https://github.com/TommyLemon/APIJSON/blob/master/Document.md#32-%E5%8A%9F%E8%83%BD%E7%AC%A6
        query_type = self.query_params.get("@query",0)
        if query_type not in [0,1,2]:
            raise UliwebError("bad param 'query': %s"%(query_type))
        self.query_type = query_type

        #order not in query params but in model params
        self.order = self.params.get("@order")

    def _filter_owner(self,q):
        owner_filtered = False
        if hasattr(self.model,"owner_condition"):
            q = q.filter(self.model.owner_condition(request.user.id))
            owner_filtered = True
        if not owner_filtered:
            user_id_field = self.setting.get("user_id_field")
            if user_id_field:
                q = q.filter(getattr(self.model.c,user_id_field)==request.user.id)
                owner_filtered = True
        if not owner_filtered:
            raise UliwebError("'%s' cannot filter with owner"%(self.name))
        return q

    def _get_array_q(self,params):
        q = self.model.all()
        if self.params_role == "OWNER":
            q = self._filter_owner(q)

        #@expr
        model_expr = params.get("@expr")
        if model_expr!=None:
            c = self.parent._expr(self.model,params,model_expr)
            q = q.filter(c)
        else:
            for n in params:
                if n[0]!="@":
                    c = self.parent._get_filter_condition(self.model,params,n)
                    q = q.filter(c)
        return q

    def _get_info(self,i,as_dict_child=False):
        if (not i):
            return {}
        d = i.to_dict()
        if self.secret_fields:
            for k in self.secret_fields:
                del d[k]
        if self.column_set:
            keys = list(d.keys())
            for k in keys:
                if k not in self.column_set:
                    del d[k]
        if as_dict_child:
            resultd = {}
            resultd[self.name] = d
            return resultd
        else:
            return d

    def query_array(self):
        self._check_GET_permission()
        self._get_array_params()
        params = self.params.copy()

        #update reference
        ref_fields = []
        refs = {}
        for n in params:
            if n[-1]=="@":
                ref_fields.append(n)
                col_name = n[:-1]
                path = params[n]
                refs[col_name] = self.parent._ref_get(path)
        if ref_fields:
            for i in ref_fields:
                del params[i]
            params.update(refs)

        q = self._get_array_q(params)
        
        if self.query_type in [1,2]:
            self.parent.vars["/%s/total"%(self.key)] = q.count()

        if self.query_type in [0,2]:
            if self.query_count:
                if self.query_page:
                    q = q.offset(self.query_page*self.query_count)
                q = q.limit(self.query_count)
            if self.order:
                for k in self.order.split(","):
                    if k[-1] == "+":
                        sort_key = k[:-1]
                        sort_order = "asc"
                    elif k[-1] == "-":
                        sort_key = k[:-1]
                        sort_order = "desc"
                    else:
                        sort_key = k
                        sort_order = "asc"
                    try:
                        column = getattr(self.model.c,sort_key)
                    except AttributeError as e:
                        raise UliwebError("'%s' doesn't have column '%s'"%(self.name,sort_key))
                    q = q.order_by(getattr(column,sort_order)())
            l = [self._get_info(i,True) for i in q]
            self.parent.rdict[self.key] = l

    def associated_query_array(self):
        self._check_GET_permission()
        self._get_array_params()
        for item in self.parent.rdict[self.key]:
            params = self.params.copy()
            #update reference
            ref_fields = []
            refs = {}
            for n in params:
                if n[-1]=="@":
                    ref_fields.append(n)
                    col_name = n[:-1]
                    path = params[n]
                    refs[col_name] = self.parent._ref_get(path,context=item)
            if ref_fields:
                for i in ref_fields:
                    del params[i]
                params.update(refs)
            q = self._get_array_q(params)
            item[self.name] = self._get_info(q.one())

def is_obj_owner(user, obj, user_id_field):
    if user and user_id_field:
        return obj.to_dict().get(user_id_field)==user.id
    return False

def has_obj_role(user, obj, user_id_field, as_role, *roles):
    from uliweb import  functions
    if as_role:
        if as_role not in roles:
            return False, "role '%s' has no permission to access the data"%(as_role)
        if not functions.has_role(user, as_role):
            return False, "user has no role '%s'"%(as_role)
        if as_role == "OWNER":
            if not is_obj_owner(user, obj, user_id_field):
                return False, "user is not the owner of data"
        return True, None
    else:
        for role in roles:
            if functions.has_role(user, role):
                if isinstance(role,str):
                    role_name = role
                elif hasattr(role, "name"):
                    role_name = role.name
                else:
                    continue
                if role_name == "OWNER":
                    if is_obj_owner(user, obj, user_id_field):
                        return True, None
                    else:
                        continue
                else:
                    return True, None
        return False, "no role to access the data"

def has_obj_permission(user, obj, user_id_field, *perms):
    from uliweb import  functions, models

    Role = models.role
    Perm = models.permission

    for name in perms:
        perm = Perm.get(Perm.c.name == name)
        if not perm:
            continue
        has, msg = functions.has_obj_role(user, obj, user_id_field, None, *list(perm.perm_roles.with_relation().all()))
        if has:
            return has, None
    return False, "no permission"

def has_permission_as_role(user, as_role, *perms):
    from uliweb import  functions, models

    Role = models.role
    Perm = models.permission

    flag = functions.has_role(user, as_role)
    if not flag:
        return False, "user has no role '%s'"%(as_role)

    for name in perms:
        perm = Perm.get(Perm.c.name==name)
        if not perm:
            continue
        for role in perm.perm_roles.with_relation().all():
            if role.name == as_role:
                return role, None
    return False, "no permission"
