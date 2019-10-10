#coding=utf-8
from uliweb import expose, functions, models, UliwebError
from uliweb.orm import ModelNotFound
from uliweb.utils._compat import string_types
from sqlalchemy.sql import and_, or_, not_
from json import loads
from collections import OrderedDict
import logging
import traceback
from . import ApiJsonModelQuery

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
            #https://blog.csdn.net/yockie/article/details/44065885
            #keep order when parse json, because the order matters for association query
            self.request_data = loads(request.data, object_pairs_hook=OrderedDict)
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

    def _ref_get(self,path,context=None):
        if context==None:
            context = {}
        if path[0]=="/":
            #relative path
            c = context
            for i in path.split("/"):
                if i:
                    if isinstance(c,dict):
                        c = c.get(i)
                    elif isinstance(c,list):
                        try:
                            c = c[int(i)]
                        except Exception as e:
                            raise UliwebError("bad path item '%s' in path '%s', error: %s"%(i,path,e))
                    else:
                        raise UliwebError("cannot get '%s' from '%s'"%(i,c))
            return c
        else:
            #absolute path
            c = self.rdict
            for i in path.split("/"):
                if i:
                    if isinstance(c,dict):
                        c = c.get(i)
                    elif isinstance(c,list):
                        try:
                            c = c[int(i)]
                        except Exception as e:
                            raise UliwebError("bad path item '%s' in path '%s', error: %s"%(i,path,e))
                    else:
                        raise UliwebError("bad path item '%s' in path '%s'"%(i,path))
            return c

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
        except UliwebError as e:
            return json({"code":400,"msg":str(e)})
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
            if hasattr(request,"user"):
                params_role = "LOGIN"
            else:
                params_role = "UNKNOWN"
        elif params_role != "UNKNOWN":
            if not hasattr(request,"user"):
                return json({"code":400,"msg":"no login user for role '%s'"%(params_role)})
        if params_role not in roles:
            return json({"code":400,"msg":"'%s' not accessible by role '%s'"%(model_name,params_role)})
        if params_role == "UNKNOWN":
            permission_check_ok = True
        elif functions.has_role(request.user,params_role):
            permission_check_ok = True
        else:
            return json({"code":400,"msg":"user doesn't has role '%s'"%(params_role)})
        if not permission_check_ok:
            return json({"code":400,"msg":"no permission"})

        if params_role=="OWNER":
            owner_filtered,q = self._filter_owner(model,model_setting,q)
            if not owner_filtered:
                return  json({"code":400,"msg":"'%s' cannot filter with owner"%(model_name)})

        params = self.request_data[key]
        if isinstance(params,dict):
            #update reference,example: {"id@": "moment/user_id"} -> {"id": 2}
            ref_fields = []
            refs = {}
            for n in params:
                if n[-1]=="@":
                    ref_fields.append(n)
                    col_name = n[:-1]
                    path = params[n]
                    refs[col_name] = self._ref_get(path,context=self.rdict)
            for i in ref_fields:
                del params[i]
            params.update(refs)
            
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

        names = [n for n in params if n[0]!='@']
        if names:
            #main model
            n = names[0]
            mquery = ApiJsonModelQuery(n,params[n],self,key)
            mquery.query_array()
            #additional model
            for n in names[1:]:
                mquery = ApiJsonModelQuery(n,params[n],self,key)
                mquery.associated_query_array()

    def _filter_owner(self,model,model_setting,q):
        owner_filtered = False
        if hasattr(model,"owner_condition"):
            q = q.filter(model.owner_condition(request.user.id))
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
        if not isinstance(item,string_types):
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
