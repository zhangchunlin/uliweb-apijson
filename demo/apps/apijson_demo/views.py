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
            "label":"Single record query: no parameter",
            "value":'''{
   "user":{
   }
}''',
        },
        {
            "label":"Single record query: with id as parameter",
            "value":'''{
   "user":{
     "id":1
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
            "label":"Array query: user",
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
        {
            "label":"Array query: moment",
            "value":'''{
  "[]":{
    "@count":10,
    "@page":0,
    "moment":{
      "@order":"id-"
    }
  }
}''',
        },
    ]

    request_post = [
        {
            "label":"Add new moment",
            "value":'''{
    "moment": {
        "content": "new moment for test",
        "picture_list": [
            "http://static.oschina.net/uploads/user/48/96331_50.jpg"
        ]
    },
    "@tag": "moment"
}''',
        },
        {
            "label":"Add new comment",
            "value":'''{
    "comment": {
        "moment_id": 1,
        "content": "new test comment"
    },
    "tag": "comment"
}''',
        },
    ]

    return {
        "user_info":user_info,
        "request_get_json":dumps(request_get),
        "request_post_json":dumps(request_post),
    }
