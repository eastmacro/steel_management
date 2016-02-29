#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from django.contrib.auth.decorators import permission_required
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from apps.order.models import Order, OrderForm, OrderItem, OrderItemForm
from apps.steel.models import Steel
from apps.utils.page_helper import list_by_page
from django.utils import timezone
from datetime import datetime, date, timedelta
from apps.client.models import Client
from django.shortcuts import get_object_or_404
from utils.api.base import dump_response
from apps.retail.models import Retail
from apps.batch.models import Batch
import xlwt
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

DATE_PATTERN = '%Y-%m-%d'

@permission_required('order.change_order')
def list(request):
    data = {}
    
    steels = Steel.objects.all()
    steel_dict = {}
    for item in steels:
        steel_dict[item.id] = item
    
    data['steels'] = steels

    orders = Order.objects.all().order_by('-create_time')
    data['orders'] = orders

    clients = Client.objects.all()
    data['clients'] = clients
    client_dict = {}
    for item in clients:
        client_dict[item.id] = item

    id = request.GET.get('id', None)
    if id:
        id = int(id)
        data['id'] = id

    from_date = request.GET.get('from_date', None)
    if from_date:
        from_date = datetime.strptime(from_date, DATE_PATTERN).date()
        orders = orders.filter(order_day__gte=from_date)
        data['from_date'] = from_date

    end_date = request.GET.get('end_date', None)
    if end_date:
        end_date = datetime.strptime(end_date, DATE_PATTERN).date()
        orders = orders.filter(order_day__lte=end_date)
        data['end_date'] = end_date

    oid = request.GET.get('oid', None)
    if oid:
        orders = orders.filter(oid=oid)
        data['oid'] = oid

    sid = request.GET.get('sid', None)
    if sid:
        sid = int(sid)
        order_items = OrderItem.objects.filter(sid=sid)
        order_id_list = []
        for item in order_items:
            order_id_list.append(item.oid)
        orders = orders.filter(oid__in=order_id_list)
        data['sid'] = sid

    client_id = request.GET.get('client_id', None)
    if client_id:
        client_id = int(client_id)
        orders = orders.filter(client_id=client_id)
        data['client_id'] = client_id

    client_name = request.GET.get('client_name', None)
    if client_name:
        temp_clients = clients.filter(name__contains=client_name)
        temp_client_list = []
        if temp_clients.exists():
            for item in temp_clients:
                temp_client_list.append(item.id)

        orders = orders.filter(client_id__in=temp_client_list)
        data['client_name'] = client_name
    
    export = request.GET.get('export', False)
    if export == 'true':
        year_month = ''
        last_month_first_day = None
        last_month_last_day = None
        if not from_date:
            today = datetime.today()
            if today.month == 1:
                last_month_first_day = date(today.year-1, 12, 1)
            else:
                last_month_first_day = date(today.year, today.month-1, 1)
            export_orders = orders.filter(order_day__gte=last_month_first_day)
            year_month += last_month_first_day.strftime('%Y%m%d') + '_'
            
            if not end_date:
                last_month_last_day = date(datetime.today().year, datetime.today().month, 1) - timedelta(days=1)
                export_orders = orders.filter(order_day__lte=last_month_last_day)
                year_month += last_month_last_day.strftime('%Y%m%d')
            else:
                year_month += end_date.strftime('%Y%m%d')
        else:
            if end_date:
                year_month += from_date.strftime('%Y%m%d') + '_'
                year_month += end_date.strftime('%Y%m%d')
                export_orders = orders
            else:
                year_month += from_date.strftime('%Y%m%d') + '_'
                export_orders = orders.filter(order_day__lte=datetime.today())
                year_month += datetime.today().strftime('%Y%m%d')
            #print last_month_last_day
        return order_export(request, export_orders, steel_dict, client_dict, year_month)
    
    order_list = list_by_page(request, orders)
    oid_list = []
    for item in order_list:
        oid_list.append(item.oid)

    order_items = OrderItem.objects.filter(oid__in=oid_list)

    order_detail_list = []
    for item in order_list:
        temp_dict = {}
        check_time = item.create_time + timedelta(minutes=5)
        if check_time < datetime.now():
            temp_dict['check_time'] = 0
        else:
            temp_dict['check_time'] = 1
        temp_order_items = order_items.filter(oid=item.oid)
        order_item_list = []
        if temp_order_items.exists():
            for term in temp_order_items:
                order_item_dict = {}
                order_item_dict['order_item'] = term
                
                if term.sid in steel_dict:
                    order_item_dict['steel'] = steel_dict[term.sid]
                
                order_item_dict['income'] = float(term.total_price) - float(term.profit)
                temp_from_oid_arr = []
                temp_from_oid_list = term.from_oid.split(',')
                temp_from_oid_list.pop()
                for oid_term in temp_from_oid_list:
                    term_oid = oid_term.split('|')[0]
                    check_batch_or_retail = term_oid.split('_')[1]
                    term_num = oid_term.split('|')[1]
                    term_arr = [term_oid, term_num, int(check_batch_or_retail)]
                    temp_from_oid_arr.append(term_arr)
                order_item_dict['from_oid'] = temp_from_oid_arr
                order_item_list.append(order_item_dict)

        temp_dict['detail'] = order_item_list
        if item.client_id in client_dict:
            temp_dict['client'] = client_dict[item.client_id]

        temp_dict['order'] = item
        temp_dict['profit'] = float(item.total_price) - float(item.profit)
        order_detail_list.append(temp_dict)
    
    data['order_list'] = order_list
    data['order_detail_list'] = order_detail_list

    return render_to_response(
        'order/list.html',
        data,
        context_instance=RequestContext(request)
    )


