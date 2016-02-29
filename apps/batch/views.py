#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from django.contrib.auth.decorators import permission_required
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from apps.batch.models import Batch, BatchForm
from apps.steel.models import Steel
from apps.utils.page_helper import list_by_page
from django.utils import timezone
from datetime import datetime, date, timedelta
from apps.supplier.models import Supplier
from apps.steel.models import CostRule
from django.shortcuts import get_object_or_404
import xlwt
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

DATE_PATTERN = '%Y-%m-%d'


@permission_required('batch.change_batch')
def list(request):
    data = {}
    batches = Batch.objects.all().order_by('-create_time')
    steels = Steel.objects.all()
    
    steel_dict = {}
    for item in steels:
        steel_dict[item.id] = item
    
    data['steels'] = steels
    id = request.GET.get('id', None)
    if id:
        id = int(id)
        data['id'] = id
    
    oid = request.GET.get('oid', None)
    if oid:
        batches = batches.filter(oid__contains=oid)
        data['oid'] = oid

    last_batches = Batch.objects.order_by('-modify_time')
    if last_batches.exists():
        last_id = last_batches[0].id
        data['last_id'] = last_id

    product_place = request.GET.get('product_place', None)
    if product_place:
        batches = batches.filter(product_place__contains=product_place)
        data['product_place'] = product_place

    from_date = request.GET.get('from_date', None)
    if from_date:
        from_date = datetime.strptime(from_date, DATE_PATTERN).date()
        batches = batches.filter(batch_date__gte=from_date)
        data['from_date'] = from_date

    end_date = request.GET.get('end_date', None)
    if end_date:
        end_date = datetime.strptime(end_date, DATE_PATTERN).date()
        batches = batches.filter(batch_date__lte=end_date)
        data['end_date'] = end_date

    steel_name = request.GET.get('steel_name', None)
    if steel_name:
        temp_steels = steels.filter(name__contains=steel_name)
        data['steel_name'] = steel_name
        if temp_steels.exists():
            steel_id_list = []
            for steel in temp_steels:
                steel_id_list.append(steel.id)
            batches = batches.filter(sid__in=steel_id_list)

    sid = request.GET.get('sid', None)
    if sid:
        sid = int(sid)
        data['sid'] = sid
        batches = batches.filter(sid=sid)

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
            export_batches = batches.filter(batch_date__gte=last_month_first_day)
            year_month += last_month_first_day.strftime('%Y%m%d') + '_'
            
            if not end_date:
                last_month_last_day = date(datetime.today().year, datetime.today().month, 1) - timedelta(days=1)
                export_batches = batches.filter(batch_date__lte=last_month_last_day)
                year_month += last_month_last_day.strftime('%Y%m%d')
            else:
                year_month += end_date.strftime('%Y%m%d')
        else:
            if end_date:
                year_month += from_date.strftime('%Y%m%d') + '_'
                year_month += end_date.strftime('%Y%m%d')
                export_batches = batches
            else:
                year_month += from_date.strftime('%Y%m%d') + '_'
                export_batches = batches.filter(batch_date__lte=datetime.today())
                year_month += datetime.today().strftime('%Y%m%d')
        #print last_month_last_day
        return batch_export(request, export_batches, steel_dict, year_month)

    batches = list_by_page(request, batches)
    batch_list = []
    for batch in batches:
        temp_dict = {}
        temp_dict['batch'] = batch
        if batch.sid in steel_dict:
            temp_dict['steel'] = steel_dict[batch.sid]

        check_time = batch.create_time + timedelta(minutes=5)
        if check_time < datetime.now():
            temp_dict['check_time'] = 0
        else:
            temp_dict['check_time'] = 1

        batch_list.append(temp_dict)

    data['batches'] = batches
    data['batch_list'] = batch_list

    return render_to_response(
        'batch/list.html',
        data,
        context_instance=RequestContext(request)
    )


