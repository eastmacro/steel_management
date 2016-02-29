#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 huozhiquan
#
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings


def list_by_page(request, retlist, pagelen=settings.PAGELEN, page=None):
    paginator = Paginator(retlist, pagelen)
    if not page:
        page = request.GET.get('page')
    ret = {}
    try:
        ret = paginator.page(page)
    except PageNotAnInteger:
        ret = paginator.page(1)
    except EmptyPage:
        ret = paginator.page(paginator.num_pages)

    return ret
