#!/usr/bin/env python
# -*- coding:UTF-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns(
    'apps.home.views',
    url('$', 'list'),
)