@permission_required('batch.change_batch')
def add(request):
    data = {}
    oid = datetime.now().strftime('%Y%m%d%H%M%S')
    oid = str(oid) + '_1'   # represent batch 1
    data['oid'] = oid
    batch = None
    steels = Steel.objects.all()
    data['steels'] = steels
    suppliers = Supplier.objects.all()
    data['suppliers'] = suppliers
    error_list = []
    if request.method == 'POST':
        post = request.POST.copy()
        oid = post.get('oid', None)
        supplier_name = post.get('supplier_name', None)
        post_supplier_id = post.get('supplier_id', None)
        if supplier_name:
            temp_suppliers = suppliers.filter(name=supplier_name)
            temp_supplier = None
            if temp_suppliers.exists():
                temp_supplier = temp_suppliers[0]
            else:
                supplier = Supplier()
                supplier.name = supplier_name
                supplier.status = 1
                supplier.create_time = timezone.now()
                supplier.modify_time = supplier.create_time
                supplier.save()
                temp_supplier = supplier
            supplier_id = temp_supplier.id
        if post_supplier_id:
            #print post_supplier_id
            post_supplier_id = int(post_supplier_id)
            temp_suppliers = suppliers.filter(id=post_supplier_id)
            if temp_suppliers.exists():
                temp_supplier = temp_suppliers[0]
                supplier_id = temp_supplier.id
            else:
                form = BatchForm(post, instance=batch)
                data['form'] = form
                return render_to_response(
                    'batch/add.html',
                    data,
                    context_instance=RequestContext(request)
                )

        steel_name = post.get('steel_name', None)
        steel_id = post.get('steel_id', None)
        len_str = post.get('len_str', None)
        wid_str = post.get('wid_str', None)

        if len_str is None:
            form = BatchForm(post, instance=batch)
            error_str = '长度不能为空'
            error_list.append(error_str)
            data['error_list'] = error_list
            data['form'] = form
            return render_to_response(
                'batch/add.html',
                data,
                context_instance=RequestContext(request)
            )

        if wid_str is None:
            form = BatchForm(post, instance=batch)
            error_str = '宽度不能为空'
            error_list.append(error_str)
            data['error_list'] = error_list
            data['form'] = form
            return render_to_response(
                'batch/add.html',
                data,
                context_instance=RequestContext(request)
            )
        #print len_str
        temp_steel = None
        if steel_name:
            temp_steels = steels.filter(name__contains=steel_name)
            if temp_steels.exists():
                temp_steel = temp_steels[0]

        if steel_id:
            steel_id = int(steel_id)
            temp_steels = steels.filter(id=steel_id)
            if temp_steels.exists():
                temp_steel = temp_steels[0]

        if temp_steel is None:
            error_str = '钢铁名称必须是已经录入系统'
            error_list.append(error_str)
            data['error_list'] = error_list

            form = BatchForm(post, instance=batch)
            data['form'] = form
            return render_to_response(
                'batch/add.html',
                data,
                context_instance=RequestContext(request)
            )

        else:
            if float(len_str) == float(temp_steel.len_str)\
                and float(wid_str) == float(temp_steel.wid_str):
                #print temp_steel.wid_str
                pass
            else:
                form = BatchForm(post, instance=batch)
                data['form'] = form
                return render_to_response(
                    'batch/add.html',
                    data,
                    context_instance=RequestContext(request)
                )

        post.update({
            'sid': temp_steel.id
        })

        create_time = timezone.now()
        modify_time = create_time
        batch_date = date.today()
        post.update({
            'oid': oid,
            'status': 1,
            'supplier_id': supplier_id,
            'create_time': create_time,
            'modify_time': modify_time,
            'batch_date': batch_date,
        })

        cost_a = float(post.get("cost_a", 0.0))  # now cost_a
        cost_b = float(post.get("cost_b", 0.0))
        true_high = 0.0
        total_price = 0.0
        weight = float(post.get('weight', 0.0))
        number = float(post.get('number', 0))
        unit_price = float(post.get('unit_price', 0.0))
        if unit_price == 0.0:
            error_str = '单价不能为零'
            error_list.append(error_str)
            data['error_list'] = error_list

            form = BatchForm(post, instance=batch)
            data['form'] = form
            return render_to_response(
                'batch/add.html',
                data,
                context_instance=RequestContext(request)
            )
        if weight == 0.0:
            error_str = '重量不能为零'
            error_list.append(error_str)
            data['error_list'] = error_list

            form = BatchForm(post, instance=batch)
            data['form'] = form
            return render_to_response(
                'batch/add.html',
                data,
                context_instance=RequestContext(request)
            )

        total_price = float(weight) * float(unit_price)
        total_price = round(total_price, 2)
        if number > 0:
            true_high = (float(weight) * 1000) / float(number) / 7.85 / float(len_str) / float(wid_str)
            cost_a = round(cost_a, 2)  # retain last 2 points after dot
            cost_b = round(cost_b, 2)
            true_high = round(true_high, 3)
            #print cost_a
        post.update({
            'cost_a': cost_a,
            'cost_b': cost_b,
            'true_high': true_high,
            'total_price': total_price
        })
        if int(temp_steel.number) > 0:
            last_batches = Batch.objects.filter(sid=int(temp_steel.id)).filter(number__gt=0).order_by('-create_time').exclude(status=0)
            if last_batches.exists():
                last_batch = last_batches[0]
                print last_batch.id
            else:
                last_batch = None
        else:
            last_batch = None

        form = BatchForm(post, instance=batch)
        data['form'] = form

        if form.is_valid():
            current_batch = form.save()  # current batch
            temp_steel = get_object_or_404(Steel, id=current_batch.sid)
            steel_cost_a = 0.0
            steel_cost_b = 0.0
            sell_price_a = 0.0
            sell_price_b = 0.0
            temp_true_high = 0.0  # compare current and last one steel different high
            if current_batch.number == 0:
                temp_steel.weight = float(temp_steel.weight)\
                    + float(current_batch.weight)
                temp_steel.modify_time = datetime.now()
                temp_steel.save()
                return HttpResponseRedirect(
                    '/batch/list/?id=%d' % current_batch.id
                )

            if last_batch:
                if float(last_batch.cost_a) > float(current_batch.cost_a):
                    steel_cost_a = float(last_batch.cost_a)\
                        + float(last_batch.cost_a)
                    steel_cost_a = steel_cost_a / 2.0
                else:
                    steel_cost_a = float(current_batch.cost_a)

                if float(last_batch.cost_b) > float(current_batch.cost_b):
                    steel_cost_b = float(last_batch.cost_b)\
                        + float(current_batch.cost_b)

                    steel_cost_b = steel_cost_b / 2.0

                else:
                    steel_cost_b = float(current_batch.cost_b)

                if float(last_batch.true_high) < float(current_batch.true_high):
                    temp_true_high = float(last_batch.true_high)
                else:
                    temp_true_high = float(current_batch.true_high)

            else:
                steel_cost_a = float(current_batch.cost_a)
                steel_cost_b = float(current_batch.cost_b)
                temp_true_high = float(current_batch.true_high)

            temp_steel.cost_a = steel_cost_a
            temp_steel.cost_b = steel_cost_b
            
            cost_rules = CostRule.objects.all().order_by('-id')[:1]
            if cost_rules.exists():
                cost_rule = float(cost_rules[0].rule)
            else:
                cost_rule = 100.0

            sell_price_a = float(steel_cost_a) / float(temp_true_high)\
                / float(temp_steel.len_str) / float(temp_steel.wid_str)\
                / 7.85
            sell_price_a = sell_price_a * 1000.0
            sell_price_a = sell_price_a + cost_rule
            sell_price_a = sell_price_a / 1000.0\
                * float(temp_steel.high_str) * float(temp_steel.len_str) * float(temp_steel.wid_str)\
                * 7.85
            temp_steel.sell_price_a = sell_price_a

            sell_price_b = float(steel_cost_b) / float(temp_true_high)\
                / float(temp_steel.len_str) / float(temp_steel.wid_str)\
                / 7.85
            sell_price_b = sell_price_b * 1000.0
            sell_price_b = sell_price_b + cost_rule
            sell_price_b = sell_price_b / 1000.0\
                * float(temp_steel.high_str) * float(temp_steel.len_str) * float(temp_steel.wid_str)\
                * 7.85
            temp_steel.sell_price_b = sell_price_b

            if current_batch.number > 0.0:
                temp_steel.number = int(temp_steel.number)\
                        + int(current_batch.number)

            round(temp_steel.cost_a, 2)
            round(temp_steel.cost_b, 2)
            round(temp_steel.sell_price_a, 2)
            round(temp_steel.sell_price_b, 2)
            temp_steel.modify_time = datetime.now()
            temp_steel.save()
            return HttpResponseRedirect(
                '/batch/?id=%d' % current_batch.id
            )
        else:
            error_str = '表单有错'
            error_list.append(error_str)
            data['error_list'] = error_list

            print form.errors
            return render_to_response(
                'batch/add.html',
                data,
                context_instance=RequestContext(request)
            )
    else:
        form = BatchForm(instance=batch)
        data['form'] = form
        return render_to_response(
            'batch/add.html',
            data,
            context_instance=RequestContext(request)
        )


