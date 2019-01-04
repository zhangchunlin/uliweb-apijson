# Introduction

uliweb-apijson is a subset and slightly different variation of [apijson](https://github.com/TommyLemon/APIJSON/blob/master/Document.md)

# apijson model configuration

## example

```
[APIJSON_MODELS]
user = {
    "user_id_field" : "id",
    "secret_fields" : ["password"],
    "GET" : { "roles" : ["ADMIN","OWNER"] },
    "HEAD" : { "roles" : ["ADMIN","OWNER"] },
    "POST" : { "roles" : ["ADMIN","OWNER"] },
    "PUT" : { "roles" : ["ADMIN","OWNER"] },
    "DELETE" : { "roles" : ["ADMIN","OWNER"] },
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
        },
    }
}
```
## document

settings.APIJSON_REQUESTS.[TAG_NAME]

request types currently support: POST, PUT

request configuration currently support: ADD,DISALLOW,NECESSARY (still not fully support [all the configuration items](https://github.com/TommyLemon/APIJSON/wiki#%E5%AE%9E%E7%8E%B0%E5%8E%9F%E7%90%86))


# Supported API Examples

Please run [demo](../../demo/README.md) project and try it.
