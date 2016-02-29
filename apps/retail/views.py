#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from django.contrib.auth.decorators import permission_required
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from apps.retail.models import Retail, RetailForm, RetailOrder, RetailOrderForm
from apps.steel.models import Steel
from apps.utils.page_helper import list_by_page
from django.utils import timezone
from datetime import datetime, date, timedelta
from apps.supplier.models import Supplier
from django.db.models import Max
from django.shortcuts import get_object_or_404
import xlwt
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

DATE_PATTERN = '%Y-%m-%d'


@permission_required('retail.change_retail')
def list(request):
    data = {}
    steels = Steel.objects.all().order_by('-create_time')
    
    steel_dict = {}
    for item in steels:
        steel_dict[item.id] = item
    
    data['steels'] = steels
    retail_orders = RetailOrder.objects.all().order_by('-create_time')
    data['retail_orders'] = retail_orders
    retails = Retail.objects.all()
    data['retails'] = retails
    suppliers = Supplier.objects.all()
    supplier_dict = {}
    for item in suppliers:
        supplier_dict[int(item.id)] = item
    
    data['suppliers'] = suppliers
    
    id = request.GET.get('id', None)
    if id:
        id = int(id)
        data['id'] = id

    from_date = request.GET.get('from_date', None)
    if from_date:
        from_date = datetime.strptime(from_date, DATE_PATTERN).date()
        retail_orders = retail_orders.filter(order_day__gte=from_date)
        data['from_date'] = from_date
    
    end_date = request.GET.get('end_date', None)
    if end_date:
        end_date = datetime.strptime(end_date, DATE_PATTERN).date()
        retail_orders = retail_orders.filter(order_day__lte=end_date)
        data['end_date'] = end_date
    
    oid = request.GET.get('oid', None)
    if oid:
        retail_orders = retail_orders.filter(oid__contains=oid)
        data['oid'] = oid
    
    sid = request.GET.get('sid', None)
    if sid:
        sid = int(sid)
        retails = retails.filter(sid=sid)
        order_id_list = []
        for item in retails:
            order_id_list.append(item.oid)
        retail_orders = retail_orders.filter(oid__in=order_id_list)
        data['sid'] = sid

    supplier_id = request.GET.get('supplier_id', None)
    if supplier_id:
        supplier_id = int(supplier_id)
        retail_orders = retail_orders.filter(supplier_id=supplier_id)
        data['supplier_id'] = supplier_id

    supplier_name = request.GET.get('supplier_name', None)
    if supplier_name:
        temp_suppliers = suppliers.filter(name__contains=supplier_name)
        temp_supplier_list = []
        if temp_suppliers.exists():
            for item in temp_suppliers:
                temp_supplier_list.append(item.id)

        retail_orders = retail_orders.filter(supplier_id__in=temp_supplier_list)
        data['supplier_name'] = supplier_name

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
            export_orders = retail_orders.filter(order_day__gte=last_month_first_day)
            year_month += last_month_first_day.strftime('%Y%m%d') + '_'
            
            if not end_date:
                last_month_last_day = date(datetime.today().year, datetime.today().month, 1) - timedelta(days=1)
                export_orders = retail_orders.filter(order_day__lte=last_month_last_day)
                year_month += last_month_last_day.strftime('%Y%m%d')
            else:
                year_month += end_date.strftime('%Y%m%d')
        else:
            if end_date:
                year_month += from_date.strftime('%Y%m%d') + '_'
                year_month += end_date.strftime('%Y%m%d')
                export_orders = retail_orders
            else:
                year_month += from_date.strftime('%Y%m%d') + '_'
                export_orders = retail_orders.filter(order_day__lte=datetime.today())
                year_month += datetime.today().strftime('%Y%m%d')
            #print last_month_last_day
        return order_export(request, export_orders, steel_dict, supplier_dict, year_month)

    retail_order_list = list_by_page(request, retail_orders)
    data['retail_order_list'] = retail_order_list
    retail_list = []
    for item in retail_order_list:
        temp_dict = {}
        temp_dict['retail'] = item
        if int(item.supplier_id) in supplier_dict:
            temp_dict['supplier'] = supplier_dict[int(item.supplier_id)]
        else:
            temp_dict['supplier'] = ''
        
        check_time = item.create_time + timedelta(minutes=5)
        if check_time < datetime.now():
            temp_dict['check_time'] = 0
        else:
            temp_dict['check_time'] = 1
        retail_list.append(temp_dict)

    data['retail_list'] = retail_list

    return render_to_response(
        'retail/order_list.html',
        data,
        context_instance=RequestContext(request)
    )


