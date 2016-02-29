#!/usr/bin/env python
# -*- coding:UTF-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns(
    'apps.steel.views',

    url(r'^edit/$', 'edit'),
    url(r'^rule/edit/$', 'rule_edit'),
    url(r'^rule/$', 'rule_list'),
    url(r'^get/detail/$', 'get_detail_steel'),
    url(r'^get/$', 'get_steel'),
    url('$', 'list'),
)
