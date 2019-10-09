import os
from uliweb import manage
from uliweb.manage import make_simple_application
from json import loads as json_loads

os.chdir('demo')

manage.call('uliweb syncdb -v')
manage.call('uliweb reset -v -y')
manage.call('uliweb dbinit -v')

def pre_call_as(username):
    from uliweb import models
    User = models.user
    user = User.get(User.c.username==username)
    def pre_call(request):
        request.user = user
    return pre_call

def test_apijson_get():
    """
    >>> application = make_simple_application(project_dir='.')
    >>> handler = application.handler()

    >>> #bad json
    >>> data ='''{
    ... ,,,
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 400, 'msg': 'not json data in the request'}

    >>> #query self user
    >>> data ='''{
    ... "user":{
    ...         "@role":"OWNER"
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d.keys())
    dict_keys(['code', 'msg', 'user'])

    >>> #query with id
    >>> data ='''{
    ... "user":{
    ...         "@role":"ADMIN",
    ...         "id": 2
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 200, 'msg': 'success', 'user': {'username': 'usera', 'nickname': 'User A', 'email': 'usera@localhost', 'is_superuser': False, 'last_login': None, 'date_join': '2018-02-02 00:00:00', 'image': '', 'active': False, 'locked': False, 'deleted': False, 'auth_type': 'default', 'timezone': '', 'id': 2}}

    >>> #query with @column
    >>> data ='''{
    ... "user":{
    ...         "@role":"OWNER",
    ...         "@column": "id,username,email,nickname,is_superuser"
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 200, 'msg': 'success', 'user': {'username': 'admin', 'nickname': 'Administrator', 'email': 'admin@localhost', 'is_superuser': True, 'id': 1}}

    >>> #query one with a non existing model
    >>> data ='''{
    ... "nonexist":{
    ...         "id": 1
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 400, 'msg': "model 'nonexist' not found"}

    >>> #query one with a non expose model
    >>> data ='''{
    ... "role":{
    ...         "id": 1
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 400, 'msg': "'role' not accessible"}

    >>> #query one with UNKNOWN role (expected ok)
    >>> data ='''{
    ... "moment":{
    ...         "id": 1
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 200, 'msg': 'success', 'moment': {'user_id': 2, 'date': '2018-11-01 00:00:00', 'content': 'test moment', 'picture_list': '[]', 'id': 1}}

    >>> #query one with UNKNOWN role (expected fail)
    >>> data ='''{
    ... "privacy":{
    ...         "id": 1
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 400, 'msg': "'privacy' not accessible by role 'UNKNOWN'"}

    >>> #query one without user but use a non-UNKNOWN role
    >>> data ='''{
    ... "publicnotice":{
    ...         "@role":"OWNER",
    ...         "id": 1
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 400, 'msg': "no user for role 'OWNER'"}

    >>> #query one with OWNER but cannot filter with OWNER
    >>> data ='''{
    ... "publicnotice":{
    ...         "@role":"OWNER",
    ...         "id": 1
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 400, 'msg': "'publicnotice' cannot filter with owner"}

    >>> #query one with UNKNOWN
    >>> data ='''{
    ... "publicnotice":{
    ...         "id": 1
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 200, 'msg': 'success', 'publicnotice': {'date': '2018-12-09 00:00:00', 'content': 'notice: a', 'id': 1}}

    >>> #query array with a non expose model
    >>> data ='''{
    ... "[]":{
    ...         "role": {"@role":"ADMIN"}
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 400, 'msg': "'role' not accessible by apijson"}

    >>> #query array with a non existing model
    >>> data ='''{
    ... "[]":{
    ...         "nonexisting": {"@role":"ADMIN"}
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 400, 'msg': "model 'nonexisting' not found"}

    >>> #query array with a non existing role
    >>> data ='''{
    ... "[]":{
    ...         "user": {"@role":"NONEXISTING"}
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 400, 'msg': "'user' not accessible by role 'NONEXISTING'"}

    >>> #query array with a role user don't have
    >>> data ='''{
    ... "[]":{
    ...         "user": {"@role":"ADMIN"}
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("usera"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 400, 'msg': "user doesn't have role 'ADMIN'"}

    >>> #query array with no permission
    >>> data ='''{
    ... "[]":{
    ...         "user": {"@role":"superuser"}
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 400, 'msg': "'user' not accessible by role 'superuser'"}

    >>> #Association query: Two tables, one to one,ref path is absolute path
    >>> data ='''{
    ...     "moment":{},
    ...     "user":{
    ...     "@column": "id,username,email",
    ...     "id@": "moment/user_id"
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 200, 'msg': 'success', 'moment': {'user_id': 2, 'date': '2018-11-01 00:00:00', 'content': 'test moment', 'picture_list': '[]', 'id': 1}, 'user': {'username': 'usera', 'email': 'usera@localhost', 'id': 2}}

    >>> #Association query: Two tables, one to one,ref path is relative path
    >>> data ='''{
    ...     "moment":{},
    ...     "user":{
    ...     "@column": "id,username,email",
    ...     "id@": "/moment/user_id"
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 200, 'msg': 'success', 'moment': {'user_id': 2, 'date': '2018-11-01 00:00:00', 'content': 'test moment', 'picture_list': '[]', 'id': 1}, 'user': {'username': 'usera', 'email': 'usera@localhost', 'id': 2}}
    """
