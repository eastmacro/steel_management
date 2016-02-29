#!/usr/bin/env python
# -*- coding: utf-8 -*-
#


from django.conf.urls import patterns, url

urlpatterns = patterns(
    'apps.account.views',
                       
    url(r'^login/$', 'login'),
    url(r'^logout/$', 'logout'),
)