@permission_required('batch.change_batch')
def edit(request, id=None):
    data = {}
    origin_batch = None
    steels = Steel.objects.all()
    data['steels'] = steels
    suppliers = Supplier.objects.all()
    data['suppliers'] = suppliers
    if id:
        id = int(id)
        origin_batch = get_object_or_404(Batch, id=id)

    data['origin_batch'] = origin_batch
    last_sid = int(origin_batch.sid)
    data['sid'] = int(last_sid)
    now_time = datetime.now()
    check_modify_time = origin_batch.create_time + timedelta(minutes=5)
    if origin_batch.status == 0 or check_modify_time < now_time:
        return HttpResponseRedirect(
            '/batch/'
        )
    else:
        pass

    data['supplier_id'] = origin_batch.supplier_id
    last_supplier_id = int(origin_batch.supplier_id)
    last_number = int(origin_batch.number)
    data['number'] = last_number
    last_weight = float(origin_batch.weight)
    oid = origin_batch.oid
    data['oid'] = oid
    if request.method == 'POST':
        post = request.POST.copy()
        supplier_id = post.get('supplier_id', None)
        steel_id = post.get('sid', None)
        #print steel_id
        if int(steel_id) == int(origin_batch.sid) and int(supplier_id) == int(origin_batch.supplier_id):
            #print steel_id
            pass
        else:
            form = BatchForm(post, instance=origin_batch)
            data['form'] = form
            return render_to_response(
                'batch/edit.html',
                data,
                context_instance=RequestContext(request)
            )
        oid = origin_batch.oid
        number = int(post.get('number', 0))
        cost_a = float(post.get('cost_a', 0.0))
        cost_b = float(post.get('cost_b', 0.0))
        true_high = 0.0
        unit_price = float(post.get('unit_price', 0))
        weight = float(post.get('weight', 0))
        current_steel = get_object_or_404(Steel, id=steel_id)
        if current_steel.status == 0:
            return HttpResponseRedirect(
                '/batch/'
            )

        len_str = current_steel.len_str
        high_str = current_steel.high_str
        wid_str = current_steel.wid_str

        if number > 0:
            true_high = (float(weight) * 1000) / float(number) / 7.85 / float(len_str) / float(wid_str)
            cost_a = round(cost_a, 2)  # retain last 2 points after dot
            cost_b = round(cost_b, 2)
            true_high = round(true_high, 3)
            #print cost_a

        total_price = float(unit_price) * float(weight)
        total_price = round(total_price, 2)
        create_time = origin_batch.create_time
        modify_time = datetime.now()
        batch_date = origin_batch.batch_date
        post.update({
            'oid': oid,
            'cost_a': cost_a,
            'cost_b': cost_b,
            'true_high': true_high,
            'modify_time': modify_time,
            'create_time': create_time,
            'total_price': total_price,
            'batch_date': batch_date,
            'status': 1,
        })
        form = BatchForm(post, instance=origin_batch)
        data['form'] = form

        current_steel = get_object_or_404(Steel, id=steel_id)
        check_number = current_steel.number - last_number
        if check_number > 0:
            last_batches = Batch.objects.filter(sid=int(current_steel.id)).filter(number__gt=0).exclude(id=origin_batch.id).exclude(status=0).order_by('-create_time')
            if last_batches.exists():
                last_batch = last_batches[0]
            else:
                last_batch = None
        else:
            last_batch = None

        if form.is_valid():
            current_batch = form.save()
            current_steels = Steel.objects.filter(id=current_batch.sid)
            steel_cost_a = 0.0
            steel_cost_b = 0.0
            sell_price_a = 0.0
            sell_price_b = 0.0
            temp_true_high = 0.0  # compare current and last one steel different high

            current_number = int(current_batch.number)
            if current_batch.number == 0:
                if last_number == 0 and current_number == 0:
                    current_steel.weight = float(current_steel.weight) + float(current_batch.weight) - float(last_weight)
                elif last_number > 0 and current_number == 0:
                    return False
                current_steel.save()
                return HttpResponseRedirect(
                    '/batch/?id=%d' % current_batch.id
                )

            if last_batch:
                if float(last_batch.cost_a) > float(current_batch.cost_a):
                    steel_cost_a = float(last_batch.cost_a)\
                        + float(current_batch.cost_a)
                    steel_cost_a = steel_cost_a / 2.0
                else:
                    steel_cost_a = float(current_batch.cost_a)
                if float(last_batch.cost_b) > float(current_batch.cost_b):
                    steel_cost_b = float(last_batch.cost_b)\
                        + float(current_batch.cost_b)
                    steel_cost_b = steel_cost_b / 2.0

                else:
                    steel_cost_b = float(current_batch.cost_b)

                if float(last_batch.true_high) \
                    < float(current_batch.true_high):
                    temp_true_high = float(last_batch.true_high)
                else:
                    temp_true_high = float(current_batch.true_high)
            else:
                steel_cost_a = float(current_batch.cost_a)
                steel_cost_b = float(current_batch.cost_b)
                temp_true_high = float(current_batch.true_high)

            cost_rules = CostRule.objects.all().order_by('-id')[:1]
            if cost_rules.exists():
                cost_rule = float(cost_rules[0].rule)
            else:
                cost_rule = 100.0

            current_steel.cost_a = steel_cost_a
            current_steel.cost_b = steel_cost_b
            sell_price_a = float(steel_cost_a) / float(temp_true_high)\
                / float(current_steel.len_str) / float(current_steel.wid_str)\
                / 7.85
            sell_price_a = sell_price_a * 1000.0
            sell_price_a = sell_price_a + cost_rule
            sell_price_a = sell_price_a / 1000.0\
                * float(current_steel.high_str) * float(current_steel.len_str) * float(current_steel.wid_str)\
                * 7.85
            current_steel.sell_price_a = sell_price_a

            sell_price_b = float(steel_cost_b) / float(temp_true_high)\
                / float(current_steel.len_str) / float(current_steel.wid_str)\
                / 7.85
            sell_price_b = sell_price_b * 1000.0
            sell_price_b = sell_price_b + cost_rule
            sell_price_b = sell_price_b / 1000.0\
                * float(current_steel.high_str) * float(current_steel.len_str) * float(current_steel.wid_str)\
                * 7.85
            current_steel.sell_price_b = sell_price_b
            print last_number
            print current_batch.number
            current_steel.number = int(current_steel.number)\
                + int(current_batch.number) - int(last_number)

            if last_number ==0 and current_number > 0:
                if last_weight == float(current_batch.weight):
                    current_steel.weight = float(current_steel.weight) - float(current_batch.weight)
                else:
                    return False

            round(current_steel.cost_a, 2)
            round(current_steel.cost_b, 2)
            round(current_steel.sell_price_a, 2)
            round(current_steel.sell_price_b, 2)
            current_steel.modify_time = datetime.now()
            current_steel.save()

            return HttpResponseRedirect(
                '/batch/?id=%d' % current_batch.id
            )
        else:
            print form.errors
            form = BatchForm(post, instance=origin_batch)
            data['form']
            return render_to_response(
                'batch/edit.html',
                data,
                context_instance=RequestContext(request)
            )

    else:
        form = BatchForm(instance=origin_batch)
        data['form'] = form
        return render_to_response(
            'batch/edit.html',
            data,
            context_instance=RequestContext(request)
        )


