#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from apps.steel.models import Steel, SteelForm
from datetime import datetime
from django.shortcuts import get_object_or_404
from apps.utils.page_helper import list_by_page
from django.http import HttpResponse
from django.contrib.auth.decorators import permission_required
import json
import sys

reload(sys)
sys.setdefaultencoding('utf-8')


@permission_required('steel.change_steel')
def list(request):
    """steel list"""
    data = {}
    steels = Steel.objects.all().order_by('-create_time')
    data['steels'] = steels
    id = request.GET.get('id', None)
    if id:
        id = int(id)
        data['id'] = id
        steels = steels.filter(id=id)
    
    name = request.GET.get('name', None)
    if name:
        data['name'] = name
        steels = steels.filter(name__contains=name)
    
    type = request.GET.get('type', None)
    if type:
        data['type'] = type
        steels = steels.filter(type__contains=type)
    
    high_str = request.GET.get('high_str', None)
    if  high_str:
        steels = steels.filter(high_str=high_str)
        data['high_str'] = high_str
    
    count = steels.count()
    steel_list = list_by_page(request, steels)
    data['count'] = count
    data['steel_list'] = steel_list
    return render_to_response(
        'home/list.html',
        data,
        context_instance=RequestContext(request)
    )