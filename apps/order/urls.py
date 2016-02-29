#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns(
    'apps.order.views',
    # 进货相关
    url(r'^add/$', 'add'),
    url(r'^detail/edit/$', 'edit'),
    url(r'^edit/$', 'order_edit'),
    url(r'^load_data/$', 'load_data'),
    url('$', 'list'),
)