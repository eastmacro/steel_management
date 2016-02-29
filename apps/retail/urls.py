#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns(
    'apps.retail.views',
    # 进货相关
    url(r'^add/$', 'add'),
    url(r'^order/edit/$', 'order_edit'),
    url(r'^edit/$', 'edit'),
    url('$', 'list'),
)
