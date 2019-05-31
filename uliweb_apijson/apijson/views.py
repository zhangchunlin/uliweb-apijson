#coding=utf-8
from uliweb import expose, functions, models, UliwebError
from uliweb.orm import ModelNotFound
from sqlalchemy.sql import and_, or_, not_
from json import loads
import logging
import traceback

log = logging.getLogger('apijson')

@expose('/apijson')
class ApiJson(object):
    def __begin__(self):
        self.rdict = {
            "code":200,
            "msg":"success"
        }
        self.vars = {}

        try:
            self.request_data = loads(request.data)
        except Exception as e:
            log.error("try to load json but get exception: '%s', request data: %s"%(e,request.data))
            return json({"code":400,"msg":"not json data in the request"})

    def _apply_vars(self):
        for key in self.request_data:
            if key[-1]=="@":
                k = self.request_data[key]
                v = self.vars.get(k)
                if v:
                    self.rdict[key[:-1]] = v

    def get(self):
        try:
            for key in self.request_data:
                if key[-1]=="@":
                    #vars need to be applied later
                    pass
                elif key[-2:]=="[]":
                    rsp = self._get_array(key)
                else:
                    rsp = self._get_one(key)
                if rsp: return rsp
            self._apply_vars()
        except Exception as e:
            err = "exception when handling 'apijson get': %s"%(e)
            log.error(err)
            traceback.print_exc()
            return json({"code":400,"msg":"get exception when handling 'apijson get',please check server side log"})
        return json(self.rdict)

    def _get_one(self,key):
        model_name = key
        params = self.request_data[key]
        params_role = params.get("@role")

        try:
            model = getattr(models,model_name)
            model_setting = settings.APIJSON_MODELS.get(model_name,{})
        except ModelNotFound as e:
            log.error("try to find model '%s' but not found: '%s'"%(model_name,e))
            return json({"code":400,"msg":"model '%s' not found"%(model_name)})
        model_column_set = None
        q = model.all()

        GET = model_setting.get("GET")
        if not GET:
            return json({"code":400,"msg":"'%s' not accessible"%(model_name)})

        roles = GET.get("roles")
        permission_check_ok = False
        if not params_role:
            if request.user:
                params_role = "LOGIN"
            else:
                params_role = "UNKNOWN"
        if params_role not in roles:
            return json({"code":400,"msg":"'%s' not accessible by role '%s'"%(model_name,params_role)})
        if params_role == "UNKNOWN":
            permission_check_ok = True
        elif functions.has_role(request.user,params_role):
            permission_check_ok = True
        else:
            return json({"code":400,"msg":"user doesn't have role '%s'"%(params_role)})
        if not permission_check_ok:
            return json({"code":400,"msg":"no permission"})

        if params_role=="OWNER":
            owner_filtered,q = self._filter_owner(model,model_setting,q)
            if not owner_filtered:
                return  json({"code":400,"msg":"'%s' cannot filter with owner"%(model_name)})

        params = self.request_data[key]
        if isinstance(params,dict):
            for n in params:
                if n[0]=="@":
                    if n=="@column":
                        model_column_set = set(params[n].split(","))
                elif hasattr(model,n):
                    q = q.filter(getattr(model.c,n)==params[n])
                else:
                    return json({"code":400,"msg":"'%s' have no attribute '%s'"%(model_name,n)})
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
        model_name = None
        model_param = None
        model_column_set = None

        query_count = params.get("@count")
        if query_count:
            try:
                query_count = int(query_count)
            except ValueError as e:
                log.error("bad param in '%s': '%s'"%(n,params))
                return json({"code":400,"msg":"@count should be an int, now '%s'"%(params[n])})

        query_page = params.get("@page")
        if query_page:
            #@page begin from 0
            try:
                query_page = int(query_page)
            except ValueError as e:
                log.error("bad param in '%s': '%s'"%(n,params))
                return json({"code":400,"msg":"@page should be an int, now '%s'"%(params[n])})
            if query_page<0:
                return json({"code":400,"msg":"page should >0, now is '%s'"%(query_page)})

        #https://github.com/TommyLemon/APIJSON/blob/master/Document.md#32-%E5%8A%9F%E8%83%BD%E7%AC%A6
        query_type = params.get("@query",0)
        if query_type not in [0,1,2]:
            return json({"code":400,"msg":"bad param 'query': %s"%(query_type)})

        for n in params:
            if n[0]!="@":
                # TODO: support join in the future, now only support 1 model
                model_name = n
                break

        if not model_name:
            return json({"code":400,"msg":"no model found in array query"})

        #model settings
        model_setting = settings.APIJSON_MODELS.get(model_name,{})
        secret_fields = model_setting.get("secret_fields")

        #model params
        #column
        model_param = params[n]
        model_column = model_param.get("@column")
        if model_column:
            model_column_set = set(model_column.split(","))
        try:
            model = getattr(models,model_name)
        except ModelNotFound as e:
            log.error("try to find model '%s' but not found: '%s'"%(model_name,e))
            return json({"code":400,"msg":"model '%s' not found"%(model_name)})
        #order
        model_order = model_param.get("@order")

        q = model.all()

        GET = model_setting.get("GET")
        if not GET:
            return json({"code":400,"msg":"'%s' not accessible by apijson"%(model_name)})

        roles = GET.get("roles")
        params_role = model_param.get("@role")
        permission_check_ok = False
        if not params_role:
            if request.user:
                params_role = "LOGIN"
            else:
                params_role = "UNKNOWN"
        if params_role not in roles:
            return json({"code":400,"msg":"'%s' not accessible by role '%s'"%(model_name,params_role)})
        if params_role == "UNKNOWN":
            permission_check_ok = True
        elif functions.has_role(request.user,params_role):
            permission_check_ok = True
        else:
            return json({"code":400,"msg":"user doesn't have role '%s'"%(params_role)})

        if not permission_check_ok:
            return json({"code":400,"msg":"no permission"})

        if params_role == "OWNER":
            owner_filtered,q = self._filter_owner(model,model_setting,q)
            if not owner_filtered:
                return  json({"code":400,"msg":"'%s' cannot filter with owner"%(model_name)})

        model_expr = model_param.get("@expr")

        if model_expr:
            c = self._expr(model,model_param,model_expr)
            q = q.filter(c)
        else:
            for n in model_param:
                if n[0]!="@":
                    c = self._get_filter_condition(model,model_param,n)
                    q = q.filter(c)

        if query_type in [1,2]:
            self.vars["/%s/total"%(key)] = q.count()

        if query_type in [0,2]:
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

    def _expr(self,model,model_param,model_expr):
        if not isinstance(model_expr,list):
            raise UliwebError("only accept array in @expr: '%s'"%(model_expr))
        num = len(model_expr)
        if (num<2 or num>3):
            raise UliwebError("only accept 2 or 3 items in @expr: '%s'"%(model_expr))
        op = model_expr[-2]
        if op=='&':
            if num!=3:
                raise UliwebError("'&'(and) expression need 3 items: '%s'"%(model_expr))
            c1 = self._get_filter_condition(model,model_param,model_expr[0],expr=True)
            c2 = self._get_filter_condition(model,model_param,model_expr[2],expr=True)
            return and_(c1,c2)
        elif op=='|':
            if num!=3:
                raise UliwebError("'|'(or) expression need 3 items: '%s'"%(model_expr))
            c1 = self._get_filter_condition(model,model_param,model_expr[0],expr=True)
            c2 = self._get_filter_condition(model,model_param,model_expr[2],expr=True)
            return or_(c1,c2)
        elif op=='!':
            if num!=2:
                raise UliwebError("'!'(not) expression need 2 items: '%s'"%(model_expr))
            return not_(self._get_filter_condition(model,model_param,model_expr[1],expr=True))
        else:
            raise UliwebError("unknown operator: '%s'"%(op))

    def _get_filter_condition(self,model,model_param,item,expr=False):
        if isinstance(item,list):
            if expr:
                return self._expr(model,model_param,model_expr=item)
            else:
                raise UliwebError("item can be array only in @expr: '%s'"%(item))
        if not isinstance(item,str):
            raise UliwebError("item should be array or string: '%s'"%(item))
        n = item
        if n[0]=="@":
            raise UliwebError("param key should not begin with @: '%s'"%(n))
        if n[-1]=="$":
            name = n[:-1]
            if hasattr(model,name):
                return getattr(model.c,name).like(model_param[n])
            else:
                raise UliwebError("'%s' does not have '%s'"%(model_name,name))
        elif n[-1]=="}" and n[-2]=="{":
            name = n[:-2]
            if hasattr(model,name):
                # TODO
                pass
            raise UliwebError("still not support '%s'"%(name))
        elif hasattr(model,n):
            return getattr(model.c,n)==model_param[n]
        else:
            raise UliwebError("not support item: '%s'"%(item))

    def head(self):
        try:
            for key in self.request_data:
                rsp = self._head(key)
                if rsp: return rsp
        except Exception as e:
            err = "exception when handling 'apijson head': %s"%(e)
            log.error(err)
            traceback.print_exc()
            return json({"code":400,"msg":err})

        return json(self.rdict)

    def _head(self,key):
        model_name = key
        params = self.request_data[key]
        params_role = params.get("@role")

        try:
            model = getattr(models,model_name)
            model_setting = settings.APIJSON_MODELS.get(model_name,{})
        except ModelNotFound as e:
            log.error("try to find model '%s' but not found: '%s'"%(model_name,e))
            return json({"code":400,"msg":"model '%s' not found"%(model_name)})

        q = model.all()

        HEAD = model_setting.get("HEAD")
        if not HEAD:
            return json({"code":400,"msg":"'%s' not accessible"%(model_name)})

        roles = HEAD.get("roles")
        permission_check_ok = False
        if not params_role:
            if request.user:
                params_role = "LOGIN"
            else:
                params_role = "UNKNOWN"
        if params_role not in roles:
            return json({"code":400,"msg":"'%s' not accessible by role '%s'"%(model_name,params_role)})
        if params_role == "UNKNOWN":
            permission_check_ok = True
        elif functions.has_role(request.user,params_role):
            permission_check_ok = True
        else:
            return json({"code":400,"msg":"user doesn't have role '%s'"%(params_role)})
        if not permission_check_ok:
            return json({"code":400,"msg":"no permission"})

        if params_role=="OWNER":
            owner_filtered,q = self._filter_owner(model,model_setting,q)
            if not owner_filtered:
                return  json({"code":400,"msg":"'%s' cannot filter with owner"%(model_name)})
        for n in params:
            if n[0]=="@":
                pass
            else:
                param = params[n]
                if not hasattr(model.c,n):
                    return  json({"code":400,"msg":"'%s' don't have field '%s'"%(model_name,n)})
                q = model.filter(getattr(model.c,n)==param)
        rdict = {
            "code":200,
            "msg":"success",
            "count":q.count(),
        }

        self.rdict[key] = rdict

    def post(self):
        try:
            tag = self.request_data.get("@tag")
            if not tag:
                return json({"code":400,"msg":"'tag' parameter is needed"})
            for key in self.request_data:
                if key[0]!="@":
                    rsp = self._post_one(key,tag)
                    if rsp:
                        return rsp
                    else:
                        #only accept one table
                        return json(self.rdict)
        except Exception as e:
            err = "exception when handling 'apijson post': %s"%(e)
            log.error(err)
            traceback.print_exc()
            return json({"code":400,"msg":err})

        return json(self.rdict)

    def _post_one(self,key,tag):
        APIJSON_REQUESTS = settings.APIJSON_REQUESTS or {}
        request_tag = APIJSON_REQUESTS.get(tag,{})
        model_name = request_tag.get("@model_name") or tag

        params = self.request_data[key]
        params_role = params.get("@role")

        try:
            model = getattr(models,model_name)
            model_setting = settings.APIJSON_MODELS.get(model_name,{})
            user_id_field = model_setting.get("user_id_field")
        except ModelNotFound as e:
            log.error("try to find model '%s' but not found: '%s'"%(model_name,e))
            return json({"code":400,"msg":"model '%s' not found"%(model_name)})

        if not request_tag:
            return json({"code":400,"msg":"tag '%s' not found"%(tag)})
        tag_POST =  request_tag.get("POST",{})
        if not tag_POST:
            return json({"code":400,"msg":"tag '%s' not support apijson_post"%(tag)})
        ADD = tag_POST.get("ADD")
        if ADD:
            ADD_role = ADD.get("@role")
            if ADD_role and not params_role:
                params_role = ADD_role

        permission_check_ok = False
        model_POST = model_setting.get("POST")
        if model_POST:
            roles = model_POST.get("roles")
            if params_role:
                if not params_role in roles:
                    return json({"code":400,"msg":"'%s' not accessible by role '%s'"%(model_name,params_role)})
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
                    elif role == "UNKNOWN":
                        permission_check_ok = True
                        break
                    else:
                        if functions.has_role(request.user,role):
                            permission_check_ok = True
                            break
        if not permission_check_ok:
            return json({"code":400,"msg":"no permission"})

        DISALLOW = tag_POST.get("DISALLOW")
        if DISALLOW:
            for field in DISALLOW:
                if field in params:
                    log.error("request '%s' disallow '%s'"%(tag,field))
                    return json({"code":400,"msg":"request '%s' disallow '%s'"%(tag,field)})

        NECESSARY = tag_POST.get("NECESSARY")
        if NECESSARY:
            for field in NECESSARY:
                if field not in params or params.get(field)==None:
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
        try:
            tag = self.request_data.get("@tag")
            if not tag:
                return json({"code":400,"msg":"'tag' parameter is needed"})
            for key in self.request_data:
                if key[0]!="@":
                    rsp = self._put_one(key,tag)
                    if rsp:
                        return rsp
                    else:
                        #only accept one table
                        return json(self.rdict)
        except Exception as e:
            err = "exception when handling 'apijson put': %s"%(e)
            log.error(err)
            traceback.print_exc()
            return json({"code":400,"msg":err})

        return json(self.rdict)

    def _put_one(self,key,tag):
        APIJSON_REQUESTS = settings.APIJSON_REQUESTS or {}
        request_tag = APIJSON_REQUESTS.get(tag,{})
        model_name = request_tag.get("@model_name") or tag

        params = self.request_data[key]
        params_role = params.get("@role")

        try:
            model = getattr(models,model_name)
            model_setting = settings.APIJSON_MODELS.get(model_name,{})
            user_id_field = model_setting.get("user_id_field")
        except ModelNotFound as e:
            log.error("try to find model '%s' but not found: '%s'"%(model_name,e))
            return json({"code":400,"msg":"model '%s' not found"%(model_name)})

        if not request_tag:
            return json({"code":400,"msg":"tag '%s' not found"%(tag)})
        tag_PUT = request_tag.get("PUT",{})
        ADD = tag_PUT.get("ADD")
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
        if not obj:
            return json({"code":400,"msg":"cannot find record id '%s'"%(id_)})

        permission_check_ok = False
        model_PUT = model_setting.get("PUT")
        if model_PUT:
            roles = model_PUT.get("roles")
            if params_role:
                if not params_role in roles:
                    return json({"code":400,"msg":"'%s' not accessible by role '%s'"%(model_name,params_role)})
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
                    elif role == "UNKNOWN":
                        permission_check_ok = True
                        break
                    else:
                        if functions.has_role(request.user,role):
                            permission_check_ok = True
                            break

        if not permission_check_ok:
            return json({"code":400,"msg":"no permission"})

        DISALLOW = tag_PUT.get("DISALLOW")
        if DISALLOW:
            for field in DISALLOW:
                if field in params:
                    log.error("request '%s' disallow '%s'"%(tag,field))
                    return json({"code":400,"msg":"request '%s' disallow '%s'"%(tag,field)})

        NECESSARY = tag_PUT.get("NECESSARY")
        if NECESSARY:
            for field in NECESSARY:
                if field not in params:
                    log.error("request '%s' have not necessary field '%s'"%(tag,field))
                    return json({"code":400,"msg":"request '%s' have not necessary field '%s'"%(tag,field)})
        kwargs = {}
        for k in params:
            if k=="id":
                continue
            elif hasattr(obj,k):
                kwargs[k] = params[k]
            else:
                return json({"code":400,"msg":"'%s' don't have field '%s'"%(model_name,k)})
        obj.update(**kwargs)
        ret = obj.save()
        obj_dict = {"id":id_}
        if ret:
            obj_dict["code"] = 200
            obj_dict["msg"] = "success"
            obj_dict["count"] = 1
        else:
            obj_dict["code"] = 400
            obj_dict["msg"] = "failed when updating, maybe no change"
            obj_dict["count"] = 0
            self.rdict["code"] = 400
            self.rdict["msg"] = "failed when updating, maybe no change"
        self.rdict[key] = obj_dict

    def delete(self):
        try:
            tag = self.request_data.get("@tag")
            if not tag:
                return json({"code":400,"msg":"'tag' parameter is needed"})
            for key in self.request_data:
                if key[0]!="@":
                    rsp = self._delete_one(key,tag)
                    if rsp:
                        return rsp
                    else:
                        #only accept one table
                        return json(self.rdict)
        except Exception as e:
            err = "exception when handling 'apijson delete': %s"%(e)
            log.error(err)
            traceback.print_exc()
            return json({"code":400,"msg":err})
        return json(self.rdict)

    def _delete_one(self,key,tag):
        APIJSON_REQUESTS = settings.APIJSON_REQUESTS or {}
        request_tag = APIJSON_REQUESTS.get(tag,{})
        model_name = request_tag.get("@model_name") or tag

        params = self.request_data[key]
        params_role = params.get("@role")

        try:
            model = getattr(models,model_name)
            model_setting = settings.APIJSON_MODELS.get(model_name,{})
            user_id_field = model_setting.get("user_id_field")
        except ModelNotFound as e:
            log.error("try to find model '%s' but not found: '%s'"%(model_name,e))
            return json({"code":400,"msg":"model '%s' not found"%(model_name)})

        if not request_tag:
            return json({"code":400,"msg":"tag '%s' not found"%(tag)})
        tag_DELETE =  request_tag.get("DELETE",{})
        ADD = tag_DELETE.get("ADD")
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
        if not obj:
            return json({"code":400,"msg":"cannot find record id '%s'"%(id_)})

        permission_check_ok = False
        DELETE = model_setting.get("DELETE")
        if DELETE:
            roles = DELETE.get("roles")
            if params_role:
                if not params_role in roles:
                    return json({"code":400,"msg":"'%s' not accessible by role '%s'"%(model_name,params_role)})
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
                    elif role == "UNKNOWN":
                        permission_check_ok = True
                        break
                    else:
                        if functions.has_role(request.user,role):
                            permission_check_ok = True
                            break

        if not permission_check_ok:
            return json({"code":400,"msg":"no permission"})

        try:
            obj.delete()
            ret = True
        except Exception as e:
            log.error("remove %s %s fail"%(model_name,id_))
            ret = False

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
