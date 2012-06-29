from pyramid.view import view_config
import base64
import json
from triage.models import Error, Project, ProjectVersion
from time import time

@view_config(route_name='api_log', renderer='string')
def log(request):
    get_params = dict(request.GET)
    try:
        msg = json.loads(base64.b64decode(get_params['data']))
        msg = _format_backtrace(msg)

        error = Error.create_from_msg(msg)
        error.save()
    except:
        return {'success': False}

    return {'success': True}



@view_config(route_name='api_version', renderer='json', request_method='POST')
def version(request):

    project = Project.objects.get(token=request.POST.get('token'))
    try:
        previous = ProjectVersion.objects(project=project).order_by('-created')[0]
    except:
        previous = None

    version = ProjectVersion()
    version.project = project
    version.created = int(time())
    version.version = request.POST.get('version')
    if previous:
        version.previous = previous.version
    version.save()

    return {'success': True}



def _format_backtrace(msg):
    if ('backtrace' in msg):
        backtrace = []
        for trace in msg['backtrace']:
            backtrace.append({
                'class': '',
                'file': '',
                'function': trace,
                'line': 'n/a'
            })
        msg['backtrace'] = backtrace
    return msg
