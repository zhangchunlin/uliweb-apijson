# Introduction

uliweb-apijson is a subset and slightly different variation of [apijson](https://github.com/TommyLemon/APIJSON/blob/master/Document.md)

# uliweb model configuration

## example

```
[APIJSON_MODELS]
user = {
    "user_id_field" : "id",
    "secret_fields" : ["password"],
    "rbac_get" : {
        "roles" : ["ADMIN","OWNER"]
    }
}
```

## document

settings.APIJSON_MODEL_CONFIG.[MODEL_NAME]

| Field         | Doc                                                        |
| ------------- | ---------------------------------------------------------- |
| user_id_field | Field name of user id, related to query user own data.     |
| secret_fields | Secret fields won't be exposed.                            |
| rbac_get      | Configure of roles or permissions for apijson 'get' method |

# Supported API Examples

Please run [demo](../../demo/README.md) project and try it.