@permission_required('order.change_order')
def add(request):
    data = {}
    order = None
    num = [0, 1, 2, 3, 4]
    data['num'] = num
    steels = Steel.objects.all()
    data['steels'] = steels
    clients = Client.objects.all()
    data['clients'] = clients
    order_day = date.today()
    data['order_day'] = order_day
    oid = datetime.now().strftime('%Y%m%d%H%M%S')
    data['oid'] = str(oid) + '_3'
    today = date.today()
    if request.method == 'POST':
        post = request.POST.copy()
        is_youpiao = post.get('is_youpiao', 0)  # check if not youpiao=1, wupiao=0
        if is_youpiao:
            is_youpiao = int(is_youpiao)
        client_id = post.get('client_id', None)

        i = 0
        oid = post.get('oid', None)
        if oid:
            pass
        else:
            return False

        order_item_list = []
        order_total_price = 0.0
        if not client_id:
            form = OrderForm(instance=order)
            data['form'] = form
            return render_to_response(
                'order/add.html',
                data,
                context_instance=RequestContext(request)
            )
        create_time = datetime.now()
        modify_time = create_time
        total_profit = 0.0  # order total profit

        while i < 5:
            temp_order_item = OrderItem()
            sid = 'sid_' + str(i)
            unit_price = 'unit_price_' + str(i)
            number = 'number_' + str(i)
            total_price = 'total_price_' + str(i)
            temp_sid = post.get(sid, None)

            if not temp_sid:
                break

            temp_number = post.get(number, None)

            if temp_number:
                temp_number = int(temp_number)
            else:
                form = OrderForm(instance=order)
                data['form'] = form
                return render_to_response(
                    'order/add.html',
                    data,
                    context_instance=RequestContext(request)
                )

            temp_unit_price = post.get(unit_price, None)
            #print temp_unit_price
            if temp_unit_price:
                temp_unit_price = float(temp_unit_price)
            else:
                form = OrderForm(instance=order)
                data['form'] = form
                return render_to_response(
                    'order/add.html',
                    data,
                    context_instance=RequestContext(request)
                )

            temp_total_price = post.get(total_price, None)
            if temp_total_price:
                temp_total_price = float(temp_total_price)
            else:
                form = OrderForm(instance=order)
                data['form'] = form
                return render_to_response(
                    'order/add.html',
                    data,
                    context_instance=RequestContext(request)
                )

            temp_steel = None
            if temp_sid:
                #print temp_sid
                temp_steels = steels.filter(id=int(temp_sid))
                if temp_steels.exists():
                    temp_steel = temp_steels[0]
                    storage_number = int(temp_steel.number) + int(temp_steel.retail_number)
                    if storage_number < int(temp_number):
                        form = OrderForm(instance=order)
                        data['form'] = form
                        return render_to_response(
                            'order/add.html',
                            data,
                            context_instance=RequestContext(request)
                        )
                else:
                    form = OrderForm(instance=order)
                    data['form'] = form
                    return render_to_response(
                        'order/add.html',
                        data,
                        context_instance=RequestContext(request)
                    )
            else:
                break

            temp_profit = 0.0  # each order item profit
            # 获取来源订单号
            temp_from_oid = ''
            need_number = int(temp_number)  # 需要的数量
            if temp_steel.retail_number > 0:
                inexhausted_retails = Retail.objects.filter(sid=temp_sid).filter(status=2).order_by('id')
                if inexhausted_retails.exists():
                    total_used_retail_num = 0   # 之前用了多少数量
                    inexhausted_retail = inexhausted_retails[0]
                    same_retail_orders = OrderItem.objects.filter(from_oid__contains=inexhausted_retail.oid)
                    excess_retail_num = int(inexhausted_retail.number)
                    if same_retail_orders.exists():
                        for item in same_retail_orders:
                            temp_from_oid_str = item.from_oid
                            temp_from_oid_list = temp_from_oid_str.split(',')
                            for term in temp_from_oid_list:
                                if inexhausted_retail.oid in term:
                                    total_used_retail_num += int(term.split('|')[1])
                        excess_retail_num = excess_retail_num - total_used_retail_num

                    if excess_retail_num < need_number or excess_retail_num == need_number:
                        need_number = need_number - excess_retail_num
                        temp_from_oid += inexhausted_retail.oid + '|' + str(excess_retail_num) + ','
                        temp_profit = temp_profit + float(excess_retail_num) * float(inexhausted_retail.unit_price)
                        inexhausted_retail.status = 3
                        inexhausted_retail.save()
                    else:
                        temp_from_oid += inexhausted_retail.oid + '|' + str(need_number) + ','
                        temp_profit = temp_profit + float(need_number) * float(inexhausted_retail.unit_price)
                        need_number = 0
                        inexhausted_retail.status = 2
                        inexhausted_retail.save()

                if need_number > 0:
                    unexhausted_retails = Retail.objects.filter(sid=temp_sid).filter(status=1).order_by('id')
                    if unexhausted_retails.exists():
                        for item in unexhausted_retails:
                            if need_number == 0:
                                break

                            if int(item.number) < need_number or int(item.number) == need_number:
                                need_number = need_number - int(item.number)
                                temp_from_oid += item.oid + '|' + str(item.number) + ','
                                temp_profit = temp_profit + float(item.number) * float(item.unit_price)
                                item.status = 3
                                item.save()
                            else:
                                temp_from_oid += item.oid + '|' + str(need_number) + ','
                                temp_profit = temp_profit + float(need_number) * float(item.unit_price)
                                need_number = 0
                                item.status = 2
                                item.save()

            if need_number > 0:
                inexhausted_batches = Batch.objects.filter(sid=temp_sid).filter(status=2).order_by('id')
                if inexhausted_batches.exists():
                    total_used_batch_num = 0   # 之前用了多少数量
                    inexhausted_batch = inexhausted_batches[0]
                    same_batch_orders = OrderItem.objects.filter(from_oid__contains=inexhausted_batch.oid)
                    excess_batch_num = int(inexhausted_batch.number)
                    if same_batch_orders.exists():
                        for item in same_batch_orders:
                            temp_from_oid_str = item.from_oid
                            temp_from_oid_list = temp_from_oid_str.split(',')
                            for term in temp_from_oid_list:
                                if inexhausted_batch.oid in term:
                                    total_used_batch_num += int(term.split('|')[1])
                        excess_batch_num = excess_batch_num - total_used_batch_num

                    #print excess_batch_num
                    if excess_batch_num < need_number or excess_batch_num == need_number:
                        need_number = need_number - excess_batch_num
                        temp_from_oid += inexhausted_batch.oid + '|' + str(excess_batch_num) + ','
                        if is_youpiao == 1:
                            temp_profit = temp_profit + float(excess_batch_num) * float(inexhausted_batch.cost_a)
                        elif is_youpiao == 0:
                            temp_profit = temp_profit + float(excess_batch_num) * float(inexhausted_batch.cost_b)
                        inexhausted_batch.status = 3
                        inexhausted_batch.save()
                    else:
                        temp_from_oid += inexhausted_batch.oid + '|' + str(need_number) + ','
                        if is_youpiao == 1:
                            temp_profit = temp_profit + float(need_number) * float(inexhausted_batch.cost_a)
                        elif is_youpiao == 0:
                            temp_profit = temp_profit + float(need_number) * float(inexhausted_batch.cost_b)
                        need_number = 0
                        inexhausted_batch.status = 2
                        inexhausted_batch.save()

            if need_number > 0:
                unexhausted_batches = Batch.objects.filter(sid=temp_sid).filter(status=1).order_by('id')
                if unexhausted_batches.exists():
                    for item in unexhausted_batches:
                        if need_number == 0:
                            break

                        if int(item.number) < need_number or int(item.number) == need_number:
                            need_number = need_number - int(item.number)
                            temp_from_oid += item.oid + '|' + str(item.number) + ','
                            if is_youpiao == 1:
                                temp_profit = temp_profit + float(item.number) * float(item.cost_a)
                            elif is_youpiao == 0:
                                temp_profit = temp_profit + float(item.number) * float(item.cost_b)
                            item.status = 3
                            item.save()
                        else:
                            temp_from_oid += item.oid + '|' + str(need_number) + ','
                            if is_youpiao == 1:
                                temp_profit = temp_profit + float(need_number) * float(item.cost_a)
                            elif is_youpiao == 0:
                                temp_profit = temp_profit + float(need_number) * float(item.cost_b)
                            need_number = 0
                            item.status = 2
                            item.save()

            #print need_number
            if need_number > 0:
                return False

            temp_order_item.oid = oid
            temp_order_item.from_oid = temp_from_oid
            temp_order_item.status = 1
            temp_order_item.sid = temp_sid
            temp_order_item.number = temp_number
            round(temp_profit, 2)
            temp_order_item.profit = temp_profit
            round(temp_unit_price, 2)
            temp_order_item.unit_price = temp_unit_price
            check_total_price = float(temp_number) * float(temp_unit_price)
            if check_total_price == float(temp_total_price):
                temp_order_item.total_price = temp_total_price
            else:
                round(check_total_price, 2)
                temp_order_item.total_price = check_total_price

            temp_order_item.create_time = create_time
            temp_order_item.modify_time = modify_time
            temp_order_item.order_day = today
            order_item_list.append(temp_order_item)
            i = i + 1
            order_total_price = order_total_price + float(temp_total_price)
            total_profit = total_profit + float(temp_profit)

        check = None
        check = OrderItem.objects.bulk_create(order_item_list)

        if check:
            pass
        else:
            form = OrderForm(instance=order)
            data['form'] = form
            return render_to_response(
                'order/add.html',
                data,
                context_instance=RequestContext(request)
            )

        if order_total_price > 0.0:
            order = Order()
            order.client_id = client_id
            order.oid = oid
            order.is_youpiao = int(is_youpiao)
            order.order_day = date.today()
            order.total_price = order_total_price
            round(total_profit, 2)
            order.profit = total_profit
            order.create_time = timezone.now()
            order.modify_time = timezone.now()
            order.save()
            current_order_items = OrderItem.objects.filter(oid=order.oid)
            if current_order_items.exists():
                for item in current_order_items:
                    temp_steel = get_object_or_404(Steel, id=item.sid)
                    total_number = int(temp_steel.retail_number) + int(temp_steel.number)
                    retail_number = int(temp_steel.retail_number)
                    if total_number > item.number or total_number == item.number:
                        if temp_steel.retail_number > 0:
                            if int(temp_steel.retail_number) > int(item.number) or int(temp_steel.retail_number) == int(item.number):
                                temp_steel.retail_number = int(temp_steel.retail_number) - int(item.number)
                            else:
                                temp_steel.number = int(temp_steel.number) - (int(item.number) - int(temp_steel.retail_number))
                                temp_steel.retail_number = 0
                        else:
                            temp_steel.number = int(temp_steel.number) - int(item.number)
                        temp_steel.save()
                    else:
                        return False
            return HttpResponseRedirect('/order/?id=%d' % int(order.id))
        else:
            form = OrderForm(post, instance=order)
            data['form'] = form
            return render_to_response(
                'order/add.html',
                data,
                context_instance=RequestContext(request)
            )
    else:
        form = OrderForm(instance=order)
        data['form'] = form
        return render_to_response(
            'order/add.html',
            data,
            context_instance=RequestContext(request)
        )


