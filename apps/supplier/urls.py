#!/usr/bin/env python
# -*- coding:UTF-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns(
    'apps.supplier.views',
    url(r'^edit/$', 'edit'),
    url(r'^get/$', 'get_supplier'),
    url('$', 'list'),
)