@permission_required('batch.change_batch')
def change(request, id=None):  # can change batch before get to market
    data = {}
    batch = None
    steels = Steel.objects.filter(status=1)
    data['steels'] = steels
    suppliers = Supplier.objects.filter(status=1)
    data['suppliers'] = suppliers
    if id:
        id = int(id)
        batch = get_object_or_404(Batch, id=id)
        if batch.number > 0 or batch.status != 1:
            return HttpResponseRedirect(
                '/batch/'
            )
    data['batch'] = batch
    data['sid'] = batch.sid
    origin_steel = get_object_or_404(Steel, id=batch.sid)

    if origin_steel.status == 0:
        return HttpResponseRedirect(
            '/batch/'
        )

    data['origin_steel'] = origin_steel
    data['supplier_id'] = batch.supplier_id
    print batch.sid
    oid = batch.oid
    data['oid'] = oid
    origin_weight = batch.weight
    if request.method == 'POST':
        oid = batch.oid
        post = request.POST.copy()
        cost_a = batch.cost_a
        cost_b = batch.cost_b
        true_high = batch.true_high
        create_time = batch.create_time
        modify_time = datetime.now()
        unit_price = post.get('unit_price', 0.0)
        weight = post.get('weight', 0.0)
        if float(unit_price) == 0.0 or float(weight) == 0.0:
            form = BatchForm(post, instance=batch)
            data['form'] = form
            return render_to_response(
                'batch/change.html',
                data,
                context_instance=RequestContext(request)
            )
        total_price = float(unit_price) * float(weight)
        post.update({
            'oid': oid,
            'number': batch.number,
            'cost_a': cost_a,
            'cost_b': cost_b,
            'true_high': true_high,
            'create_time': create_time,
            'modify_time': modify_time,
            'total_price': total_price,
            'batch_date': batch.batch_date,
        })
        sid = post.get('sid', None)
        if sid:
            sid = int(sid)
            current_steel = get_object_or_404(Steel, id=current_batch.sid)
            if current_steel.status == 1:
                pass
            else:
                form = BatchForm(post, instance=batch)
                data['form'] = form
                return render_to_response(
                    'batch/change.html',
                    data,
                    context_instance=RequestContext(request)
                )
        else:
            form = BatchForm(post, instance=batch)
            data['form'] = form
            return render_to_response(
                'batch/change.html',
                data,
                context_instance=RequestContext(request)
            )

        form = BatchForm(post, instance=batch)
        data['form'] = form
        if form.is_valid():
            current_batch = form.save()
            origin_steel.weight = float(origin_steel.weight) - float(origin_weight)
            origin_steel.save()

            current_steel.weight = float(current_steel.weight) + float(current_batch.weight)
            current_steel.save()
            return HttpResponseRedirect(
                '/batch/?id=%d' % current_batch.id
            )
        else:
            print form.errors
            form = BatchForm(post, instance=batch)
            data['form'] = form
            return render_to_response(
                'batch/change.html',
                data,
                context_instance=RequestContext(request)
            )

    else:
        form = BatchForm(instance=batch)
        data['form'] = form
        return render_to_response(
            'batch/change.html',
            data,
            context_instance=RequestContext(request)
        )


