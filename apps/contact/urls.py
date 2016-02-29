#!/usr/bin/env python
# -*- coding:UTF-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns(
    'apps.contact.views',
    url(r'^type/edit/$', 'contact_type_edit'),
    url(r'^type/$', 'contact_type_list'),
    url(r'^edit/$', 'edit'),
    url('$', 'list'),
)
