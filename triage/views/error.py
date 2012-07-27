from pyramid.view import view_config
from pyramid.renderers import render_to_response
from pyramid.httpexceptions import HTTPFound, HTTPNotFound

from triage.models import Error, Comment, Tag, User, ErrorInstance, Project
from triage.util import GithubLinker
from time import time
from os import path

import logging
import datetime
import calendar

#fixme
import random

def get_errors(request, fetch_recent=False):
    project = get_selected_project(request)

    log = logging.getLogger(__name__)

    search = request.GET.get('search', '')
    show = request.GET.get('show', 'open')  # open, resolved, mine
    tags = request.GET.getall('tags')
    order_by = request.GET.get('order_by', 'date')
    direction = request.GET.get('direction', 'desc')
    start = int(request.GET.get('start', 0))
    time_latest = int(request.GET.get('timelatest', time()))

    if show not in ['open', 'resolved', 'mine']:
        show = 'open'

    if show == 'open':
        errors = project.errors().active()
    elif show == 'resolved':
        errors = project.errors().resolved()
    elif show == 'mine':
        errors = project.errors().active().filter(claimedby=request.user)

    if search:
        errors.search(search)

    if tags:
        errors.filter(tags__in=tags)

    if fetch_recent:
        return errors.filter(timelatest__gt=time_latest).count()

    errors.filter(timelatest__lte=time_latest)

    order_map = {
        'date': 'timelatest',
        'occurances': 'count',
        'activity': 'comments'
    }

    if order_by in order_map:
        order_by = order_map[order_by]
    else:
        order_by = 'timelatest'

    if direction == 'desc':
        order_by = '-' + order_by

    errors.order_by(order_by)

    pagedErrors = errors.skip(start).limit(20)

    log.debug(errors.count())
    log.debug(pagedErrors.count())

    return list(pagedErrors)


@view_config(route_name='error_list', permission='authenticated', xhr=True, renderer='errors/list.html')
def error_list(request):
    return {
        'selected_project': get_selected_project(request),
        'errors': get_errors(request),
        'basename': path.basename
    }


@view_config(route_name='error_list', permission='authenticated', xhr=False, renderer='error-list.html')
def error_page(request):
    project = get_selected_project(request)

    search = request.GET.get('search', '')
    show = request.GET.get('show', 'open')  # open, resolved, mine
    order_by = request.GET.get('order_by', 'date')
    direction = request.GET.get('direction', 'desc')

    if show not in ['open', 'resolved', 'mine']:
        show = 'open'

    errors = get_errors(request)

    counts = {
        'open': project.errors().active().filter(seenby__ne=request.user).count(),
        'resolved': project.errors().resolved().filter(seenby__ne=request.user).count(),
        'mine': project.errors().active().filter(claimedby=request.user).count()
    }

    return {
        'search': search,
        'errors': errors,
        'selected_project': project,
        'available_projects': Project.objects(),
        'show': show,
        'order_by': order_by,
        'direction': direction,
        'counts': counts,
        'basename': path.basename
    }


@view_config(route_name='error_list_changes', permission='authenticated', xhr=True, renderer='json')
def error_list_changes(request):
    return get_errors(request, True)


@view_config(route_name='error_view', permission='authenticated')
def view(request):
    project = get_selected_project(request)

    error_id = request.matchdict['id']
    try:
        error = Error.objects().with_id(error_id)
    except:
        return HTTPNotFound()
    if request.user not in error.seenby:
        error.seenby.append(request.user)
        error.save()

    instances = ErrorInstance.objects(hash=error.hash)[:10]

    params = {
        'error': error,
        'selected_project': project,
        'available_projects': Project.objects(),
        'instances': instances,
        'github': GithubLinker(project.github),
        'trend': get_trend(error)
    }

    try:
        template = 'error-view/' + str(error['language']).lower() + '.html'
        return render_to_response(template, params)
    except:
        template = 'error-view/generic.html'
        return render_to_response(template, params)

@view_config(route_name='error_toggle_claim', permission='authenticated', xhr=True, renderer='json')
def toggle_claim(request):
    error_id = request.matchdict['id']
    project = get_selected_project(request)

    try:
        error = Error.objects(project=project.token).with_id(error_id)
        if error.claimedby and error.claimedby != request.user:
            return {'type': 'failure'}

        error.claimedby = None if error.claimedby else request.user
        error.save()

        return {'type': 'success'}
    except:
        return {'type': 'failure'}


@view_config(route_name='error_toggle_resolve', permission='authenticated', xhr=True, renderer='json')
def toggle_resolve(request):
    error_id = request.matchdict['id']
    project = get_selected_project(request)

    try:
        error = Error.objects(project=project.token).with_id(error_id)
        if error.hiddenby and error.hiddenby != request.user:
            return {'type': 'failure'}

        error.hiddenby = None if error.hiddenby else request.user
        error.save()

        return {'type': 'success'}
    except:
        return {'type': 'failure'}


