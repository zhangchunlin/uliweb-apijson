#coding=utf-8
from uliweb import expose, functions, models
from uliweb.orm import ModelNotFound
from json import loads
import logging

log = logging.getLogger('apijson')

@expose('/apijson')
class ApiJson(object):
    def __begin__(self):
        self.rdict = {
            "code":200,
            "msg":"success"
        }

        try:
            self.request_data = loads(request.data)
        except Exception as e:
            log.error("try to load json but get exception: '%s', request data: %s"%(e,request.data))
            return json({"code":400,"msg":"not json data in the request"})
    
    def get(self):
        for key in self.request_data:
            if key[-2:]=="[]":
                rsp = self._get_array(key)
            else:
                rsp = self._get_one(key)
            if rsp: return rsp

        return json(self.rdict)

    def _get_one(self,key):
        modelname = key
        params = self.request_data[key]

        try:
            model = getattr(models,modelname)
            model_setting = settings.APIJSON_MODELS.get(modelname,{})
        except ModelNotFound as e:
            log.error("try to find model '%s' but not found: '%s'"%(modelname,e))
            return json({"code":400,"msg":"model '%s' not found"%(modelname)})
        model_column_set = None
        q = model.all()

        #rbac check begin
        rbac_get = model_setting.get("rbac_get",{})
        if not rbac_get:
            return json({"code":401,"msg":"'%s' not accessible by apijson"%(modelname)})

        roles = rbac_get.get("roles")
        perms = rbac_get.get("perms")
        params_role = params.get("@role")
        permission_check_ok = False
        user_role = None
        if params_role:
            if params_role not in roles:
                return json({"code":401,"msg":"'%s' not accessible by role '%s'"%(modelname,params_role)})
            if functions.has_role(request.user,params_role):
                permission_check_ok = True
                user_role = params_role
            else:
                return json({"code":401,"msg":"user doesn't have role '%s'"%(params_role)})
        if not permission_check_ok and roles:
            for role in roles:
                if functions.has_role(request.user,role):
                    permission_check_ok = True
                    user_role = role
                    break

        if not permission_check_ok and perms:
            for perm in perms:
                if functions.has_permission(request.user,perm):
                    permission_check_ok = True
                    break

        if not permission_check_ok:
            return json({"code":401,"msg":"no permission"})
        #rbac check end

        filtered = False

        if user_role == "OWNER":
            owner_filtered,q = self._filter_owner(model,model_setting,q)
            if not owner_filtered:
                return  json({"code":401,"msg":"'%s' cannot filter with owner"%(modelname)})
            filtered = True

        params = self.request_data[key]
        if isinstance(params,dict):
            for n in params:
                if n[0]=="@":
                    if n=="@column":
                        model_column_set = set(params[n].split(","))
                elif hasattr(model,n):
                    q = q.filter(getattr(model.c,n)==params[n])
                    filtered = True
                else:
                    return json({"code":400,"msg":"'%s' have no attribute '%s'"%(modelname,n)})
        #default filter is trying to filter with owner
        if not filtered and request.user:
            owner_filtered,q = self._filter_owner(model,model_setting,q)
        o = q.one()
        if o:
            o = o.to_dict()
            secret_fields = model_setting.get("secret_fields")
            if secret_fields:
                for k in secret_fields:
                    del o[k]
            if model_column_set:
                keys = list(o.keys())
                for k in keys:
                    if k not in model_column_set:
                        del o[k]
        self.rdict[key] = o

    def _get_array(self,key):
        params = self.request_data[key]
        query_count = None
        query_page = None
        modelname = None
        model_param = None
        model_column_set = None
        for n in params:
            if n[0]=="@":
                if not query_count and n=="@count":
                    try:
                        query_count = int(params[n])
                    except ValueError as e:
                        log.error("bad param in '%s': '%s'"%(n,params))
                        return json({"code":400,"msg":"@count should be an int, now '%s'"%(params[n])})
                    if query_count<=0:
                        return json({"code":400,"msg":"count should >0, now is '%s' "%(query_count)})
                elif not query_page and n=="@page":
                    #@page begin from 0
                    try:
                        query_page = int(params[n])
                    except ValueError as e:
                        log.error("bad param in '%s': '%s'"%(n,params))
                        return json({"code":400,"msg":"@page should be an int, now '%s'"%(params[n])})
                    if query_page<0:
                        return json({"code":400,"msg":"page should >0, now is '%s' "%(query_page)})

            # TODO: support join in the future, now only support 1 model
            elif not modelname:
                modelname = n
        
        if not modelname:
            return json({"code":400,"msg":"no model found in array query"})

        #model settings
        model_setting = settings.APIJSON_MODELS.get(modelname,{})
        secret_fields = model_setting["secret_fields"]
        
        #model params
        #column
        model_param = params[n]
        model_column = model_param.get("@column")
        if model_column:
            model_column_set = set(model_column.split(","))
        try:
            model = getattr(models,modelname)
        except ModelNotFound as e:
            log.error("try to find model '%s' but not found: '%s'"%(modelname,e))
            return json({"code":400,"msg":"model '%s' not found"%(modelname)})
        #order
        model_order = model_param.get("@order")

        q = model.all()

        #rbac check begin
        rbac_get = model_setting.get("rbac_get",{})
        if not rbac_get:
            return json({"code":401,"msg":"'%s' not accessible by apijson"%(modelname)})

        roles = rbac_get.get("roles")
        perms = rbac_get.get("perms")
        params_role = params.get("@role")
        permission_check_ok = False
        user_role = None
        if params_role:
            if params_role not in roles:
                return json({"code":401,"msg":"'%s' not accessible by role '%s'"%(modelname,params_role)})
            if functions.has_role(request.user,params_role):
                permission_check_ok = True
                user_role = params_role
            else:
                return json({"code":401,"msg":"user doesn't have role '%s'"%(params_role)})
        if not permission_check_ok and roles:
            for role in roles:
                if functions.has_role(request.user,role):
                    permission_check_ok = True
                    user_role = role
                    break

        if not permission_check_ok and perms:
            for perm in perms:
                if functions.has_permission(request.user,perm):
                    permission_check_ok = True
                    break

        if not permission_check_ok:
            return json({"code":401,"msg":"no permission"})
        #rbac check end

        if user_role == "OWNER":
            owner_filtered,q = self._filter_owner(model,model_setting,q)
            if not owner_filtered:
                return  json({"code":401,"msg":"'%s' cannot filter with owner"%(modelname)})

        if query_count:
            if query_page:
                q = q.offset(query_page*query_count)
            q = q.limit(query_count)
        if model_order:
            for k in model_order.split(","):
                if k[-1] == "+":
                    sort_key = k[:-1]
                    sort_order = "asc"
                elif k[-1] == "-":
                    sort_key = k[:-1]
                    sort_order = "desc"
                else:
                    sort_key = k
                    sort_order = "asc"
                column = getattr(model.c,sort_key)
                q = q.order_by(getattr(column,sort_order)())

        def _get_info(i):
            d = i.to_dict()
            if secret_fields:
                for k in secret_fields:
                    del d[k]
            if model_column_set:
                keys = list(d.keys())
                for k in keys:
                    if k not in model_column_set:
                        del d[k]
            return d
        l = [_get_info(i) for i in q]
        self.rdict[key] = l

    def _filter_owner(self,model,model_setting,q):
        owner_filtered = False
        if hasattr(model,"owner_condition"):
            q = q.filter(model.owner_condition())
            owner_filtered = True
        if not owner_filtered:
            user_id_field = model_setting.get("user_id_field")
            if user_id_field:
                q = q.filter(getattr(model.c,user_id_field)==request.user.id)
                owner_filtered = True
        return owner_filtered,q

    def post(self):
        return json(self.rdict)
