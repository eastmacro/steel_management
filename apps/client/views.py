#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from django.contrib.auth.decorators import permission_required
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from apps.client.models import Client, ClientForm
from datetime import datetime
from django.shortcuts import get_object_or_404
from apps.utils.page_helper import list_by_page
from django.http import HttpResponse
import json
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

DATE_PATTERN = '%Y-%m-%d'


@permission_required('client.change_client')
def list(request):
    data = {}
    clients = Client.objects.all().order_by('-create_time')
    data['clients'] = clients
    id = request.GET.get('id', None)
    if id:
        id = int(id)
        data['id'] = id
        clients = clients.filter(id=id)

    name = request.GET.get('name', None)
    if name:
        data['name'] = name
        clients = clients.filter(name__contains=name)

    status = request.GET.get('status', None)
    if status:
        status = int(status)
        clients = clients.filter(status=status)
        data['status'] = status

    count = clients.count()
    client_list = list_by_page(request, clients)
    data['count'] = count
    data['client_list'] = client_list
    return render_to_response(
        'client/list.html',
        data,
        context_instance=RequestContext(request)
    )


@permission_required('client.change_client')
def edit(request):
    data = {}
    id = request.GET.get('id', None)
    client = None
    if id:
        id = int(id)
        client = get_object_or_404(Client, id=id)
        data['client'] = client
        #print client
        data['id'] = id

    if request.method == 'POST':
        post = request.POST.copy()
        
        create_time = datetime.now()
        modify_time = create_time
        
        if client:
            create_time = client.create_time
            modify_time = datetime.now()
    
        post.update({
            'status': 1,
            'create_time': create_time,
            'modify_time': modify_time,
        })

        form = ClientForm(post, instance=client)
        data['form'] = form
        if form.is_valid():
            current_client = form.save()
            print current_client
            return HttpResponseRedirect('/client/?id=%d' % current_client.id)
        else:
            print form.errors
            return render_to_response(
                'client/edit.html',
                data,
                context_instance=RequestContext(request)
            )
    else:
        form = ClientForm(instance=client)
        data['form'] = form
        return render_to_response(
            'client/edit.html',
            data,
            context_instance=RequestContext(request)
        )


def get_client(request):
    resp_dict = {
        'code': 0,
        'client_list': None
    }
    client_list = []
    name = request.POST.get('client_name', None)
    if name:
        clients = Client.objects.filter(name__contains=name).filter(status=1).order_by('-create_time')
        if clients.exists():
            for client in clients:
                print client.name
                client_list.append({
                    'name': client.name,
                })
            resp_dict['code'] = 1
            resp_dict['client_list'] = client_list
    
        return HttpResponse(
            json.dumps(resp_dict),
            content_type='application/json'
        )