@permission_required('order.change_order')
def edit(request):
    data= {}
    order = None
    id = request.GET.get('id', None)
    if id:
        pass
    else:
        return HttpResponseRedirect(
            '/order/'
        )
    id = int(id)
    origin_order_item = get_object_or_404(OrderItem, id=id)

    check_time = origin_order_item.create_time + timedelta(minutes=5)
    if check_time > datetime.now():
        pass
    else:
        return HttpResponseRedirect(
            '/order/'
        )

    data['order_item'] = origin_order_item
    origin_number = int(origin_order_item.number)
    steels = Steel.objects.all()
    data['steels'] = steels

    if request.method == 'POST':
        post = request.POST.copy()
        sid = post.get('sid', None)
        number = post.get('number', 0)
        unit_price = post.get('unit_price', 0.0)
        if not sid or unit_price == 0.0 or number == 0:
            form = OrderItemForm(post, instance=origin_order_item)
            data['form'] = form
            return render_to_response(
                'order/edit.html',
                data,
                context_instance=RequestContext(request)
            )
        oid = origin_order_item.oid
        order = get_object_or_404(Order, oid=oid)
        order.total_price = float(order.total_price) - float(origin_order_item.total_price)
        current_total_price = float(number) * float(unit_price)
        order.total_price = float(order.total_price) + float(current_total_price)
        order.modify_time = datetime.now()
        order.profit = float(order.profit) - float(origin_order_item.profit)

        origin_from_oid = origin_order_item.from_oid
        origin_from_oid_list = origin_from_oid.split(',')
        origin_from_oid_list.pop()
        temp_steel = get_object_or_404(Steel, id=sid)
        temp_profit = 0.0
        for item in origin_from_oid_list:
            #print item
            temp_oid = item.split('|')[0]
            temp_number = item.split('|')[1]
            check_batch_or_retail = int(temp_oid.split('_')[1])
            if check_batch_or_retail == 1:
                temp_steel.number = int(temp_steel.number) + int(temp_number)
                temp_batch = get_object_or_404(Batch, oid=temp_oid)
                check_batches_orders = OrderItem.objects.filter(from_oid__contains=temp_batch.oid).exclude(id=origin_order_item.id)
                if check_batches_orders.exists():
                    temp_batch.status = 2
                else:
                    temp_batch.status = 1
                temp_batch.save()
            elif check_batch_or_retail == 2:
                temp_steel.retail_number = int(temp_steel.retail_number) + int(temp_number)
                temp_retail = None
                temp_retails = Retail.objects.filter(oid=temp_oid).filter(sid=sid)
                if temp_retails.exists():
                    temp_retail = temp_retails[0]
                else:
                    return False

                check_retails_orders = OrderItem.objects.filter(from_oid__contains=temp_retail.oid).exclude(id=origin_order_item.id)
                if check_retails_orders.exists():
                    temp_retail.status = 2
                else:
                    temp_retail.status = 1
                temp_retail.save()
        temp_steel.save()

        # 获取来源订单号
        temp_from_oid = ''
        need_number = int(number)  # 需要的数量
        temp_steel = get_object_or_404(Steel, id=sid)
        if temp_steel.retail_number > 0:
            inexhausted_retails = Retail.objects.filter(sid=sid).filter(status=2).order_by('id')
            if inexhausted_retails.exists():
                total_used_retail_num = 0   # 之前用了多少数量
                inexhausted_retail = inexhausted_retails[0]
                same_retail_orders = OrderItem.objects.filter(from_oid__contains=inexhausted_retail.oid).exclude(id=origin_order_item.id)
                excess_retail_num = int(inexhausted_retail.number)
                if same_retail_orders.exists():
                    for item in same_retail_orders:
                        temp_from_oid_str = item.from_oid
                        temp_from_oid_list = temp_from_oid_str.split(',')
                        for term in temp_from_oid_list:
                            if inexhausted_retail.oid in term:
                                total_used_retail_num += int(term.split('|')[1])
                    excess_retail_num = excess_retail_num - total_used_retail_num

                if excess_retail_num < need_number or excess_retail_num == need_number:
                    need_number = need_number - excess_retail_num
                    temp_from_oid += inexhausted_retail.oid + '|' + str(excess_retail_num) + ','
                    temp_profit = temp_profit + float(excess_retail_num) * float(inexhausted_retail.unit_price)
                    inexhausted_retail.status = 3
                    inexhausted_retail.save()
                else:
                    temp_from_oid += inexhausted_retail.oid + '|' + str(need_number) + ','
                    temp_profit = temp_profit + float(need_number) * float(inexhausted_retail.unit_price)
                    need_number = 0
                    inexhausted_retail.status = 2
                    inexhausted_retail.save()

            if need_number > 0:
                unexhausted_retails = Retail.objects.filter(sid=sid).filter(status=1).order_by('id')
                if unexhausted_retails.exists():
                    for item in unexhausted_retails:
                        if need_number == 0:
                            break

                        if int(item.number) < need_number or int(item.number) == need_number:
                            need_number = need_number - int(item.number)
                            temp_from_oid += item.oid + '|' + str(item.number) + ','
                            temp_profit = temp_profit + float(item.number) * float(item.unit_price)
                            item.status = 3
                            item.save()
                        else:
                            temp_from_oid += item.oid + '|' + str(need_number) + ','
                            temp_profit = temp_profit + float(need_number) * float(item.unit_price)
                            need_number = 0
                            item.status = 2
                            item.save()

        if need_number > 0:
            inexhausted_batches = Batch.objects.filter(sid=sid).filter(status=2).order_by('id')
            if inexhausted_batches.exists():
                total_used_batch_num = 0   # 之前用了多少数量
                inexhausted_batch = inexhausted_batches[0]
                same_batch_orders = OrderItem.objects.filter(from_oid__contains=inexhausted_batch.oid).exclude(id=origin_order_item.id)
                excess_batch_num = int(inexhausted_batch.number)
                if same_batch_orders.exists():
                    for item in same_batch_orders:
                        temp_from_oid_str = item.from_oid
                        temp_from_oid_list = temp_from_oid_str.split(',')
                        for term in temp_from_oid_list:
                            if inexhausted_batch.oid in term:
                                total_used_batch_num += int(term.split('|')[1])
                    excess_batch_num = excess_batch_num - total_used_batch_num

                #print excess_batch_num
                if excess_batch_num < need_number or excess_batch_num == need_number:
                    need_number = need_number - excess_batch_num
                    temp_from_oid += inexhausted_batch.oid + '|' + str(excess_batch_num) + ','
                    if order.is_youpiao == 1:
                        temp_profit = temp_profit + float(excess_batch_num) * float(inexhausted_batch.cost_a)
                    elif order.is_youpiao == 0:
                        temp_profit = temp_profit + float(excess_batch_num) * float(inexhausted_batch.cost_b)
                    inexhausted_batch.status = 3
                    inexhausted_batch.save()
                else:
                    temp_from_oid += inexhausted_batch.oid + '|' + str(need_number) + ','
                    if order.is_youpiao == 1:
                        temp_profit = temp_profit + float(need_number) * float(inexhausted_batch.cost_a)
                    elif order.is_youpiao == 0:
                        temp_profit = temp_profit + float(need_number) * float(inexhausted_batch.cost_b)
                    need_number = 0
                    inexhausted_batch.status = 2
                    inexhausted_batch.save()

        if need_number > 0:
            unexhausted_batches = Batch.objects.filter(sid=sid).filter(status=1).order_by('id')
            if unexhausted_batches.exists():
                for item in unexhausted_batches:
                    if need_number == 0:
                        break

                    if int(item.number) < need_number or int(item.number) == need_number:
                        need_number = need_number - int(item.number)
                        temp_from_oid += item.oid + '|' + str(item.number) + ','
                        if order.is_youpiao == 1:
                            temp_profit = temp_profit + float(item.number) * float(item.cost_a)
                        elif order.is_youpiao == 0:
                            temp_profit = temp_profit + float(item.number) * float(item.cost_b)
                        item.status = 3
                        item.save()
                    else:
                        temp_from_oid += item.oid + '|' + str(need_number) + ','
                        if order.is_youpiao == 1:
                            temp_profit = temp_profit + float(need_number) * float(item.cost_a)
                        elif order.is_youpiao == 0:
                            temp_profit = temp_profit + float(need_number) * float(item.cost_b)
                        need_number = 0
                        item.status = 2
                        item.save()

        #print need_number
        if need_number > 0:
            return False

        round(temp_profit, 2)
        order.profit += temp_profit
        order.save()

        post.update({
            'profit': temp_profit,
            'from_oid': temp_from_oid,
            'oid': oid,
            'total_price': current_total_price,
            'create_time': origin_order_item.create_time,
            'order_day': origin_order_item.order_day,
            'modify_time': datetime.now(),
            'status': 1,
        })

        form = OrderItemForm(post, instance=origin_order_item)
        data['form'] = form
        if form.is_valid():
            current_order_item = form.save()
            current_sid = current_order_item.sid
            current_number = int(current_order_item.number)
            current_steel = get_object_or_404(Steel, id=current_order_item.sid)
            total_number = int(current_steel.retail_number) + int(current_steel.number)
            retail_number = int(current_steel.retail_number)
            if total_number > current_order_item.number or total_number == current_order_item.number:
                if current_steel.retail_number > 0:
                    if int(current_steel.retail_number) > int(current_order_item.number) or int(current_steel.retail_number) == int(current_order_item.number):
                        current_steel.retail_number = int(current_steel.retail_number) - int(current_order_item.number)
                    else:
                        current_steel.number = int(current_steel.number) - (int(current_order_item.number) - int(current_steel.retail_number))
                        current_steel.retail_number = 0
                else:
                    current_steel.number = int(current_steel.number) - int(current_order_item.number)
                current_steel.save()
            else:
                return False

            return HttpResponseRedirect(
                '/order/?id=%d' % int(order.id)
            )
        else:
            print form.errors
            return render_to_response(
                'order/edit.html',
                data,
                context_instance=RequestContext(request)
            )

    else:
        form = OrderItemForm(instance=origin_order_item)
        data['form'] = form
        return render_to_response(
            'order/edit.html',
            data,
            context_instance=RequestContext(request)
        )


