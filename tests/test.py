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

    >>> #query with @column which have a non existing column name
    >>> data ='''{
    ... "user":{
    ...         "@role":"OWNER",
    ...         "@column": "id,username,email,nickname,is_superuser,nonexisting"
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 200, 'msg': 'success', 'user': {'username': 'admin', 'nickname': 'Administrator', 'email': 'admin@localhost', 'is_superuser': True, 'id': 1}}

    >>> #query with a non existing column property
    >>> data ='''{
    ... "user":{
    ...         "nonexisting": 1
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 400, 'msg': "'user' have no attribute 'nonexisting'"}

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
    {'code': 400, 'msg': "no login user for role 'OWNER'"}

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

    >>> #query one with OWNER which will use owner_condition() to filter
    >>> data ='''{
    ... "moment":{
    ...         "@role":"OWNER"
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("usera"), middlewares=[])
    Moment: owner_condition
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 200, 'msg': 'success', 'moment': {'user_id': 2, 'date': '2018-11-01 00:00:00', 'content': 'test moment', 'picture_list': '[]', 'id': 1}}

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

    >>> #query array
    >>> data ='''{
    ... "[]":{
    ...         "user": {"@role":"ADMIN"}
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 200, 'msg': 'success', '[]': [{'user': {'username': 'admin', 'nickname': 'Administrator', 'email': 'admin@localhost', 'is_superuser': True, 'last_login': None, 'date_join': '2018-11-01 00:00:00', 'image': '', 'active': False, 'locked': False, 'deleted': False, 'auth_type': 'default', 'timezone': '', 'id': 1}}, {'user': {'username': 'usera', 'nickname': 'User A', 'email': 'usera@localhost', 'is_superuser': False, 'last_login': None, 'date_join': '2018-02-02 00:00:00', 'image': '', 'active': False, 'locked': False, 'deleted': False, 'auth_type': 'default', 'timezone': '', 'id': 2}}, {'user': {'username': 'userb', 'nickname': 'User B', 'email': 'userb@localhost', 'is_superuser': False, 'last_login': None, 'date_join': '2018-03-03 00:00:00', 'image': '', 'active': False, 'locked': False, 'deleted': False, 'auth_type': 'default', 'timezone': '', 'id': 3}}, {'user': {'username': 'userc', 'nickname': 'User C', 'email': 'userc@localhost', 'is_superuser': False, 'last_login': None, 'date_join': '2018-04-04 00:00:00', 'image': '', 'active': False, 'locked': False, 'deleted': False, 'auth_type': 'default', 'timezone': '', 'id': 4}}]}

    >>> #query array
    >>> data ='''{
    ... "[]":{
    ...         "user": {
    ...             "@role":"ADMIN",
    ...             "@column":"id,username,nickname,email"
    ...         }
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 200, 'msg': 'success', '[]': [{'user': {'username': 'admin', 'nickname': 'Administrator', 'email': 'admin@localhost', 'id': 1}}, {'user': {'username': 'usera', 'nickname': 'User A', 'email': 'usera@localhost', 'id': 2}}, {'user': {'username': 'userb', 'nickname': 'User B', 'email': 'userb@localhost', 'id': 3}}, {'user': {'username': 'userc', 'nickname': 'User C', 'email': 'userc@localhost', 'id': 4}}]}

    >>> #query array with non existing role
    >>> data ='''{
    ... "[]":{
    ...         "user": {
    ...             "@role":"NONEXISTING",
    ...             "@column":"id,username,nickname,email"
    ...         }
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 400, 'msg': "'user' not accessible by role 'NONEXISTING'"}

    >>> #query array with UNKNOWN
    >>> data ='''{
    ... "[]":{
    ...         "user": {
    ...             "@column":"id,username,nickname,email"
    ...         }
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 400, 'msg': "'user' not accessible by role 'UNKNOWN'"}

    >>> #query array without login user
    >>> data ='''{
    ... "[]":{
    ...         "user": {
    ...             "@role":"ADMIN",
    ...             "@column":"id,username,nickname,email"
    ...         }
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 400, 'msg': "no login user for role 'ADMIN'"}

    >>> #query array with a role which the user doesn't really have
    >>> data ='''{
    ... "[]":{
    ...         "user": {
    ...             "@role":"ADMIN",
    ...             "@column":"id,username,nickname,email"
    ...         }
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("usera"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 400, 'msg': "user doesn't have role 'ADMIN'"}

    >>> #query array with @count
    >>> data ='''{
    ... "[]":{
    ...         "@count":3,
    ...         "user": {
    ...         }
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("usera"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 200, 'msg': 'success', '[]': [{'user': {'username': 'admin', 'nickname': 'Administrator', 'email': 'admin@localhost', 'is_superuser': True, 'last_login': None, 'date_join': '2018-11-01 00:00:00', 'image': '', 'active': False, 'locked': False, 'deleted': False, 'auth_type': 'default', 'timezone': '', 'id': 1}}, {'user': {'username': 'usera', 'nickname': 'User A', 'email': 'usera@localhost', 'is_superuser': False, 'last_login': None, 'date_join': '2018-02-02 00:00:00', 'image': '', 'active': False, 'locked': False, 'deleted': False, 'auth_type': 'default', 'timezone': '', 'id': 2}}, {'user': {'username': 'userb', 'nickname': 'User B', 'email': 'userb@localhost', 'is_superuser': False, 'last_login': None, 'date_join': '2018-03-03 00:00:00', 'image': '', 'active': False, 'locked': False, 'deleted': False, 'auth_type': 'default', 'timezone': '', 'id': 3}}]}

    >>> #query array ,@count is bad param
    >>> data ='''{
    ... "[]":{
    ...         "@count":"bad",
    ...         "user": {
    ...         }
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("usera"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 400, 'msg': "@count should be an int, but get 'bad'"}

    >>> #query array with @count and @page
    >>> data ='''{
    ... "[]":{
    ...         "@count":2,
    ...         "@page":1,
    ...         "user": {
    ...         }
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("usera"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 200, 'msg': 'success', '[]': [{'user': {'username': 'userb', 'nickname': 'User B', 'email': 'userb@localhost', 'is_superuser': False, 'last_login': None, 'date_join': '2018-03-03 00:00:00', 'image': '', 'active': False, 'locked': False, 'deleted': False, 'auth_type': 'default', 'timezone': '', 'id': 3}}, {'user': {'username': 'userc', 'nickname': 'User C', 'email': 'userc@localhost', 'is_superuser': False, 'last_login': None, 'date_join': '2018-04-04 00:00:00', 'image': '', 'active': False, 'locked': False, 'deleted': False, 'auth_type': 'default', 'timezone': '', 'id': 4}}]}

    >>> #query array with @count and @page, @page bad param
    >>> data ='''{
    ... "[]":{
    ...         "@count":2,
    ...         "@page":"bad",
    ...         "user": {
    ...         }
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("usera"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 400, 'msg': "@page should be an int, but get 'bad'"}

    >>> #query array with @count and @page, @page <0
    >>> data ='''{
    ... "[]":{
    ...         "@count":2,
    ...         "@page":-2,
    ...         "user": {
    ...         }
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("usera"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 400, 'msg': "page should >0, but get '-2'"}

    >>> #query array with @count/@page/@query, @query bad param
    >>> data ='''{
    ... "[]":{
    ...         "@count":2,
    ...         "@page":1,
    ...         "@query":3,
    ...         "user": {
    ...         }
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("usera"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 400, 'msg': "bad param 'query': 3"}

    >>> #query array with @count/@page/@query, @query = 0
    >>> data ='''{
    ... "[]":{
    ...         "@count":2,
    ...         "@page":1,
    ...         "@query":0,
    ...         "user": {
    ...         }
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("usera"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 200, 'msg': 'success', '[]': [{'user': {'username': 'userb', 'nickname': 'User B', 'email': 'userb@localhost', 'is_superuser': False, 'last_login': None, 'date_join': '2018-03-03 00:00:00', 'image': '', 'active': False, 'locked': False, 'deleted': False, 'auth_type': 'default', 'timezone': '', 'id': 3}}, {'user': {'username': 'userc', 'nickname': 'User C', 'email': 'userc@localhost', 'is_superuser': False, 'last_login': None, 'date_join': '2018-04-04 00:00:00', 'image': '', 'active': False, 'locked': False, 'deleted': False, 'auth_type': 'default', 'timezone': '', 'id': 4}}]}

    >>> #query array with OWNER but cannot filter with OWNER
    >>> data ='''{
    ...    "[]":{
    ...         "publicnotice": {
    ...             "@role":"OWNER"
    ...         }
    ...    }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 400, 'msg': "'publicnotice' cannot filter with owner"}

    >>> #query array with OWNER
    >>> data ='''{
    ...    "[]":{
    ...         "comment": {
    ...             "@role":"OWNER"
    ...         }
    ...    }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 200, 'msg': 'success', '[]': [{'comment': {'user_id': 1, 'to_id': 3, 'moment_id': 1, 'date': '2018-11-01 00:00:00', 'content': 'comment from admin', 'id': 1}}]}

    >>> #query array with OWNER, the model using owner_condition
    >>> data ='''{
    ...    "[]":{
    ...         "moment": {
    ...             "@role":"OWNER"
    ...         }
    ...    }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("usera"), middlewares=[])
    Moment: owner_condition
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 200, 'msg': 'success', '[]': [{'moment': {'user_id': 2, 'date': '2018-11-01 00:00:00', 'content': 'test moment', 'picture_list': '[]', 'id': 1}}]}

    >>> #query array with some filter column
    >>> data ='''{
    ...   "[]":{
    ...     "@count":4,
    ...     "@page":0,
    ...     "user":{
    ...             "@column":"id,username,nickname,email",
    ...             "@order":"id-",
    ...             "@role":"ADMIN",
    ...             "username":"admin"
    ...         }
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 200, 'msg': 'success', '[]': [{'user': {'username': 'admin', 'nickname': 'Administrator', 'email': 'admin@localhost', 'id': 1}}]}

    >>> #query array with reference, @query = 1
    >>> data ='''{
    ...     "[]":{
    ...         "@count":2,
    ...         "@page":0,
    ...         "@query":1,
    ...         "user":{
    ...             "@column":"id,username,nickname,email",
    ...             "@order":"id-",
    ...             "@role":"ADMIN"
    ...         }
    ...     },
    ...     "total@":"/[]/total"
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 200, 'msg': 'success', 'total': 4}

    >>> #query array with reference, @query = 2
    >>> data ='''{
    ...     "[]":{
    ...         "@count":2,
    ...         "@page":0,
    ...         "@query":2,
    ...         "user":{
    ...             "@column":"id,username,nickname,email",
    ...             "@order":"id-",
    ...             "@role":"ADMIN"
    ...         }
    ...     },
    ...     "total@":"/[]/total"
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 200, 'msg': 'success', '[]': [{'user': {'username': 'userc', 'nickname': 'User C', 'email': 'userc@localhost', 'id': 4}}, {'user': {'username': 'userb', 'nickname': 'User B', 'email': 'userb@localhost', 'id': 3}}], 'total': 4}

    >>> #query array with @order +
    >>> data ='''{
    ...     "[]":{
    ...         "@count":2,
    ...         "@page":0,
    ...         "@query":2,
    ...         "user":{
    ...             "@column":"id,username,nickname,email",
    ...             "@order":"id+",
    ...             "@role":"ADMIN"
    ...         }
    ...     },
    ...     "total@":"/[]/total"
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 200, 'msg': 'success', '[]': [{'user': {'username': 'admin', 'nickname': 'Administrator', 'email': 'admin@localhost', 'id': 1}}, {'user': {'username': 'usera', 'nickname': 'User A', 'email': 'usera@localhost', 'id': 2}}], 'total': 4}

    >>> #query array with @order having a non existing column
    >>> data ='''{
    ...     "[]":{
    ...         "@count":2,
    ...         "@page":0,
    ...         "@query":2,
    ...         "user":{
    ...             "@column":"id,username,nickname,email",
    ...             "@order":"nonexist+",
    ...             "@role":"ADMIN"
    ...         }
    ...     },
    ...     "total@":"/[]/total"
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 400, 'msg': "'user' doesn't have column 'nonexist'"}

    >>> #query array with @expr
    >>> data ='''{
    ...   "[]":{
    ...     "@count":4,
    ...     "@page":0,
    ...     "user":{
    ...             "@column":"id,username,nickname,email",
    ...             "@order":"id-",
    ...             "@role":"ADMIN",
    ...             "@expr":["username$","|","nickname$"],
    ...             "username$":"%b%",
    ...             "nickname$":"%c%"
    ...         }
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 200, 'msg': 'success', '[]': [{'user': {'username': 'userc', 'nickname': 'User C', 'email': 'userc@localhost', 'id': 4}}, {'user': {'username': 'userb', 'nickname': 'User B', 'email': 'userb@localhost', 'id': 3}}]}

    >>> #query array with @expr, bad param which is not list
    >>> data ='''{
    ...   "[]":{
    ...     "@count":4,
    ...     "@page":0,
    ...     "user":{
    ...             "@column":"id,username,nickname,email",
    ...             "@order":"id-",
    ...             "@role":"ADMIN",
    ...             "@expr":{},
    ...             "username$":"%b%",
    ...             "nickname$":"%c%"
    ...         }
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 400, 'msg': "only accept array in @expr, but get 'OrderedDict()'"}

    >>> #query array with @expr, bad param which is an empty list
    >>> data ='''{
    ...   "[]":{
    ...     "@count":4,
    ...     "@page":0,
    ...     "user":{
    ...             "@column":"id,username,nickname,email",
    ...             "@order":"id-",
    ...             "@role":"ADMIN",
    ...             "@expr":[],
    ...             "username$":"%b%",
    ...             "nickname$":"%c%"
    ...         }
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 400, 'msg': "only accept 2 or 3 items in @expr, but get '[]'"}

    >>> #query array with @expr, bad param which is >3 items list
    >>> data ='''{
    ...   "[]":{
    ...     "@count":4,
    ...     "@page":0,
    ...     "user":{
    ...             "@column":"id,username,nickname,email",
    ...             "@order":"id-",
    ...             "@role":"ADMIN",
    ...             "@expr":["username$","|","username$","|","nickname$"],
    ...             "username$":"%b%",
    ...             "nickname$":"%c%"
    ...         }
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 400, 'msg': "only accept 2 or 3 items in @expr, but get '['username$', '|', 'username$', '|', 'nickname$']'"}

    >>> #query array with @expr, bad param which have bad operator
    >>> data ='''{
    ...   "[]":{
    ...     "@count":4,
    ...     "@page":0,
    ...     "user":{
    ...             "@column":"id,username,nickname,email",
    ...             "@order":"id-",
    ...             "@role":"ADMIN",
    ...             "@expr":["username$","*","nickname$"],
    ...             "username$":"%b%",
    ...             "nickname$":"%c%"
    ...         }
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 400, 'msg': "unknown operator: '*'"}

    >>> #query array with @expr, bad expr: & only 1 parameter
    >>> data ='''{
    ...   "[]":{
    ...     "@count":4,
    ...     "@page":0,
    ...     "user":{
    ...             "@column":"id,username,nickname,email",
    ...             "@order":"id-",
    ...             "@role":"ADMIN",
    ...             "@expr":["&","nickname$"],
    ...             "username$":"%b%",
    ...             "nickname$":"%c%"
    ...         }
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 400, 'msg': "'&'(and) expression need 3 items, but get '['&', 'nickname$']'"}

    >>> #query array with @expr, bad expr: | only 1 parameter
    >>> data ='''{
    ...   "[]":{
    ...     "@count":4,
    ...     "@page":0,
    ...     "user":{
    ...             "@column":"id,username,nickname,email",
    ...             "@order":"id-",
    ...             "@role":"ADMIN",
    ...             "@expr":["|","nickname$"],
    ...             "username$":"%b%",
    ...             "nickname$":"%c%"
    ...         }
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 400, 'msg': "'|'(or) expression need 3 items, but get '['|', 'nickname$']'"}

    >>> #query array with @expr, bad expr: | only 1 parameter
    >>> data ='''{
    ...   "[]":{
    ...     "@count":4,
    ...     "@page":0,
    ...     "user":{
    ...             "@column":"id,username,nickname,email",
    ...             "@order":"id-",
    ...             "@role":"ADMIN",
    ...             "@expr":["username$","!","nickname$"],
    ...             "username$":"%b%",
    ...             "nickname$":"%c%"
    ...         }
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 400, 'msg': "'!'(not) expression need 2 items, but get '['username$', '!', 'nickname$']'"}

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

    >>> #Association query: Two tables, one is array, one is single, there is a abs reference to array
    >>> data ='''{
    ...     "moment[]":{"moment":{"@count":3}},
    ...     "user":{
    ...     "@column": "id,username,email",
    ...     "id@": "moment[]/1/moment/user_id"
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 200, 'msg': 'success', 'moment[]': [{'moment': {'user_id': 2, 'date': '2018-11-01 00:00:00', 'content': 'test moment', 'picture_list': '[]', 'id': 1}}, {'moment': {'user_id': 3, 'date': '2018-11-02 00:00:00', 'content': 'test moment from b', 'picture_list': '[]', 'id': 2}}, {'moment': {'user_id': 4, 'date': '2018-11-06 00:00:00', 'content': 'test moment from c', 'picture_list': '[]', 'id': 3}}], 'user': {'username': 'userb', 'email': 'userb@localhost', 'id': 3}}

    >>> #Association query: Two tables, one is array, one is single, there is a rel reference to array
    >>> data ='''{
    ...     "moment[]":{"moment":{"@count":3}},
    ...     "user":{
    ...     "@column": "id,username,email",
    ...     "id@": "/moment[]/1/moment/user_id"
    ...     }
    ... }'''
    >>> r = handler.post('/apijson/get', data=data, pre_call=pre_call_as("admin"), middlewares=[])
    >>> d = json_loads(r.data)
    >>> print(d)
    {'code': 200, 'msg': 'success', 'moment[]': [{'moment': {'user_id': 2, 'date': '2018-11-01 00:00:00', 'content': 'test moment', 'picture_list': '[]', 'id': 1}}, {'moment': {'user_id': 3, 'date': '2018-11-02 00:00:00', 'content': 'test moment from b', 'picture_list': '[]', 'id': 2}}, {'moment': {'user_id': 4, 'date': '2018-11-06 00:00:00', 'content': 'test moment from c', 'picture_list': '[]', 'id': 3}}], 'user': {'username': 'userb', 'email': 'userb@localhost', 'id': 3}}

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