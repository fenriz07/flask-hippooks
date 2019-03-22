from flask import request, url_for
from hipcooks import app, models, utils
from datetime import date
from dateutil.relativedelta import relativedelta as rd
from sqlalchemy import not_


def apply_filters(request_args, filters, query):
    for (filter_name, filter_func) in filters.items():
        filter_arg = 'filter_' + filter_name
        if filter_arg in request_args:
            query = filter_func(request_args[filter_arg], query)
    return query


def replace_filters(request_args, **kwargs):
    stripped_args = {arg: value for arg, value in request_args.items()
                     if not arg.startswith('filter_')}
    for arg, value in kwargs.items():
        stripped_args['filter_' + arg] = value
    return stripped_args


@app.template_global()
def this_url_with_filters(**kwargs):
    args = replace_filters(request.args, **kwargs)
    return url_for(request.endpoint, **args)


def _away(now, start_delta, end_delta):
    if now is None:
        now = date.today()
    return {'date_begin':
            utils.date_string(now + start_delta),
            'date_end':
            utils.date_string(now + end_delta)}


@app.template_global()
def weeks_away(weeks, now=None):
    return _away(now, rd(weeks=weeks), rd(weeks=weeks+1))


@app.template_global()
def months_away(months, now=None):
    return _away(now, rd(months=months), rd(months=months+1))


@app.template_global()
def years_back(years_ago, months=0, month=None, now=None):
    if now is None:
        now = date.today()
    offset = rd(years=-years_ago, months=months, month=month, day=1)
    return _away(now, offset, offset+rd(months=1))


@app.template_global()
def years_back_date(years_ago, months=0, month=None, now=None):
    if now is None:
        now = date.today()
    return now + rd(years=-years_ago, months=months, month=month, day=1)


@app.template_global()
def years_back_to_start(now=None):
    if now is None:
        now = date.today()
    return range(0, now.year-_hipcooks_start_year+1)
_hipcooks_start_year = 2003


def _schedule_date_begin(date_string, query):
    return query.filter(
        models.Schedule.date >= utils.from_date_string(date_string))


def _schedule_date_end(date_string, query):
    return query.filter(
        models.Schedule.date < utils.from_date_string(date_string))


def _schedule_is_public(public, query):
    if public:
        return query.filter(models.Schedule.is_public)
    else:
        return query


def _schedule_is_private(private, query):
    if private:
        return query.filter(not_(models.Schedule.is_public))
    else:
        return query


def _schedule_campus(campus_id, query):
    return query.join(models.Campus).filter(models.Campus.id == campus_id)


schedule_filters = {
    'date_begin': _schedule_date_begin,
    'date_end': _schedule_date_end,
    'public': _schedule_is_public,
    'private': _schedule_is_private,
    'campus': _schedule_campus,
}