@permission_required('batch.change_batch')
def batch_export(request, batch_list, steel_dict, year_month):
    filename = str(year_month) + '批量进货备份.xls'
    workbook = xlwt.Workbook(encoding='utf-8')
    style = xlwt.XFStyle()
    font = xlwt.Font()
    font.name = 'SimSun'
    style.font = font
    sheet = workbook.add_sheet('sheet1', cell_overwrite_ok=True)

    sheet.write(0, 0, '订单号')
    sheet.write(0, 1, '钢铁名称', style)
    sheet.write(0, 2, '宽度', style)
    sheet.write(0, 3, '长度', style)
    sheet.write(0, 4, '规格', style)
    sheet.write(0, 5, '重量', style)
    sheet.write(0, 6, '数量', style)
    sheet.write(0, 7, '单价(元/吨)', style)
    sheet.write(0, 8, '有票成本', style)
    sheet.write(0, 9, '无票成本', style)
    sheet.write(0, 10, '总价', style)
    sheet.write(0, 11, '围数', style)
    sheet.write(0, 12, '时间', style)

    i = 1
    for item in batch_list:
        sheet.write(i, 0, item.oid)
        if item.sid in steel_dict:
            sheet.write(i, 1, steel_dict[item.sid].name, style)
            sheet.write(i, 2, float(steel_dict[item.sid].wid_str), style)
            sheet.write(i, 3, float(steel_dict[item.sid].len_str), style)
            sheet.write(i, 4, float(steel_dict[item.sid].high_str), style)
        sheet.write(i, 5, float(item.weight))
        if int(item.number) > 0:
            sheet.write(i, 6, int(item.number))
        else:
            sheet.write(i, 6, '未开板', style)
        sheet.write(i, 7, float(item.unit_price))
        sheet.write(i, 8, float(item.cost_a))
        sheet.write(i, 9, float(item.cost_b))
        sheet.write(i, 10, float(item.total_price))
        sheet.write(i, 11, float(item.true_high))
        sheet.write(i, 12, str(item.batch_date))

        i += 1

    response = HttpResponse(mimetype='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    workbook.save(response)
    return response