@view_config(route_name='error_tag_add', permission='authenticated', xhr=True, renderer='json')
def tag_add(request):
    tag = request.matchdict['tag']
    error_id = request.matchdict['id']
    project = get_selected_project(request)

    try:
        error = Error.objects(project=project.token).with_id(error_id)
        if tag in error.tags:
            return {'type': 'failure'}

        error.tags.append(tag)
        error.save()
        Tag.create(tag).save()
        return {'type': 'success'}
    except:
        return {'type': 'failure'}


@view_config(route_name='error_tag_remove', permission='authenticated', xhr=True, renderer='json')
def tag_remove(request):
    tag = request.matchdict['tag']
    error_id = request.matchdict['id']
    project = get_selected_project(request)

    try:
        error = Error.objects(project=project.token).with_id(error_id)
        if tag not in error.tags:
            return {'type': 'failure'}

        error.tags.remove(tag)
        error.save()
        Tag.removeOne(tag)
        return {'type': 'success'}
    except:
        return {'type': 'failure'}


@view_config(route_name='error_comment_add', permission='authenticated', xhr=True, renderer='json')
def comment_add(request):
    error_id = request.matchdict['id']
    project = get_selected_project(request)

    try:
        error = Error.objects(project=project.token).with_id(error_id)
        error.comments.append(Comment(
            author=request.user,
            content=request.POST.get('comment').strip(),
            created=int(time())
        ))
        error.save()
        return {'type': 'success'}
    except:
        return {'type': 'failure'}


@view_config(route_name='error_toggle_hide')
def toggle_hide(request):
    error_id = request.matchdict['id']
    project = get_selected_project(request)

    try:
        error = Error.objects(project=project.token).with_id(error_id)
        error.hiddenby = None if error.hiddenby else request.user
        error.save()

        url = request.route_url('error_view', project=project.token, id=error_id)
        return HTTPFound(location=url)
    except:
        return HTTPNotFound()

@view_config(route_name='error_timeline', xhr=False, renderer='error-timeline.html')
def timeline(request):

    project = get_selected_project(request)

    counts = {
        'open': project.errors().active().filter(seenby__ne=request.user).count(),
        'resolved': project.errors().resolved().filter(seenby__ne=request.user).count(),
        'mine': project.errors().active().filter(claimedby=request.user).count()
    }

    return {
        'selected_project': project,
        'available_projects': Project.objects(),
        'counts': counts,
        'basename': path.basename
    }


@view_config(route_name='error_timeline_data', renderer='json')
def timeline_data(request):
    project = get_selected_project(request)

    # grouping errors by type
    hash_to_errors = {}
    for error in project.raw_errors().order_by('timestamp'):
        # creating a map for this error
        if error.hash not in hash_to_errors:
            hash_to_errors[error.hash] = {}

        date = datetime.datetime.utcfromtimestamp(error.timestamp)
        date = date.strptime(date.strftime('%Y-%m-%d'), '%Y-%m-%d')
        day = int(date.strftime('%s')) * 1000

        # initializing the count for this day
        if day not in hash_to_errors[error.hash]:
            hash_to_errors[error.hash][day] = 0

        # incrementing the count for today
        hash_to_errors[error.hash][day] += 1

    # random fake data
    for hash in sorted(hash_to_errors.keys()):
        for i in [1,2,3,4,5,6,7,8]:
            randomDay = day + ( i * 86400 ) * 1000
            hash_to_errors[hash][randomDay] = random.randint(3, 20)

    # blah
    timeline_data = []
    for hash in sorted(hash_to_errors.keys()):

        datapoints = []
        for date in sorted(hash_to_errors[hash].keys()):
            datapoints.append([date, hash_to_errors[hash][date]])

        timeline_data.append({
            'label': hash,
            'data': datapoints
        })

    return {
        'type': 'success',
        'data': timeline_data
    }
    #except:
    #    return {'type': 'failure'}

def get_selected_project(request):
    try:
        return Project.objects.get(token=request.matchdict['project'])
    except:
        raise HTTPNotFound()

def get_trend(error):
    errors = ErrorInstance.objects(hash=error.hash)

    return put_errors_in_daily_buckets(errors)

def put_errors_in_daily_buckets(errors):

    #hack remove pls
    base_date = 0

    # group by day
    day_to_count_map = {}
    for error in sorted(errors, key=lambda x: x.timestamp):
        index = date_to_utc_day_timestamp(error.timestamp)
        base_date = index # remove

        if index not in day_to_count_map:
            day_to_count_map[index] = 0

        day_to_count_map[index] += 1

    # random fake data
    for i in [1,2,3,4,5,6,7,8]:
        nextDay = base_date + ( i * 86400 ) * 1000
        day_to_count_map[nextDay] = random.randint(3, 20)

    # transform into a [date, count] list
    datapoints = []
    for day in sorted(day_to_count_map.keys()):
        datapoints.append([day, day_to_count_map[day]])

    return datapoints

def date_to_utc_day_timestamp(date):
    # horrible, please fix
    date = datetime.datetime.utcfromtimestamp(date)
    date = date.strptime(date.strftime('%Y-%m-%d'), '%Y-%m-%d')
    return int(date.strftime('%s')) * 1000
