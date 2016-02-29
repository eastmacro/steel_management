#!/usr/bin/env python
# -*- coding: utf-8 -*-


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings


def list_by_page(request, retlist, page_len=settings.PAGELEN):
    paginator = Paginator(retlist, page_len)
    page = request.GET.get('page')
    ret = {}
    try:
        ret = paginator.page(page)
    except PageNotAnInteger:
        ret = paginator.page(1)
    except EmptyPage:
        ret = paginator.page(paginator.num_pages)

    return ret
