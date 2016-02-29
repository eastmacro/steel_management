#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from django.conf.urls import patterns, include, url
from django.conf import settings
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
                       
    url(r'^$', 'apps.account.views.redirect'),
    # Account
    url(r'^account/login/$', 'apps.account.views.login'),
    url(r'^account/login/submit/$', 'apps.account.views.login'),

    url(
        r'^account/password/change/$',
        'django.contrib.auth.views.password_change',
        {
            'post_change_redirect': '/account/logout/'
        }
    ),
                       
    url(r'^supplier/', include('apps.supplier.urls')),
    url(r'^client/', include('apps.client.urls')),
    url(r'^steel/', include('apps.steel.urls')),
    url(r'^batch/', include('apps.batch.urls')),
    url(r'^retail/', include('apps.retail.urls')),
    url(r'^order/', include('apps.order.urls')),
    url(r'^contact/', include('apps.contact.urls')),
    url(r'^data/', include('apps.data.urls')),
    url(r'^home/', include('apps.home.urls')),
    url(r'^account/', include('apps.account.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^captcha/', include('captcha.urls')),
)
