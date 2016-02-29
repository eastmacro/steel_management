#!/usr/bin/env python
#-*- coding: UTF-8 -*-

from django.db import models
from django.forms import ModelForm

STATUS_CHOICES = (
    (0, '无效'),
    (1, '有效'),
)


class Supplier(models.Model):
    class Meta:
        db_table = 'supplier'
    
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    contact = models.CharField(max_length=100, default='', blank=True)
    status = models.IntegerField(default=1, choices=STATUS_CHOICES)
    create_time = models.DateTimeField()
    modify_time = models.DateTimeField()


class SupplierForm(ModelForm):
    class Meta:
        model = Supplier
