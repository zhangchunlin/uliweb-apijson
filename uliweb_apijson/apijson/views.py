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
        GET = model_setting.get("GET",{})
        if not GET:
            return json({"code":401,"msg":"'%s' not accessible by apijson"%(modelname)})

        roles = GET.get("roles")
        perms = GET.get("perms")
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
        secret_fields = model_setting.get("secret_fields")
        
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
        GET = model_setting.get("GET",{})
        if not GET:
            return json({"code":401,"msg":"'%s' not accessible by apijson"%(modelname)})

        roles = GET.get("roles")
        perms = GET.get("perms")
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
        tag = self.request_data.get("@tag")
        for key in self.request_data:
            if key[0]!="@":
                rsp = self._post_one(key,tag)
                if rsp:
                    return rsp
                else:
                    #only accept one table
                    return json(self.rdict)
        return json(self.rdict)

    def _post_one(self,key,tag):
        tag = tag or key
        modelname = key
        params = self.request_data[key]
        params_role = params.get("@role")

        try:
            model = getattr(models,modelname)
            model_setting = settings.APIJSON_MODELS.get(modelname,{})
            request_setting_tag = settings.APIJSON_REQUESTS.get(tag,{})
            user_id_field = model_setting.get("user_id_field")
        except ModelNotFound as e:
            log.error("try to find model '%s' but not found: '%s'"%(modelname,e))
            return json({"code":400,"msg":"model '%s' not found"%(modelname)})

        request_setting_model = request_setting_tag.get(modelname,{})
        request_setting_POST =  request_setting_model.get("POST",{})
        ADD = request_setting_POST.get("ADD")
        permission_check_ok = False
        if ADD:
            ADD_role = ADD.get("@role")
            if ADD_role and not params_role:
                params_role = ADD_role

        POST = model_setting.get("POST")
        if POST:
            roles = POST.get("roles")
            if params_role:
                if not params_role in roles:
                    return json({"code":401,"msg":"'%s' not accessible by role '%s'"%(modelname,params_role)})
                roles = [params_role]

            if roles:
                for role in roles:
                    if role == "OWNER":
                        if request.user:
                            permission_check_ok = True
                            if user_id_field:
                                params[user_id_field] = request.user.id
                            else:
                                #need OWNER, but don't know how to set user id
                                return json({"code":400,"msg":"no permission"})
                            break
                    else:
                        if functions.has_role(request.user,role):
                            permission_check_ok = True
                            break
        if not permission_check_ok:
            return json({"code":400,"msg":"no permission"})

        DISALLOW = request_setting_POST.get("DISALLOW")
        if DISALLOW:
            for field in DISALLOW:
                if field in params:
                    log.error("request '%s' disallow '%s'"%(tag,field))
                    return json({"code":400,"msg":"request '%s' disallow '%s'"%(tag,field)})

        NECESSARY = request_setting_POST.get("NECESSARY")
        if NECESSARY:
            for field in NECESSARY:
                if field not in params:
                    log.error("request '%s' don't have necessary field '%s'"%(tag,field))
                    return json({"code":400,"msg":"request '%s' don't have necessary field '%s'"%(tag,field)})

        obj = model(**params)
        ret = obj.save()
        obj_dict = obj.to_dict(convert=False)
        secret_fields = model_setting.get("secret_fields")
        if secret_fields:
            for k in secret_fields:
                del obj_dict[k]

        if ret:
            obj_dict["code"] = 200
            obj_dict["message"] = "success"
        else:
            obj_dict["code"] = 400
            obj_dict["message"] = "fail"
            self.rdict["code"] = 400
            self.rdict["message"] = "fail"

        self.rdict[key] = obj_dict

    def put(self):
        tag = self.request_data.get("@tag")
        for key in self.request_data:
            if key[0]!="@":
                rsp = self._put_one(key,tag)
                if rsp:
                    return rsp
                else:
                    #only accept one table
                    return json(self.rdict)

        return json(self.rdict)

    def _put_one(self,key,tag):
        tag = tag or key
        modelname = key
        params = self.request_data[key]
        params_role = params.get("@role")

        try:
            model = getattr(models,modelname)
            model_setting = settings.APIJSON_MODELS.get(modelname,{})
            request_setting_tag = settings.APIJSON_REQUESTS.get(tag,{})
            user_id_field = model_setting.get("user_id_field")
        except ModelNotFound as e:
            log.error("try to find model '%s' but not found: '%s'"%(modelname,e))
            return json({"code":400,"msg":"model '%s' not found"%(modelname)})
        
        request_setting_model = request_setting_tag.get(modelname,{})
        request_setting_PUT =  request_setting_model.get("PUT",{})
        permission_check_ok = False

        ADD = request_setting_PUT.get("ADD")
        if ADD:
            ADD_role = ADD.get("@role")
            if ADD_role and not params_role:
                params_role = ADD_role

        try:
            id_ = params.get("id")
            if not id_:
                return json({"code":400,"msg":"id param needed"})
            id_ = int(id_)
        except ValueError as e:
            return json({"code":400,"msg":"id '%s' cannot convert to integer"%(params.get("id"))})
        obj = model.get(id_)

        PUT = model_setting.get("PUT")
        if PUT:
            roles = PUT.get("roles")
            if params_role:
                if not params_role in roles:
                    return json({"code":401,"msg":"'%s' not accessible by role '%s'"%(modelname,params_role)})
                roles = [params_role]
            if roles:
                for role in roles:
                    if role == "OWNER":
                        if request.user:
                            if user_id_field:
                                if obj.to_dict().get(user_id_field)==request.user.id:
                                    permission_check_ok = True
                                    break
                        else:
                            return json({"code":400,"msg":"need login user"})
                    else:
                        if functions.has_role(request.user,role):
                            permission_check_ok = True
                            break

        if not permission_check_ok:
            return json({"code":400,"msg":"no permission"})
        
        if not obj:
            return json({"code":400,"msg":"cannot find record id '%s'"%(id_)})
        kwargs = {}
        for k in params:
            if k=="id":
                continue
            elif hasattr(obj,k):
                kwargs[k] = params[k]
            else:
                return json({"code":400,"msg":"'%s' don't have field '%s'"%(modelname,k)})
        obj.update(**kwargs)
        ret = obj.save()
        obj_dict = {"id":id_}
        if ret:
            obj_dict["code"] = 200
            obj_dict["message"] = "success"
            obj_dict["count"] = 1
        else:
            obj_dict["code"] = 400
            obj_dict["message"] = "fail"
            obj_dict["count"] = 0
            self.rdict["code"] = 400
            self.rdict["message"] = "fail"
        self.rdict[key] = obj_dict

    def delete(self):
        return json(self.rdict)