@permission_required('retail.change_retail')
def add(request):
    data = {}
    order = None
    num = [0, 1, 2, 3, 4]
    data['num'] = num
    steels = Steel.objects.filter(status=1)
    data['steels'] = steels
    suppliers = Supplier.objects.filter(status=1)
    data['suppliers'] = suppliers
    order_day = date.today()
    data['order_day'] = order_day
    oid = datetime.now().strftime('%Y%m%d%H%M%S')
    oid = str(oid) + '_2'
    data['oid'] = oid
    if request.method == 'POST':
        post = request.POST.copy()
        supplier_id = post.get('supplier_id', None)

        i = 0
        oid = post.get('oid', None)
        #print oid
        order_list = []
        order_total_price = 0.0
        if not supplier_id:
            form = RetailOrderForm(instance=order)
            data['form'] = form
            return render_to_response(
                'retail/add.html',
                data,
                context_instance=RequestContext(request)
            )
        now_time = datetime.now()
        while i < 5:
            temp_retail = Retail()
            sid = 'sid_' + str(i)
            unit_price = 'unit_price_' + str(i)
            number = 'number_' + str(i)
            total_price = 'total_price_' + str(i)
            temp_sid = post.get(sid, None)
            temp_number = post.get(number, None)
            temp_unit_price = post.get(unit_price, None)
            temp_total_price = post.get(total_price, None)
            if temp_sid:
                #print temp_sid
                pass
            else:
                break
            if temp_number:
                temp_number = int(temp_number)
            if temp_unit_price:
                temp_unit_price = float(temp_unit_price)
            
            temp_retail.oid = oid
            #print temp_retail.oid
            temp_retail.sid = temp_sid
            temp_retail.number = temp_number
            temp_retail.unit_price = temp_unit_price
            check_total_price = float(temp_number) * float(temp_unit_price)
            if check_total_price == temp_total_price:
                temp_retail.total_price = temp_total_price
            else:
                temp_retail.total_price = check_total_price
            temp_retail.status = 1
            temp_retail.create_time = now_time
            order_list.append(temp_retail)
            i = i + 1
            order_total_price = order_total_price + float(check_total_price)
        #print order_list
        print Retail.objects.bulk_create(order_list)
        check = 1
        if check:
            pass
        else:
            form = RetailOrderForm(instance=order)
            data['form'] = form
            return render_to_response(
                'retail/add.html',
                data,
                context_instance=RequestContext(request)
            )

        if order_total_price > 0.0:
            order = RetailOrder()
            order.supplier_id = supplier_id
            order.oid = oid
            order.order_day = date.today()
            order.total_price = order_total_price
            order.create_time = now_time
            order.modify_time = now_time
            order.status = 1
            order.save()
            print order.oid
            current_retails = Retail.objects.filter(oid=order.oid)
            if current_retails.exists():
                for item in current_retails:
                    temp_steel = get_object_or_404(Steel, id=item.sid)
                    if temp_steel.status == 1:
                        pass
                    else:
                        return False
                    temp_steel.retail_number = int(temp_steel.retail_number) + int(item.number)
                    temp_steel.save()
            else:
                return False
            return HttpResponseRedirect('/retail/?id=%d' % int(order.id))
        else:
            print form.errors
            form = RetailOrderForm(post, instance=order)
            data['form'] = form
            return render_to_response(
                'retail/add.html',
                data,
                context_instance=RequestContext(request)
            )
    else:
        form = RetailOrderForm(instance=order)
        data['form'] = form
        return render_to_response(
            'retail/add.html',
            data,
            context_instance=RequestContext(request)
        )


