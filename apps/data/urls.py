#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns(
    'apps.data.views',
    # 数据相关
    url(r'^day/$', 'day_sale'),
    url(r'^steel/$', 'steel_summary'),
)
