# -*- coding: utf-8 -*-
from odoo.http import request
from datetime import datetime, timezone
import pytz
import logging

_logger = logging.getLogger(__name__)

def get_allowed_companies(user_id, acids):
    user_companies = user_id.partner_id.x_studio_associated_company.ids
    allowed_companies = [0]
    if acids:
        current_acids = acids.split(",")
        for c in current_acids:
            if int(c) in user_companies:
                allowed_companies.append(int(c))
    
    return tuple(allowed_companies)

def to_int(value):
    if value:
        return int(value)
    else:
        return value

def get_default_int_value(data,compare_value,default_value):
    if data == compare_value:
        return default_value
    else:
        return int(data)

def check_date_format(value, format):
    result = True
    try:
        temp = datetime.strptime(value,format)
    except Exception as e:
        result = False

    return result

def timezone_adjust(value, format, adj):
    temp = datetime.strptime(value,format) 
    date = value
    if temp:
        date = datetime.fromisoformat(temp.isoformat() + adj).astimezone(pytz.timezone('UTC')).strftime(format)
    return date

def timezone_adjust_reverse(value, format, adj):
    temp = datetime.strptime(value,format) 
    date = value
    if temp:
        original_date = datetime.fromisoformat(temp.isoformat() + adj)
        original_timestamp = datetime.timestamp(original_date)
        adjusted_date = datetime.fromisoformat(temp.isoformat() + adj).replace(tzinfo=timezone.utc)
        adjusted_timestamp = datetime.timestamp(adjusted_date)
        diff = adjusted_timestamp - original_timestamp
        final_date = datetime.fromtimestamp(adjusted_timestamp + diff)
        date = final_date.strftime(format)
    return date

def has_access_right(partner_id, access_right):
    result = False
    for access in partner_id.x_studio_individual_type:
        if access.x_name == access_right:
            result = True

    return result