@permission_required('retail.change_retail')
def edit(request):
    data= {}
    retail = None
    
    id = request.GET.get('id', None)
    if id:
        pass
    else:
        return HttpResponseRedirect(
            '/retail/'
        )
    id = int(id)
    retail = get_object_or_404(Retail, id=id)
    origin_retail = retail

    check_time = origin_retail.create_time + timedelta(minutes=5)
    if check_time > datetime.now():
        pass
    else:
        return HttpResponseRedirect(
            '/retail/'
        )
    data['retail'] = retail
    steels = Steel.objects.filter(status=1)
    data['steels'] = steels
    origin_number = origin_retail.number
    origin_steel = get_object_or_404(Steel, id=origin_retail.sid)

    if request.method == 'POST':
        post = request.POST.copy()
        sid = post.get('sid', None)
        number = post.get('number', 0)
        unit_price = post.get('unit_price', 0.0)
        if not sid or unit_price == 0.0 or number == 0:
            form = RetailForm(post, instance=retail)
            data['form'] = form
            return render_to_response(
                'retail/edit.html',
                data,
                context_instance=RequestContext(request)
            )
        oid = origin_retail.oid
        order = get_object_or_404(RetailOrder, oid=oid)
        order.total_price = float(order.total_price) - float(origin_retail.total_price)
        order.save()
        order = get_object_or_404(RetailOrder, oid=oid)
        print order.total_price
        current_total_price = float(number) * float(unit_price)
        order.total_price = float(order.total_price) + float(current_total_price)
        print order.total_price
        order.modify_time = datetime.now()
        order.save()
        post.update({
            'oid': oid,
            'total_price': current_total_price,
            'status': 1,
            'create_time': origin_retail.create_time
        })
        form = RetailForm(post, instance=origin_retail)
        data['form'] = form
        if form.is_valid():
            current_retail = form.save()
            origin_steel.retail_number = int(origin_steel.retail_number) - int(origin_number)
            #print origin_steel.retail_number
            origin_steel.save()
            
            current_steel = get_object_or_404(Steel, id=current_retail.sid)
            current_steel.retail_number = int(current_steel.retail_number) + int(current_retail.number)
            #print current_steel.retail_number
            current_steel.save()
            return HttpResponseRedirect(
                '/retail/?id=%d' % int(origin_retail.oid)
            )
        else:
            print form.errors
            return render_to_response(
                'retail/edit.html',
                data,
                context_instance=RequestContext(request)
            )

    else:
        form = RetailForm(instance=retail)
        data['form'] = form
        return render_to_response(
            'retail/edit.html',
            data,
            context_instance=RequestContext(request)
        )


@permission_required('retail_order.change_retail_order')
def order_edit(request):
    data = {}
    order = None
    oid = request.GET.get('oid', None)
    if oid:
        order = get_object_or_404(RetailOrder, oid=oid)
        data['order'] = order
        data['oid'] = oid
    suppliers = Supplier.objects.all()
    data['suppliers'] = suppliers
    if request.method == 'POST':
        post = request.POST.copy()
        supplier_id = post.get('supplier_id', None)
        if supplier_id:
            supplier_id = int(supplier_id)
        else:
            form = RetailOrderForm(instance=order)
            data['form'] = form
            return render_to_response(
                'retail/order_edit.html',
                data,
                context_instance=RequestContext(request)
            )

        supplier = None
        supplier = get_object_or_404(Supplier, id=supplier_id)
        if supplier:
            order.supplier_id = supplier_id
            order.save()
            return HttpResponseRedirect(
                '/retail/?id=%d' % int(order.oid)
            )
        
    else:
        print form.errors
        form = RetailOrderForm(instance=order)
        data['form'] = form
        return render_to_response(
            'retail/order_edit.html',
            data,
            context_instance=RequestContext(request)
        )

@permission_required('order.change_order')
def order_export(request, order_list, steel_dict, supplier_dict, year_month):
    oid_list = []
    for item in order_list:
        oid_list.append(item.oid)

    retails = Retail.objects.filter(oid__in=oid_list)
    retail_dict = {}
    for item in retails:
        if item.oid in retail_dict:
            temp_list = retail_dict[item.oid]
            temp_list.append(item)
            retail_dict[item.oid] = temp_list
        else:
            temp_list = []
            temp_list.append(item)
            retail_dict[item.oid] = temp_list

    print retail_dict

    filename = str(year_month) + '散货订单备份.xls'
    workbook = xlwt.Workbook(encoding='utf-8')
    style = xlwt.XFStyle()
    font = xlwt.Font()
    font.name = 'SimSun'
    style.font = font
    sheet = workbook.add_sheet('sheet1', cell_overwrite_ok=True)
    i = 0
    for item in order_list:
        sheet.write(i, 0, '订单号')
        sheet.write(i, 1, '供应商', style)
        sheet.write(i, 2, '总价', style)
        sheet.write(i, 3, '时间', style)
        i += 1
        sheet.write(i, 0, item.oid)
        sheet.write(i, 1, supplier_dict[item.supplier_id].name, style)
        sheet.write(i, 2, float(item.total_price))
        sheet.write(i, 3, str(item.order_day), style)
        i += 1
        sheet.write(i, 0, '货品', style)
        sheet.write(i, 1, '数量', style)
        sheet.write(i, 2, '单价', style)
        sheet.write(i, 3, '总价', style)
        i += 1
                               
        for term in retail_dict[item.oid]:
            sheet.write(i, 0, steel_dict[term.sid].name)
            sheet.write(i, 1, int(term.number))
            sheet.write(i, 2, float(term.unit_price))
            sheet.write(i, 3, float(term.total_price))
                               
        i += 2

    response = HttpResponse(mimetype='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    workbook.save(response)
    return response