#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns(
    'apps.batch.views',
    # 进货相关
    url(r'^add/$', 'add'),
    url(r'^edit/(?P<id>\d+)/$', 'edit'),
    url(r'^change/(?P<id>\d+)/$', 'change'),
    url('$', 'list'),
)