@permission_required('order.change_order')
def order_edit(request):
    data = {}
    order = None
    oid = request.GET.get('oid', None)
    if oid:
        order = get_object_or_404(Order, oid=oid)
        data['order'] = order
        data['oid'] = oid
    origin_is_youpiao = int(order.is_youpiao)
    clients = Client.objects.all()
    data['clients'] = clients
    if request.method == 'POST':
        post = request.POST.copy()
        
        is_youpiao = post.get('is_youpiao', None)
        if is_youpiao:
            is_youpiao = int(is_youpiao)
        else:
            False

        if is_youpiao != origin_is_youpiao:
            total_profit = 0.0
            order.is_youpiao = is_youpiao
            is_youpiao = int(is_youpiao)
            order_items = OrderItem.objects.filter(oid=order.oid)
            if order_items.exists():
                for item in order_items:
                    sid = int(item.sid)
                    from_oid_list = item.from_oid.split(',')
                    from_oid_list.pop()
                    temp_profit = 0.0
                    for term in from_oid_list:
                        temp_oid = term.split('|')[0]
                        temp_num = int(term.split('|')[1])
                        check_batch_or_retail = int(temp_oid.split('_')[1])
                        if check_batch_or_retail == 1:
                            temp_batch = Batch.objects.get(oid=temp_oid)
                            if is_youpiao == 1:
                                temp_profit += float(temp_batch.cost_a) * float(temp_num)
                            elif is_youpiao == 0:
                                temp_profit += float(temp_batch.cost_b) * float(temp_num)
                        elif check_batch_or_retail == 2:
                            temp_retails = Retail.objects.filter(oid=temp_oid).filter(sid=sid)
                            if temp_retails.exists():
                                temp_retail = temp_retails[0]
                                temp_profit += float(temp_retail.unit_price) * float(temp_num)
                    item.profit = temp_profit
                    item.save()
                    total_profit += temp_profit
            else:
                False

            order.profit = total_profit

        client_id = post.get('client_id', None)
        if client_id:
            client_id = int(client_id)
        else:
            form = OrderForm(instance=order)
            data['form'] = form
            return render_to_response(
                'order/order_edit.html',
                data,
                context_instance=RequestContext(request)
            )

        client = None
        client = get_object_or_404(Client, id=client_id)
        if client:
            order.client_id = client_id
            order.save()
            return HttpResponseRedirect(
                '/order/?id=%d' % int(order.id)
            )

    else:
        form = OrderForm(instance=order)
        data['form'] = form
        return render_to_response(
            'order/order_edit.html',
            data,
            context_instance=RequestContext(request)
        )

