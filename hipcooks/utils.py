from hipcooks import app
from flask import session, render_template_string
from PIL import Image
import datetime
import os
import errno
import re
from jinja2 import (evalcontextfilter, evalcontextfunction, Markup, escape,
                    Environment, FileSystemLoader)
import bbcode
from dateutil import relativedelta
import calendar
import io
import csv
import base64


def file_upload(file, name, subdir):
    """
    Saves a werkzeug FileStorage object 'file' as 'name' in
    'subdir' under the upload folder
    """
    pic_file = path_on_disk(subdir, name)
    file.save(pic_file)
    return name


def create_thumbnail(input_file, output_filename, size=(128, 128)):
    im = Image.open(input_file)
    im.thumbnail(size)
    output_file = path_on_disk('thumbnails', output_filename)
    im.save(output_file, "JPEG")
    return output_filename


def path_on_disk(*path_fragments):
    dir = os.path.join(app.config["UPLOAD_FOLDER"],
                       *path_fragments[:-1])
    try:
        os.makedirs(dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    return os.path.join(app.config["UPLOAD_FOLDER"],
                        *path_fragments)


def url_path(*path_fragments):
    return '/{}/{}'.format(
        app.config["UPLOAD_FOLDER_NAME"],
        '/'.join(path_fragments)
    )

app.template_global("rdelta")(relativedelta.relativedelta)
app.template_global("tdelta")(datetime.timedelta)
app.template_global("SU")(relativedelta.SU)
app.template_global("MO")(relativedelta.MO)


@app.template_filter('thumbnail_path')
def template_url_path(image_name):
    return url_path('thumbnails', image_name)


@app.template_filter()
@evalcontextfilter
def nl2li(eval_ctx, value):
    result = u'\n\n'.join(u'<li><span>{}</span></li>'.format(p)
                          for p in _paragraph_re.split(escape(value.strip())))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result
_paragraph_re = re.compile(r'(?:\s*(?:\r|\n))+')


@app.template_global('date_string')
def date_string(date):
    return date.strftime('%Y-%m-%d')


@app.template_global('from_date_string')
def from_date_string(date_string):
    return datetime.datetime.strptime(date_string, '%Y-%m-%d').date()


@app.template_global('eval')
@evalcontextfunction
def evaluate_string(eval_ctx, string):
    return Markup(render_template_string(string, context=eval_ctx))


def csv_from_rows(rows):
    fptr = io.BytesIO()
    csvwriter = csv.writer(fptr)
    for row in rows:
        csv_row = []
        for cell in row:
            try:
                csv_row.append(cell.encode("utf-8", "ignore"))
            except:
                csv_row.append(cell)

        csvwriter.writerow(csv_row)

    return fptr.getvalue()


# Emulates the rather strange "changing date header" from the original site.
def schedule_date_range(start, end):
    dates = []
    show_dates = True
    if start is None or end is None or (end - start).days > 365:
        range_view = 'years'

        for year in range(2003, datetime.date.today().year + 1):
            dt = datetime.date(year=year, month=1, day=1)
            dates.append((str(year),
                         [dt, dt + relativedelta.relativedelta(years=1)]))
    elif (end - start).days < 32:
        if (end - start).days == 7:
            range_view = 'week'
        else:
            range_view = 'month'
        show_dates = False

        dt = start
        while dt < end:
            next_date = dt + relativedelta.relativedelta(days=1)
            dates.append((dt.strftime("%B %-d"), [dt, next_date]))
            dt = next_date
    else:
        range_view = 'single_year'

        dt = start + relativedelta.relativedelta(day=1)
        while dt < end:
            month_end = dt + relativedelta.relativedelta(months=1)
            dates.append((dt.strftime("%B %Y"), [dt, month_end]))
            dt = month_end
    return dates, show_dates, range_view


def date_back(start, end):
    if start is None or end is None or (end - start).days > 364:
        return None

    if (end - start).days < calendar.monthrange(start.year, start.month)[1]:
        return (start.strftime("%B %Y"), [start.replace(day=1), start.replace(day=calendar.monthrange(start.year, start.month)[1]) + datetime.timedelta(days=1)], )
    else:
        return (start.strftime("%Y"), [start.replace(day=1, month=1), start.replace(day=1, month=1) + datetime.timedelta(days=365)],)


def format_time_range(start_time, end_time):
    noon = datetime.time(hour=12)
    start_is_am = start_time < noon
    end_is_am = end_time < noon
    start = format(
        start_time,
        "%-I" +
        (":%M" if start_time.minute != 0 else "") +
        ("%p" if start_is_am != end_is_am else "")
    )
    end = format(
        end_time,
        "%-I" + (":%M" if end_time.minute != 0 else "") + "%p"
    )
    return "{}-{}".format(start, end).lower()


def include_file(loader, env):
    def curried(name):
        return Markup(loader.get_source(env, name)[0])
    return curried


def nonHTMLJinjaEnv():
    loader = FileSystemLoader([os.path.join(os.path.dirname(__file__), "../static"),
                               os.path.join(os.path.dirname(__file__), "templates")])
    env = Environment(loader=loader)
    env.globals['include_file'] = include_file(loader, env)
    return env


def base_64_encoded_file(filename):
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), filename), 'r') as f:
        return base64.b64encode(f.read())
