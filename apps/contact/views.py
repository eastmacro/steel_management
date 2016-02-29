#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from django.contrib.auth.decorators import permission_required
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from apps.contact.models import ContactBook, ContactBookForm, ContactType, ContactTypeForm
from datetime import datetime
from django.shortcuts import get_object_or_404
from apps.utils.page_helper import list_by_page
from django.http import HttpResponse
import json
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

DATE_PATTERN = '%Y-%m-%d'


@permission_required('contact.change_contact')
def list(request):
    data = {}
    
    id = request.GET.get('id', None)
    if id:
        id = int(id)
        data['id'] = id
    
    contacts = ContactBook.objects.all().order_by('-create_time')
    data['contacts'] = contacts

    type_list = ContactType.objects.all()
    data['contact_types'] = type_list
    type_dict = {}
    for item in type_list:
        type_dict[item.id] = item

    name = request.GET.get('name', None)
    if name:
        data['name'] = name
        contacts = contacts.filter(name__contains=name)
    
    type = request.GET.get('type', None)
    if type:
        type = int(type)
        contacts = contacts.filter(type=type)
        data['type'] = type

    remark = request.GET.get('remark', None)
    if remark:
        contacts = contacts.filter(remark__contains=remark)
        data['remark'] = remark

    count = contacts.count()
    contact_list = list_by_page(request, contacts)
    item_list = []
    for item in contact_list:
        item_list.append({
            'contact': item,
            'type': type_dict[int(item.type)],
        })
    data['count'] = count
    data['contact_list'] = contact_list
    data['item_list'] = item_list
    return render_to_response(
        'contact/list.html',
        data,
        context_instance=RequestContext(request)
    )


@permission_required('contact.change_contact')
def edit(request):
    data = {}
    id = request.GET.get('id', None)
    contact = None
    type_list = ContactType.objects.all()
    data['contact_types'] = type_list
    if id:
        id = int(id)
        contact = get_object_or_404(ContactBook, id=id)
        data['contact'] = contact
        print contact
        data['id'] = id
        data['type'] = int(contact.type)
    if request.method == 'POST':
        post = request.POST.copy()
        
        create_time = datetime.now()
        modify_time = create_time
        
        if contact:
            create_time = contact.create_time
            modify_time = datetime.now()
        
        post.update({
            'status': 1,
            'create_time': create_time,
            'modify_time': modify_time,
        })

        form = ContactBookForm(post, instance=contact)
        data['form'] = form
        if form.is_valid():
            current_contact = form.save()
            return HttpResponseRedirect('/contact/?id=%d' % current_contact.id)
        else:
            print form.errors
            return render_to_response(
                'contact/edit.html',
                data,
                context_instance=RequestContext(request)
            )
    else:
        form = ContactBookForm(instance=contact)
        data['form'] = form
        return render_to_response(
            'contact/edit.html',
            data,
            context_instance=RequestContext(request)
        )


@permission_required('contact.change_contact')
def contact_type_list(request):
    data = {}
    contact_types = ContactType.objects.all()

    type = request.GET.get('type', None)
    if type:
        contact_types = contact_types.filter(type__contains=type)
        data['type'] = type


    count = contact_types.count()
    contact_list = list_by_page(request, contact_types)
    data['count'] = count
    data['contact_list'] = contact_list
    return render_to_response(
        'contact/type_list.html',
        data,
        context_instance=RequestContext(request)
    )


@permission_required('contact.change_contact')
def contact_type_edit(request):
    data = {}
    id = request.GET.get('id', None)
    contact_type = None

    if id:
        id = int(id)
        contact_type = get_object_or_404(ContactType, id=id)
        data['contact_type'] = contact_type
        #print contact_type
        data['id'] = id

    if request.method == 'POST':
        post = request.POST.copy()

        form = ContactTypeForm(post, instance=contact_type)
        data['form'] = form
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/contact/type/')
        else:
            print form.errors
            return render_to_response(
                'contact/type_edit.html',
                data,
                context_instance=RequestContext(request)
            )
    else:
        form = ContactTypeForm(instance=contact_type)
        data['form'] = form
        return render_to_response(
            'contact/type_edit.html',
            data,
            context_instance=RequestContext(request)
        )