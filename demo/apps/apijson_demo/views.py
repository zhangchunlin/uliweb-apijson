#coding=utf-8
from uliweb import expose, functions
from json import dumps

@expose('/')
def index():
    if request.user:
        user_info = "login as user '%s(%s)'"%(request.user.username,request.user)
    else:
        user_info = "not login, you can login with username 'admin/usera/userb/userc', and password '123'"
    request_get = [
        {
            "label":"Single record query: with id as parameter",
            "value":'''{
   "user":{
     "id":1
   }
}''',
        },
        {
            "label":"Single record query: no parameter",
            "value":'''{
   "user":{
   }
}''',
        },
        {
            "label":"Single record query: @column",
            "value":'''{
   "user":{
     "@column": "id,username,email"
   }
}''',
        },
        {
            "label":"Array query: private data",
            "value":'''{
  "[]":{
    "@count":2,
    "@page":0,
    "user":{
      "@column":"id,username,nickname,email",
      "@order":"id-"
    }
  }
}''',
        },
    ]

    request_post = [
        {
            "label":"Add record",
            "value":'''{
    "Moment": {
        "content": "new moment for test",
        "pictureList": [
            "http://static.oschina.net/uploads/user/48/96331_50.jpg"
        ]
    },
    "tag": "Moment"
}''',
        },
    ]

    return {
        "user_info":user_info,
        "request_get_json":dumps(request_get),
        "request_post_json":dumps(request_post),
    }
