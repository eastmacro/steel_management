#!/usr/bin/env python
#-*- coding: UTF-8 -*-

from django.db import models
from django import forms
from captcha.fields import CaptchaField
from django.contrib.auth.forms import AuthenticationForm

ACCOUNT_STATUS_LABEL = {
    0: '正常',
    1: '封号',
}

ACCOUNT_STATUS_CHOICES = (
    (0, ACCOUNT_STATUS_LABEL[0]),
    (1, ACCOUNT_STATUS_LABEL[1]),
)


class AdminUserInfo(models.Model):
    """后台用户信息类"""
    class Meta:
        db_table = 'admin_user_info'
        permissions = (
            ("login_admin", "允许登陆钢铁管理后台"),
        )
    
    connection_name = 'admin'
    
    id = models.AutoField(primary_key=True)
    auid = models.IntegerField()  # 后台用户id
    department = models.IntegerField(default=0)
    qq = models.CharField(max_length=30, blank=True)
    mobile = models.CharField(max_length=20, blank=True)
    birth = models.DateField(blank=True)
    address = models.CharField(max_length=300, blank=True)
    remark = models.CharField(max_length=300, blank=True)
    job_title = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )


class CaptchaUserAuthenticationForm(AuthenticationForm):
    captcha = CaptchaField()
