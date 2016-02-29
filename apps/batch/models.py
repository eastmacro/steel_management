#!/usr/bin/env python
# -*- coding:UTF-8 -*-

from django.db import models
from django.forms import ModelForm
from apps.supplier.models import Supplier

STATUS_CHOICES = (
    (0, '作废'),
    (1, '未用'),
    (2, '已用但没有用完'),
    (3, '已完全使用'),
)

class Batch(models.Model):
    class Meta:
        db_table = 'batch'

    id = models.AutoField(primary_key=True)
    oid = models.CharField(unique=True, max_length=50, default='')
    supplier_id = models.IntegerField()  # 进货商ID
    sid = models.IntegerField()  # steel id
    number = models.IntegerField(blank=True, default=0)
    weight = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0.0
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0
    )  # 每吨得单价

    cost_a = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        blank=True,
    )  # 有票成本
    
    cost_b = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        blank=True,
    )  # 无票成本
                                 
    true_high = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0.0,
        blank=True,
    )  # 围数
                                 
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        blank=True,
    )
    product_place = models.CharField(max_length=50, blank=True, default='')
    batch_date = models.DateField()
    create_time = models.DateTimeField()
    modify_time = models.DateTimeField()
    status = models.IntegerField(default=1, choices=STATUS_CHOICES)

class BatchForm(ModelForm):
    class Meta:
        model = Batch
