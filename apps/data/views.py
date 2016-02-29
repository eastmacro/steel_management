#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from django.contrib.auth.decorators import permission_required
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from apps.order.models import Order, OrderItem
from apps.steel.models import Steel
from apps.utils.page_helper import list_by_page
from django.utils import timezone
from datetime import datetime, date, timedelta
from apps.client.models import Client
from django.db.models import Max, Sum
from django.shortcuts import get_object_or_404
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

DATE_PATTERN = '%Y-%m-%d'


@permission_required('order.change_order')
def day_sale(request):
    data = {}
    orders = Order.objects.all().order_by('-order_day')
    
    today = date.today()
    first_day_in_month = date(today.year, today.month, 1)
    from_date = request.GET.get('from_date', None)
    if from_date:
        from_date = datetime.strptime(from_date, DATE_PATTERN).date()
    else:
        from_date = first_day_in_month

    orders = orders.filter(order_day__gte=from_date)
    data['from_date'] = from_date

    end_date = request.GET.get('end_date', None)
    if end_date:
        end_date = datetime.strptime(end_date, DATE_PATTERN).date()
    else:
        end_date = today
    orders = orders.filter(order_day__lte=end_date)
    data['end_date'] = end_date

    data['orders'] = orders

    temp_orders = orders.values('order_day').annotate(Sum('total_price'))
    cost_orders = orders.values('order_day').annotate(Sum('profit'))
    #print cost_orders
    order_dict = {}
    cost_dict = {}
    temp_date = from_date
    
    for item in temp_orders:
        order_dict[item['order_day']] = float(item['total_price__sum'])
    for item in cost_orders:
        cost_dict[item['order_day']] = float(item['profit__sum'])

    order_list = []
    day_list = []
    money_list = []
    cost_list = []
    while temp_date < end_date:
        day_list.append(temp_date)
        if temp_date in order_dict:
            temp_data = {}
            temp_data['date'] = temp_date
            temp_data['money'] = order_dict[temp_date]
            money_list.append(order_dict[temp_date])
            temp_data['cost'] = cost_dict[temp_date]
            cost_list.append(cost_dict[temp_date])
        else:
            temp_data = {}
            temp_data['date'] = temp_date
            temp_data['money'] = 0.0
            money_list.append(0.0)
            temp_data['cost'] = 0.0
            cost_list.append(0.0)

        order_list.append(temp_data)
        temp_date = temp_date + timedelta(days=1)
    temp_data = {}
    temp_data['date'] = end_date
    day_list.append(end_date)
    #print day_list
    data['date_list'] = day_list
    if end_date in order_dict:
        temp_data['money'] = order_dict[temp_date]
        money_list.append(order_dict[temp_date])
        temp_data['cost'] = order_dict[temp_date]
        cost_list.append(cost_dict[temp_date])
    else:
        temp_data['money'] = 0.0
        temp_data['cost'] = 0.0
        money_list.append(0.0)
        cost_list.append(0.0)

    order_list.append(temp_data)
    order_list = list_by_page(request, order_list)
    data['order_list'] = order_list
    data['money_list'] = money_list
    data['cost_list'] = cost_list

    return render_to_response(
        'data/day_sale.html',
        data,
        context_instance=RequestContext(request)
    )


@permission_required('steel.change_steel')
def steel_summary(request):
    data = {}
    orders = Order.objects.all().order_by('-order_day')
    steels = Steel.objects.all().order_by('-create_time')
    data['steels'] = steels
    sid_dict = {}
    for item in steels:
        sid_dict[item.id] = item
    
    today = date.today()
    first_day_in_month = date(today.year, today.month, 1)
    from_date = request.GET.get('from_date', None)
    if from_date:
        from_date = datetime.strptime(from_date, DATE_PATTERN).date()
    else:
        from_date = first_day_in_month
    
    orders = orders.filter(order_day__gte=from_date)
    data['from_date'] = from_date

    end_date = request.GET.get('end_date', None)
    if end_date:
        end_date = datetime.strptime(end_date, DATE_PATTERN).date()
    else:
        end_date = today
    orders = orders.filter(order_day__lte=end_date)
    data['end_date'] = end_date

    date_list = []
    temp_date = from_date
    while temp_date < end_date:
        date_list.append(temp_date)
        temp_date = temp_date + timedelta(days=1)
    date_list.append(end_date)
    data['date_list'] = date_list

    oid_list = []
    for item in orders:
        oid_list.append(item.oid)

    order_items = OrderItem.objects.filter(oid__in=oid_list)

    sid = request.GET.get('sid', None)
    if sid:
        sid = int(sid)
        order_items = order_items.filter(sid=sid)
        oid_list = []
        if order_items.exists():
            for item in order_items:
                oid_list.append(item.oid)
        orders = orders.filter(oid__in=oid_list)
        data['sid'] = sid

    orders = list_by_page(request, orders)

    if sid:
        steel = get_object_or_404(Steel, id=sid)
        data['chart_name'] = steel.name
        chart_order_items = OrderItem.objects.filter(sid=sid).filter(create_time__lte=end_date).filter(create_time__gte=from_date)
        chart_order_item_list = chart_order_items.values('order_day', 'sid').annotate(Sum('number')).order_by('order_day')
        temp_date = from_date
        chart_data_list = []
        chart_data_dict = {}
        temp_date = from_date
        for item in chart_order_item_list:
            chart_data_dict[item['order_day']] = item
        temp_date = from_date
        while temp_date < end_date:
            if temp_date in chart_data_dict:
                chart_data_list.append(chart_data_dict[temp_date]['number__sum'])
            else:
                chart_data_list.append(0.0)
            temp_date = temp_date + timedelta(days=1)
        if end_date in chart_data_dict:
            chart_data_list.append(chart_data_dict[end_date]['number__sum'])
        else:
            chart_data_list.append(0.0)
        data['chart_data_list'] = chart_data_list

    data['orders'] = orders
    
    order_item_list = order_items.values('order_day', 'sid').annotate(Sum('number')).order_by('-order_day')
    #print order_item_list
    item_list = []
    for item in order_item_list:
        if item['sid'] in sid_dict:
            item_list.append({
                'steel': sid_dict[item['sid']],
                'data': item,
            })

    data['item_list'] = item_list

    return render_to_response(
        'data/steel_summary.html',
        data,
        context_instance=RequestContext(request)
    )

