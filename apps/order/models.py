#!/usr/bin/env python
# -*- coding:UTF-8 -*-

from django.db import models
from django.forms import ModelForm
from apps.supplier.models import Supplier

STATUS_CHOICES = (
    (0, '作废'),
    (1, '未用'),
    (2, '已用'),
)

IS_YOUPIAO_CHOICES = (
    (0, '无票'),
    (1, '有票'),

)


class OrderItem(models.Model):
    class Meta:
        db_table = 'order_item'
    
    id = models.AutoField(primary_key=True)
    oid = models.CharField(max_length=50)
    from_oid = models.CharField(max_length=200)  # store from batch/retail id
    sid = models.IntegerField()
    number = models.IntegerField()
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True
    )
    profit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    create_time = models.DateTimeField()
    modify_time = models.DateTimeField()
    order_day = models.DateField()
    status = models.IntegerField(default=1, choices=STATUS_CHOICES)

class OrderItemForm(ModelForm):
    class Meta:
        model = OrderItem


class Order(models.Model):
    class Meta:
        db_table = 'order'
    
    id = models.AutoField(primary_key=True)
    oid = models.CharField(unique=True, max_length=50)
    is_youpiao = models.IntegerField(default=0, choices=IS_YOUPIAO_CHOICES)
    client_id = models.IntegerField()
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True
    )
    profit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    create_time = models.DateTimeField()
    modify_time = models.DateTimeField()
    order_day = models.DateField()
    status = models.IntegerField(default=1, choices=STATUS_CHOICES)
    

class OrderForm(ModelForm):
    class Meta:
        model = Order
