#!/usr/bin/env python
#-*- coding: UTF-8 -*-

from django.db import models
from django.forms import ModelForm

STATUS_CHOICES = (
    (0, '无效'),
    (1, '有效'),
)


class ContactBook(models.Model):
    class Meta:
        db_table = 'contact_book'
    
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    contact = models.CharField(max_length=100, default='', blank=True)
    type = models.IntegerField(default=1)
    status = models.IntegerField(default=1, choices=STATUS_CHOICES)
    create_time = models.DateTimeField()
    modify_time = models.DateTimeField()
    remark = models.CharField(max_length=200, default='', blank=True)

class ContactBookForm(ModelForm):
    class Meta:
        model = ContactBook


class ContactType(models.Model):
    class Meta:
        db_table = 'contact_type'

    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=50, unique=True)


class ContactTypeForm(ModelForm):
    class Meta:
        model = ContactType
