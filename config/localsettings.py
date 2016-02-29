#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 huozhiquan
#
#
SITE_ID = 1
DEBUG = True
TEMPLATE_DEBUG = DEBUG

MANAGERS = (
    ('Huo Zhiquan', 'chiquanhuo@gmail.com'),
    # ('Your Name', 'your_email@example.com'),
)

ADMIN_DATABASE = "default"
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'steel_management',                      # Or path to database file if using sqlite3.
        'USER': 'root',                      # Not used with sqlite3.
        'PASSWORD': '123123',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    },
}
