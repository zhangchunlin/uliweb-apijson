# Introduction

uliweb-apijson is a subset and slightly different variation of [apijson](https://github.com/TommyLemon/APIJSON/blob/master/Document.md)

# Difference with original apijson

| feature  | apijson(java) | uliweb-apijson | comment                                                      |
| -------- | ------------- | -------------- | ------------------------------------------------------------ |
| @combine | ✔️             | ✖️              | Example:  "@combine":"&key0,&key1,\|key2,key3"               |
| @expr    | ✖️             | ✔️              | Example:  "@expr":[["username$","&","email$"],"&",["!","nickname$"]] |



# apijson model configuration

## example

```
[APIJSON_MODELS]
user = {
    "user_id_field" : "id",
    "secret_fields" : ["password"],
    "GET" : { "roles" : ["ADMIN","OWNER"] },
    "HEAD" : { "roles" : ["ADMIN","OWNER"] },
    "POST" : { "roles" : ["ADMIN"] },
    "PUT" : { "roles" : ["ADMIN","OWNER"] },
    "DELETE" : { "roles" : ["ADMIN"] },
}
usergroup = {
    "GET" : { "roles" : ["ADMIN","LOGIN"] },
    "HEAD" : { "roles" : ["ADMIN"] },
    "POST" : { "roles" : ["ADMIN"] },
    "PUT" : { "roles" : ["ADMIN"] },
    "DELETE" : { "roles" : ["ADMIN"] },
}
```

## document

settings.APIJSON_MODELS.[MODEL_NAME]

| Field         | Doc                                                        |
| ------------- | ---------------------------------------------------------- |
| user_id_field | Field name of user id, related to query user own data.     |
| secret_fields | Secret fields won't be exposed.                            |
| GET/HEAD/POST/PUT/DELETE      | Configure of roles or permissions for apijson methods |

# apijson request configuration

## example

```
[APIJSON_REQUESTS]
moment = {
    "moment": {
        "POST" :{
            "ADD":{"@role": "OWNER"},
            "DISALLOW" : ["id"],
            "NECESSARY" : ["content"],
        },
        "PUT" :{
            "ADD":{"@role": "OWNER"},
            "NECESSARY" : ["id","content"],
            "DISALLOW" : ["email"],
        },
    }
}
```
## document

settings.APIJSON_REQUESTS.[TAG_NAME]

request types currently support: POST, PUT

request configuration currently support: ADD,DISALLOW,NECESSARY (still not fully support [all the configuration items](https://github.com/TommyLemon/APIJSON/wiki#%E5%AE%9E%E7%8E%B0%E5%8E%9F%E7%90%86))

# apijson table configuration

## example

```
[APIJSON_TABLES]
roles = {
    "@model_name" : "role",
    "editable" : "auto",
    "table_fields" : [
        {"title":"#","key":"id","width":80,"component":"id"},
        {"title":"Name","key":"name","component":"name_link"},
        {"title":"Description","key":"description"},
        {"title":"Is reserved","key":"reserve","component":"checkbox"},
    ],
    "viewedit_fields" : [
        {"title":"#","key":"id","editable":False},
        {"title":"Name","key":"name"},
        {"title":"Description","key":"description"},
        {"title":"Is reserved","key":"reserve","component":"checkbox"},
    ],
    "add_fields" : [
        {"title":"Name","key":"name"},
        {"title":"Description","key":"description"},
        {"title":"Is reserved","key":"reserve","component":"checkbox"},
    ],
}
```

## document

Provide 2 vue component about table:

|                         | apijson-table                                                | apijson-viewedit                                             |
| ----------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| uliweb template include | {{include "vue/inc_apijson_table.html"}}                     | {{include "vue/inc_apijson_viewedit.html"}}                  |
| example:                | ```<apijson-table model_name="permission" :config="tconfig" :custom_tcolumns_render_generator="custom_tcolumns_render_generator" ref="table"></apijson-table>``` | ```<apijson-viewedit model_name="permission" request_tag="{{=request_tag}}" :id="id_" :config="tconfig"></apijson-viewedit>``` |






# Supported API Examples

Please run [demo](../../demo/README.md) project and try it.
