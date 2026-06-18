import logging
from datetime import datetime

from odoo import fields

_logger = logging.getLogger(__name__)


def safe_list(val, log=False, field_name=None):
    """
    Ensure value is a list.

    Args:
        val: any value
        log (bool): log warning if invalid
        field_name (str): field name for logging

    Returns:
        list
    """
    if isinstance(val, list):
        return val
    if log and val not in (None, []):
        _logger.warning(f"{field_name or 'value'} expected list, got {type(val)}")
    return []


def safe_dict(val, log=False, field_name=None):
    """
    Ensure value is a dict.
    """
    if isinstance(val, dict):
        return val
    if log and val not in (None, {}):
        _logger.warning(f"{field_name or 'value'} expected dict, got {type(val)}")
    return {}


def safe_str(val):
    """
    Ensure value is string.
    """
    return val if isinstance(val, str) else ''


def safe_int(val, default=0):
    """
    Ensure value is int.
    """
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def safe_float(val, default=0.0):
    """
    Ensure value is float.
    """
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def safe_bool(val):
    """
    Ensure value is boolean.
    """
    return bool(val)


def safe_get(data, key, default=None):
    """
    Safe dict get (handles None dict).
    """
    if not isinstance(data, dict):
        return default
    return data.get(key, default)


def ensure_list_of_dicts(val, log=False, field_name=None):
    """
    Ensure list of dicts.
    Filters out invalid entries.
    """
    result = []
    for item in safe_list(val, log, field_name):
        if isinstance(item, dict):
            result.append(item)
        elif log:
            _logger.warning(f"{field_name or 'value'} contains non-dict item: {type(item)}")
    return result


def normalize_ids(ids):
    """
    Convert list/int/string IDs into comma-separated string.
    """
    if isinstance(ids, list):
        return ','.join(map(str, ids))
    return ids


def safe_dates(val):
    """
    Convert API string to Odoo datetime or date object.
    Handles both 'YYYY-MM-DD' and 'YYYY-MM-DDTHH:MM:SS'.

    Returns:
        datetime.datetime, datetime.date, or False
    """
    if not val:
        return False
    try:
        # Datetime with T or space
        dt = fields.Datetime.to_datetime(val)
        if dt.time() == datetime.min.time():
            # If time is 00:00:00 → treat as date
            return dt.date()
        return dt
    except Exception:
        try:
            # Try parsing as date only
            return datetime.strptime(val, "%Y-%m-%d").date()
        except Exception as e:
            _logger.warning(f"Invalid date/datetime value: {val} ({e})")
            return False


def process_dates_recursive(data):
    """
    Recursively traverse a dict, list of dicts, or Odoo One2many/M2M commands
    and convert any string that looks like a date/datetime to actual datetime objects.

    Args:
        data (dict/list/tuple): The input structure

    Returns:
        same structure with dates converted
    """
    if isinstance(data, dict):
        new_data = {}
        for k, v in data.items():
            new_data[k] = process_dates_recursive(v)
        return new_data
    elif isinstance(data, list):
        # Check if it is a list of commands [(0,0,vals), (0,0,vals)...]
        new_list = []
        for item in data:
            if isinstance(item, (list, tuple)) and len(item) == 3 and isinstance(item[2], dict):
                new_item = (item[0], item[1], process_dates_recursive(item[2]))
                new_list.append(new_item)
            else:
                new_list.append(process_dates_recursive(item))
        return new_list
    elif isinstance(data, str):
        # Try to parse datetime strings automatically
        if "T" in data or "-" in data:
            dt = safe_dates(data)
            if dt:
                return dt
        return data
    else:
        return data
