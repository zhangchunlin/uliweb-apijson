#coding=utf-8
from uliweb import models
from uliweb.orm import set_dispatch_send

set_dispatch_send(False)

User = models.user
Privacy = models.privacy
Comment = models.comment
Moment = models.moment

user_list = [
    {
        "username": "admin",
        "nickname": "Administrator",
        "email": "admin@localhost",
    },
    {
        "username": "usera",
        "nickname": "User A",
        "email": "usera@localhost",
    },
    {
        "username": "userb",
        "nickname": "User B",
        "email": "userb@localhost",
    },
    {
        "username": "userc",
        "nickname": "User C",
        "email": "userc@localhost",
    },
]

privacy_list = [
    {
        "username" : "usera",
        "certified" : True,
        "phone" : "13333333333",
        "balance" : 100,
        "password" : "hash_of_123",
        "paypassword" : "hash_of_sudfy8e7r",
    },
    {
        "username" : "userb",
        "certified" : True,
        "phone" : "12222222222",
        "balance" : 130,
        "password" : "hash_of_dfdfd",
        "paypassword" : "hash_of_234erere",
    },
    {
        "username" : "userc",
        "certified" : True,
        "phone" : "14323424234",
        "balance" : 600,
        "password" : "hash_of_w3erere",
        "paypassword" : "hash_of_ghtwertr",
    },
]

moment_list = [
    {
        "username" : "usera",
        "date" : "2018-11-1",
        "content" : "test moment",
    },
    {
        "username" : "userb",
        "date" : "2018-11-2",
        "content" : "test moment from b",
    },
    {
        "username" : "userc",
        "date" : "2018-11-6",
        "content" : "test moment from c",
    },
    {
        "username" : "admin",
        "date" : "2018-11-7",
        "content" : "test moment from admin",
    },
]

comment_list = [
    {
        "username" : "usera",
        "to_username" : "userb",
        "moment_id" : 1,
        "date" : "2018-12-1",
        "content" : "comment haha",
    },
    {
        "username" : "userb",
        "to_username" : "usera",
        "moment_id" : 2,
        "date" : "2018-12-2",
        "content" : "comment xixi",
    },
    {
        "username" : "userc",
        "to_username" : "usera",
        "moment_id" : 3,
        "date" : "2018-12-9",
        "content" : "comment hoho",
    },
    {
        "username" : "admin",
        "to_username" : "usera",
        "moment_id" : 4,
        "date" : "2018-12-10",
        "content" : "comment kaka",
    },
]

for d in user_list:
    if not User.get(User.c.username==d["username"]):
        print("create user '%s'"%(d["username"]))
        u = User(**d)
        u.set_password("123")
        if d["username"]=="admin":
            u.is_superuser = True
        u.save()

for d in privacy_list:
    user = User.get(User.c.username==d["username"])
    if user:
        d["user_id"] = user.id
        print("create privacy record for user '%s'"%(d["username"]))
        Privacy(**d).save()
    else:
        print("error: unknown user '%s'"%(d["username"]))

for d in moment_list:
    user = User.get(User.c.username==d["username"])
    if user:
        d["user_id"] = user.id
        print("create moment record for user '%s'"%(d["username"]))
        Moment(**d).save()
    else:
        print("error: unknown user '%s'"%(d["username"]))


for d in comment_list:
    user = User.get(User.c.username==d["username"])
    if user:
        d["user_id"] = user.id
        d["to_id"] = User.get(User.c.username==d["to_username"]).id
        print("create comment record for user '%s'"%(d["username"]))
        Comment(**d).save()
    else:
        print("error: unknown user '%s'"%(d["username"]))
