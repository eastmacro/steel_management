#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from apps.steel.models import Steel, SteelForm
from apps.steel.models import CostRule, CostRuleForm
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
        'steel/list.html',
        data,
        context_instance=RequestContext(request)
    )


@permission_required('steel.change_steel')
def edit(request):
    data = {}
    id = request.GET.get("id", None)
    steel = None
    if id:
        id = int(id)
        steel = get_object_or_404(Steel, id=id)
        data['id'] = id

    if request.method == 'POST':
        post = request.POST.copy()
        
        create_time = datetime.now()
        modify_time = create_time
        print create_time
        number = 0
        weight = 0.0
        cost_a = 0.0
        cost_b = 0.0
        sell_price_a = 0.0
        sell_price_b = 0.0
        retail_number = 0

        if steel:
            cost_a = steel.cost_a
            cost_b = steel.cost_b
            create_time = steel.create_time
            modify_time = datetime.now()
            number = steel.number
            weight = steel.weight
            sell_price_a = steel.sell_price_a
            sell_price_b = steel.sell_price_b
            retail_number = steel.retail_number
    
        post.update({
            'status': 1,
            'create_time': create_time,
            'modify_time': modify_time,
            'number': number,
            'weight': weight,
            'cost_a': cost_a,
            'cost_b': cost_b,
            'sell_price_a': sell_price_a,
            'sell_price_b': sell_price_b,
            'retail_number': retail_number,
        })

        form = SteelForm(post, instance=steel)
        data['form'] = form
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/steel/')
        else:
            print form.errors
            return render_to_response(
                'steel/edit.html',
                data,
                context_instance=RequestContext(request)
            )
    else:
        form = SteelForm(instance=steel)
        data['form'] = form
        return render_to_response(
            'steel/edit.html',
            data,
            context_instance=RequestContext(request)
        )


def get_steel(request):
    resp_dict = {
        'code': 0,
        'steel_list': None
    }
    steel_list = []
    steel_name = request.POST.get('steel_name', None)
    steels = Steel.objects.filter(name__contains=steel_name).filter(status=1).order_by('-create_time')
    if steels.exists():
        for steel in steels:
            steel_list.append({
                'id': int(steel.id),
                'name': steel.name,
            })
        resp_dict['code'] = 1
        resp_dict['steel_list'] = steel_list
    return HttpResponse(
        json.dumps(resp_dict),
        content_type='application/json'
    )


@permission_required('steel.change_steel')
def get_detail_steel(request):
    dresp_dict = {
        'code': 0,
        'steel_id': None,
        'steel_name': None,
        'high_str': 0,
        'len_str': 0,
        'wid_str': 0,
    }

    steel_name = request.POST.get('steel_name', None)
    steel_id = request.POST.get('steel_id', None)
    steel = None
    print steel_name
    if steel_name:
        steels = Steel.objects.filter(name__contains=steel_name).filter(status=1).order_by('-create_time')
        if steels.exists():
            steel = steels[0]
            print steel.len_str
            dresp_dict.update({
                "code": 1,
                "steel_id": steel.id,
                "steel_name": steel.name,
                "high_str": float(steel.high_str),
                "len_str": float(steel.len_str),
                "wid_str": float(steel.wid_str),
            })
    else:
        if steel_id:
            steels = Steel.objects.filter(id=steel_id).filter(status=1).order_by('-create_time')
            if steels.exists():
                steel = steels[0]
                print steel.len_str
                dresp_dict.update({
                    "code": 1,
                    "steel_id": steel.id,
                    "steel_name": steel.name,
                    "high_str": float(steel.high_str),
                    "len_str": float(steel.len_str),
                    "wid_str": float(steel.wid_str),
                })
    return HttpResponse(
        json.dumps(dresp_dict),
        content_type='application/json'
    )


@permission_required('steel.change_steel')
def rule_edit(request):
    data = {}
    id = request.GET.get("id", None)
    cost_rule = None
    if id:
        id = int(id)
        cost_rule = get_object_or_404(CostRule, id=id)
        data['id'] = id

    if request.method == 'POST':
        post = request.POST.copy()
        
        create_time = datetime.now()
        modify_time = create_time
        
        if cost_rule:
            create_time = cost_rule.create_time
            modify_time = datetime.now()
    
        post.update({
            'create_time': create_time,
            'modify_time': modify_time,
        })

        form = CostRuleForm(post, instance=cost_rule)
        data['form'] = form
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/steel/rule/')
        else:
            print form.errors
            return render_to_response(
                'steel/rule_edit.html',
                data,
                context_instance=RequestContext(request)
            )
    else:
        form = CostRuleForm(instance=cost_rule)
        data['form'] = form
        return render_to_response(
            'steel/rule_edit.html',
            data,
            context_instance=RequestContext(request)
        )


@permission_required('steel.change_steel')
def rule_list(request):
    """steel list"""
    data = {}
    cost_rules = CostRule.objects.all().order_by('-create_time')
    data['cost_rules'] = cost_rules
    
    count = cost_rules.count()
    rule_list = list_by_page(request, cost_rules)
    data['count'] = count
    data['rule_list'] = rule_list
    return render_to_response(
        'steel/rule_list.html',
        data,
        context_instance=RequestContext(request)
    )
