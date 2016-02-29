#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from django.contrib.auth.decorators import permission_required
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from apps.supplier.models import Supplier, SupplierForm
from datetime import datetime
from django.shortcuts import get_object_or_404
from apps.utils.page_helper import list_by_page
from django.http import HttpResponse
import json
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

DATE_PATTERN = '%Y-%m-%d'


@permission_required('supplier.change_supplier')
def list(request):
    data = {}
    suppliers = Supplier.objects.all().order_by('-create_time')
    data['suppliers'] = suppliers
    
    id = request.GET.get('id', None)
    if id:
        id = int(id)
        data['id'] = id
        suppliers = suppliers.filter(id=id)

    name = request.GET.get('name', None)
    if name:
        data['name'] = name
        suppliers = suppliers.filter(name__contains=name)

    status = request.GET.get('status', None)
    if status:
        status = int(status)
        suppliers = suppliers.filter(status=status)
        data['status'] = status

    count = suppliers.count()
    supplier_list = list_by_page(request, suppliers)
    data['count'] = count
    data['supplier_list'] = supplier_list
    return render_to_response(
        'supplier/list.html',
        data,
        context_instance=RequestContext(request)
    )


@permission_required('supplier.change_supplier')
def edit(request):
    data = {}
    id = request.GET.get('id', None)
    supplier = None
    if id:
        id = int(id)
        supplier = get_object_or_404(Supplier, id=id)
        data['supplier'] = supplier
        print supplier
        data['id'] = id

    if request.method == 'POST':
        post = request.POST.copy()
        
        create_time = datetime.now()
        modify_time = create_time
        
        if supplier:
            create_time = supplier.create_time
            modify_time = datetime.now()
    
        post.update({
            'status': 1,
            'create_time': create_time,
            'modify_time': modify_time,
        })

        form = SupplierForm(post, instance=supplier)
        data['form'] = form
        if form.is_valid():
            current_supplier = form.save()
            return HttpResponseRedirect('/supplier/?id=%d' % current_supplier.id)
        else:
            print form.errors
            return render_to_response(
                'supplier/edit.html',
                data,
                context_instance=RequestContext(request)
            )
    else:
        form = SupplierForm(instance=supplier)
        data['form'] = form
        return render_to_response(
            'supplier/edit.html',
            data,
            context_instance=RequestContext(request)
        )


def get_supplier(request):
    resp_dict = {
        'code': 0,
        'supplier_list': None
    }
    print "ok"
    supplier_list = []
    name = request.POST.get('supplier_name', None)
    if name:
        suppliers = Supplier.objects.filter(name__contains=name).filter(status=1).order_by('-create_time')
        if suppliers.exists():
            for supplier in suppliers:
                print supplier.name
                supplier_list.append({
                    'name': supplier.name,
                })
            resp_dict['code'] = 1
            resp_dict['supplier_list'] = supplier_list

    return HttpResponse(
        json.dumps(resp_dict),
        content_type='application/json'
    )