@permission_required('order.change_order')
def load_data(request):
    resp_dict = {
        'code':0,
        'data':None,
    }
    order_list = []
    date = request.GET.get('date', None)

    clients = Client.objects.all()
    client_dict = {}
    #print "ok"
    for item in clients:
        client_dict[int(item.id)] = item.name
    if date:
        date = datetime.strptime(date, DATE_PATTERN).date()
        orders = Order.objects.filter(order_day=date).order_by('-create_time')
        if orders.exists():
            for item in orders:
                print item
                temp_client = None
                if int(item.client_id) in client_dict:
                    temp_client = client_dict[int(item.client_id)]
                order_list.append({
                    'oid': item.oid,
                    'total_price': float(item.total_price),
                    'order_date': str(item.order_day),
                    'client': temp_client,
                })
        resp_dict['code'] = 1
        resp_dict['data'] = order_list

    return dump_response(resp_dict)


@permission_required('order.change_order')
def order_export(request, order_list, steel_dict, client_dict, year_month):
    oid_list = []
    for item in order_list:
        oid_list.append(item.oid)

    order_items = OrderItem.objects.filter(oid__in=oid_list)

    order_detail_list = []
    for item in order_list:
        temp_dict = {}
        is_youpiao = int(item.is_youpiao)
        temp_order_items = order_items.filter(oid=item.oid)
        order_item_list = []
        if temp_order_items.exists():
            for term in temp_order_items:
                order_item_dict = {}
                order_item_dict['order_item'] = term
                temp_sid = term.sid
                if term.sid in steel_dict:
                    order_item_dict['steel'] = steel_dict[term.sid]
                
                order_item_dict['income'] = float(term.total_price) - float(term.profit)
                temp_from_oid_arr = []
                temp_from_oid_list = term.from_oid.split(',')
                temp_from_oid_list.pop()
                for oid_term in temp_from_oid_list:
                    term_oid = oid_term.split('|')[0]
                    check_batch_or_retail = int(term_oid.split('_')[1])
                    term_num = oid_term.split('|')[1]
                    cost = 0.0
                    if check_batch_or_retail == 1:
                        temp_batch = get_object_or_404(Batch, oid=term_oid)
                        if is_youpiao == 1:
                            print cost
                            cost = float(temp_batch.cost_a)
                        else:
                            cost = float(temp_batch.cost_b)
                    elif check_batch_or_retail == 2:
                        temp_retails = Retail.objects.filter(oid=term_oid).filter(sid=int(temp_sid))
                        if temp_retails.exists():
                            temp_retail = temp_retails[0]
                            cost = float(temp_retail.unit_price)
                        else:
                            return False
                    term_arr = [term_oid, term_num, int(check_batch_or_retail), cost]
                    print term_arr
                    temp_from_oid_arr.append(term_arr)
                order_item_dict['from_oid'] = temp_from_oid_arr
                order_item_list.append(order_item_dict)
    
        temp_dict['detail'] = order_item_list
        if item.client_id in client_dict:
            temp_dict['client'] = client_dict[item.client_id]

        temp_dict['order'] = item
        temp_dict['profit'] = float(item.total_price) - float(item.profit)
        order_detail_list.append(temp_dict)

    filename = str(year_month) + '销售订单备份.xls'
    workbook = xlwt.Workbook(encoding='utf-8')
    style = xlwt.XFStyle()
    font = xlwt.Font()
    font.name = 'SimSun'
    style.font = font
    sheet = workbook.add_sheet('sheet1', cell_overwrite_ok=True)

    #print order_detail_list

    i = 0
    for item in order_detail_list:

        sheet.write(i, 0, '订单号')
        sheet.write(i, 1, '客户', style)
        sheet.write(i, 2, '是否有票', style)
        sheet.write(i, 3, '总销售额', style)
        sheet.write(i, 4, '总成本', style)
        sheet.write(i, 5, '总利润', style)
        sheet.write(i, 6, '时间', style)
        i += 1
        sheet.write(i, 0, item['order'].oid)
        sheet.write(i, 1, item['client'].name, style)
        sheet.write(i, 2, int(item['order'].is_youpiao))
        sheet.write(i, 3, float(item['order'].total_price))
        sheet.write(i, 4, float(item['order'].profit))
        sheet.write(i, 5, float(item['profit']))
        sheet.write(i, 6, str(item['order'].order_day))
        i += 1
        sheet.write(i, 0, '货品', style)
        sheet.write(i, 1, '数量', style)
        sheet.write(i, 2, '单价', style)
        sheet.write(i, 3, '销售额', style)
        sheet.write(i, 4, '成本', style)
        sheet.write(i, 5, '来源', style)
        i += 1
        for term in item['detail']:
            sheet.write(i, 0, term['steel'].name)
            sheet.write(i, 1, int(term['order_item'].number))
            sheet.write(i, 2, float(term['order_item'].unit_price))
            sheet.write(i, 3, float(term['order_item'].total_price))
            sheet.write(i, 4, float(term['order_item'].profit))
            j = 5
            for from_oid_term in term['from_oid']:
                sheet.write(i, j, from_oid_term[0])
                j += 1
                sheet.write(i, j, int(from_oid_term[1]))
                j += 1
                sheet.write(i, j, float(from_oid_term[3]))
                j += 1

        i += 2

    response = HttpResponse(mimetype='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    workbook.save(response)
    return response
