#!/usr/bin/env python
# -*- coding: utf-8 -*-


from django.http import HttpResponse
import json


def dump_response(resp):
    return HttpResponse(json.dumps(resp), content_type="application/json")
