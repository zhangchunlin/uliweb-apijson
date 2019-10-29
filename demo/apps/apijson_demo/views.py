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
            "label":"Single query: self user",
            "value":'''{
   "user":{
        "@role":"OWNER"
   }
}''',
        },

        {
            "label":"Single query: with id as parameter",
            "value":'''{
   "user":{
        "id":2,
        "@role":"ADMIN"
   }
}''',
        },

        {
            "label":"Single query: @column",
            "value":'''{
    "user":{
       "@column": "id,username,email",
       "@role":"OWNER"
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
            "@order":"id-",
            "@role":"ADMIN"
        }
    }
}''',
        },

        {
            "label":"Array query: moment",
            "value":'''{
    "moment[]":{
        "@count":10,
        "@page":0,
        "@query":2,
        "moment":{
            "@order":"id-"
        }
    },
    "total@":"/moment[]/total"
}''',
        },

        {
            "label":"Array query: like",
            "value":'''{
  "[]":{
    "@count":4,
    "@page":0,
    "user":{
        "@column":"id,username,nickname,email",
        "@order":"id-",
        "@role":"ADMIN",
        "username$":"%user%"
    }
  }
}''',
        },

        {
            "label":"Array query: {} with list",
            "value":'''{
  "[]":{
    "moment":{
        "id{}":[2,3]
    }
  }
}''',
        },

        {
            "label":"Array query: {} with conditions",
            "value":'''{
  "[]":{
    "user":{
        "id&{}":">2,<=4"
    }
  }
}''',
        },

        {
            "label":"Array query: simple @expr",
            "value":'''{
  "[]":{
    "@count":4,
    "@page":0,
    "user":{
        "@column":"id,username,nickname,email",
        "@order":"id-",
        "@role":"ADMIN",
        "@expr":["username$","|","nickname$"],
        "username$":"%b%",
        "nickname$":"%c%"
    }
  }
}''',
        },

        {
            "label":"Array query: complex @expr",
            "value":'''{
  "[]":{
    "@count":4,
    "@page":0,
    "user":{
        "@column":"id,username,nickname,email",
        "@order":"id-",
        "@role":"ADMIN",
        "@expr":[["username$","&","email$"],"&",["!","nickname$"]],
        "username$":"%b%",
        "nickname$":"%Admin%",
        "email$":"%local%"
    }
  }
}''',
        },

        {
            "label":"Association query: Two tables, one to one",
            "value":'''{
    "moment":{},
    "user":{
       "@column": "id,username,email",
       "id@": "moment/user_id"
    }
}''',
        },

        {
            "label":"Association query: Two tables, one to many",
            "value":'''{
    "moment": {},
    "[]": {
        "comment": {
            "moment_id@": "moment/id",
            "@order":"date-"
        }
    }
}''',
        },

        {
            "label":"Association query: Two tables in array",
            "value":'''{
  "[]": {
    "moment": {
      "@column": "id,date,user_id"
    },
    "user": {
      "id@": "/moment/user_id",
      "@column": "id,username"
    }
  }
}''',
        },
    ]

    request_head = [
        {
            "label":"query number of moments for one user",
            "value":'''{
    "moment": {
        "user_id": 1
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
    "@tag": "comment"
}''',
        },
    ]

    request_put = [
        {
            "label":"Modify moment",
            "value":'''{
    "moment": {
        "id": 1,
        "content": "modify moment content"
    },
    "@tag": "moment"
}''',
        },
    ]

    request_delete = [
        {
            "label":"Delete moment",
            "value":'''{
    "moment": {
        "id": 1
    },
    "@tag": "moment"
}''',
        },
    ]
    return {
        "user_info":user_info,
        "request_get_json":dumps(request_get),
        "request_head_json":dumps(request_head),
        "request_post_json":dumps(request_post),
        "request_put_json":dumps(request_put),
        "request_delete_json":dumps(request_delete),
    }
