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


class Retail(models.Model):
    class Meta:
        db_table = 'retail'
    
    id = models.AutoField(primary_key=True)
    oid = models.CharField(max_length=50, default='')
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
    status = models.IntegerField(default=1, choices=STATUS_CHOICES)
    create_time = create_time = models.DateTimeField()
    steel = None

    @property
    def get_steel(self):
        if not self.steel:
            self.steel = Steel.objects.get(id=sid)
        return self.steel


class RetailForm(ModelForm):
    class Meta:
        model = Retail


class RetailOrder(models.Model):
    class Meta:
        db_table = 'retail_order'

    id = models.AutoField(primary_key=True)
    oid = models.CharField(unique=True, max_length=50)
    supplier_id = models.IntegerField()
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True
    )

    create_time = models.DateTimeField()
    modify_time = models.DateTimeField()
    order_day = models.DateField()
    status = models.IntegerField(default=1, choices=STATUS_CHOICES)
    
    retails = None
    
    @property
    def get_retails(self):
        if not self.retails:
            self.retails = Retail.objects.filter(oid=self.oid)
        return self.retails


class RetailOrderForm(ModelForm):
    class Meta:
        model = RetailOrder