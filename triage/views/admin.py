from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.renderers import render_to_response
from jinja2 import Markup
from triage.forms import UserRegisterSchema, UserFormSchema, user_form_validator, user_register_validator
from deform import Form, ValidationFailure
from pyramid.security import remember, forget
from pyramid.security import authenticated_userid
from triage.models import User, Project
from mongoengine.queryset import DoesNotExist
from deform.widget import TextInputWidget
from colander import Invalid


@view_config(route_name='admin_user', permission='authenticated', renderer='admin/users/list.html')
def admin_user(request):
    return {
        'users': User.objects()
    }


@view_config(route_name='admin_user_edit', permission='authenticated', renderer='admin/users/edit.html')
def admin_user_edit(request):
    def default_values(schema, user):
        for field in schema.children:
            if field.name in user and field.name != 'password':
                field.default = user[field.name]


    user = User.objects.with_id(request.matchdict['user'])
    schema = UserFormSchema(validator=user_form_validator(user))

    default_values(schema, user)

    form = Form(schema, buttons=('submit',))
    form_render = None

    if 'submit' in request.POST:
        controls = request.POST.items()

        try:
            values = form.validate(controls)
            user.update(values)
            user.save()
            default_values(schema, user)
        except ValidationFailure, e:
            form_render = e.render()

    if not form_render:
        form_render = form.render()

    params = {
        'user': user,
        'form': Markup(form_render)
    }

    return params

@view_config(route_name='admin_user_create', permission='authenticated')
def admin_user_create(request):
    schema = UserRegisterSchema(validator=user_register_validator)
    form = Form(schema, buttons=('submit',))

    if 'submit' in request.POST:
        controls = request.POST.items()

        try:
            values = form.validate(controls)
            user = User.from_data(values)
            user.tzoffset = values['tzoffset']
            user.save()

            return HTTPFound(location=request.route_url('admin_user'))

        except ValidationFailure, e:
            form_render = e.render()
    else:
        form_render = form.render()

    params = {
        'form': Markup(form_render)
    }

    return render_to_response('admin/users/create.html', params)


@view_config(route_name='admin_user_delete', permission='authenticated')
def admin_user_delete(request):
    user = User.objects.with_id(request.matchdict['user'])
    logged_user_id = authenticated_userid(request)

    if user:
        user.delete()
        if str(user.id) == logged_user_id:
            headers = forget(request)
            return HTTPFound(location=request.route_url('index'), headers=headers)
        else:
            return HTTPFound(location=request.route_url('admin_user'))

    else:
        return HTTPNotFound()


@view_config(route_name='admin_project', permission='authenticated', renderer='admin/projects/list.html')
def admin_project(request):
    return {
        'projects': Project.objects()
    }
