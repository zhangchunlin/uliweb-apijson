#coding=utf-8
from uliweb import expose, functions
from json import dumps

@expose('/')
def index():
    request_data_list = [
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
            "label":"Array query",
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
    return {
        "request_data_list_json":dumps(request_data_list)
    }
