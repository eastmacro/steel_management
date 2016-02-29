#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from django.db import models
from django.forms import ModelForm

STATUS_CHOICES = (
    (0, '无效'),
    (1, '有效'),
)


class Steel(models.Model):
    class Meta:
        db_table = "steel"
    
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    type = models.CharField(max_length=50, default='')
    high_str = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    len_str = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    wid_str = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    number = models.IntegerField(default=0, blank=True)
    retail_number = models.IntegerField(default=0, blank=True)  # 散货数量
    weight = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0.0,
        blank=True
    )
    
    # 综合成本a，综合成本b
    cost_a = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        blank=True
    )
        
    cost_b = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        blank=True
    )
                                 
    sell_price_a = models.DecimalField(  # sell price a
        max_digits=10,
        decimal_places=2,
        default=0.0,
        blank=True
    )
                                 
    sell_price_b = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        blank=True
    )
    create_time = models.DateTimeField()
    modify_time = models.DateTimeField()
    status = models.IntegerField(default=1, choices=STATUS_CHOICES)

class SteelForm(ModelForm):
    class Meta:
        model = Steel


class CostRule(models.Model):
    class Meta:
        db_table = "cost_rule"
    
    id = models.AutoField(primary_key=True)
    rule = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    create_time = models.DateTimeField()
    modify_time = models.DateTimeField()


class CostRuleForm(ModelForm):
    class Meta:
        model = CostRule
