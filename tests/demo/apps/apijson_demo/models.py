#coding=utf-8

from uliweb.orm import *

class Privacy(Model):
    user_id = Reference("user")
    certified = Field(bool)
    phone = Field(str)
    balance = Field(DECIMAL)
    password = Field(str)
    paypassword = Field(str)

class Moment(Model):
    user_id = Reference("user")
    date = Field(datetime.datetime, auto_now_add=True)
    content = Field(TEXT)
    picture_list = Field(JSON, default=[])

class Comment(Model):
    user_id = Reference("user")
    to_id = Reference("user")
    moment_id = Reference("moment")
    date = Field(datetime.datetime, auto_now_add=True)
    content = Field(TEXT)

class PublicNotice(Model):
    date = Field(datetime.datetime, auto_now_add=True)
    content = Field(TEXT)
