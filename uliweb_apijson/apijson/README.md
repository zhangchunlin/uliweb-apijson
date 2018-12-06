# Introduction

uliweb-apijson is a subset and slightly different variation of [apijson](https://github.com/TommyLemon/APIJSON/blob/master/Document.md)

# uliweb model configuration

## example

```
[APIJSON_MODEL_CONFIG]
user = {
    "public" : False,
    "user_id_field" : "id",
    "secret_fields" : ["password"],
    "default_filter_by_self" : True
}
```

## document

settings.APIJSON_MODEL_CONFIG.[MODEL_NAME]

| Field                  | Doc                                                          |
| ---------------------- | ------------------------------------------------------------ |
| public                 | Default to be "False".<br />If not public, should be **login user** and only can see **user own data**. |
| user_id_field          | Field name of user id, related to query user own data.       |
| secret_fields          | Secret fields won't be exposed.                              |
| default_filter_by_self | If True, when no filter parameter, will filter by self user id |

# Supported API Examples

### Single record query: with id as parameter

URL: apijson/get

Method: POST

Request:

```
{
   "user":{
     "id":1
   }
}
```

Response:

```
{
  "code": 200,
  "msg": "success",
  "user": {
    "username": "usera",
    "nickname": "User A",
    "email": "usera@localhost",
    "is_superuser": false,
    "last_login": null,
    "date_join": "2018-12-05 15:44:26",
    "image": "",
    "active": false,
    "locked": false,
    "deleted": false,
    "auth_type": "default",
    "id": 1
  }
}
```

### Single record query: no parameter

URL: apijson/get

Method: POST

Request:

```
{
   "user":{
   }
}
```

Response:

```
{
  "code": 200,
  "msg": "success",
  "user": {
    "username": "usera",
    "nickname": "User A",
    "email": "usera@localhost",
    "is_superuser": false,
    "last_login": null,
    "date_join": "2018-12-05 15:44:26",
    "image": "",
    "active": false,
    "locked": false,
    "deleted": false,
    "auth_type": "default",
    "id": 1
  }
}
```

### Single record query: @column

URL: apijson/get

Method: POST

Request:

```
{
   "user":{
     "@column": "id,username,email"
   }
}
```

Response:

```
{
  "code": 200,
  "msg": "success",
  "user": {
    "username": "usera",
    "email": "usera@localhost",
    "id": 1
  }
}
```

### Array query

URL: apijson/get

Method: POST

Request:

```
{
  "[]":{
    "@count":2,
    "@page":0,
    "user":{
      "@column":"id,username,nickname,email",
      "@order":"id-"
    }
  }
}
```

Response:

```
{
  "code": 200,
  "msg": "success",
  "[]": [
    {
      "username": "userc",
      "nickname": "User C",
      "email": "userc@localhost",
      "id": 3
    },
    {
      "username": "userb",
      "nickname": "User B",
      "email": "userb@localhost",
      "id": 2
    }
  ]
}
```

