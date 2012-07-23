from colander import MappingSchema, SchemaNode
from colander import String, Email, Integer
from colander import Invalid
from deform.widget import PasswordWidget, HiddenWidget
from triage.models import User
from passlib.apps import custom_app_context as pwd_context


def user_login_validator(form, values):
    try:
        user = User.objects.get(email=values['email'])
        if (not pwd_context.verify(values['password'], user.password)):
            raise Exception
    except:
        exception = Invalid(form, 'There was a problem with your submission')
        exception['email'] = 'Your Email or Password is incorrect'
        raise exception


def user_register_validator(form, values):
    exception = Invalid(form, 'There was a problem with your submission')
    if values['password'] != values['confirm_password']:
        exception['confirm_password'] = 'Confirm Password does not match Password'

    user = User.objects(name=values['name'])
    if user:
        exception['name'] = 'You have to choose a unique name'

    user = User.objects(email=values['email'])
    if user:
        exception['email'] = 'Email already exists in our database'

    if exception.children:
        raise exception


def user_form_validator(current_user):
    def unique_exception(exception, field):
        exception[field] = "You have to choose a unique {field}"
        return exception

    def user_inner_validator(form, values):
        exception = Invalid(form, 'There was a problem with your submission')

        if values['password'] and values['password'] != values['confirm_password']:
            exception['confirm_password'] = 'Confirm Password does not match Password'

        user = User.objects(name=values['name'])
        if user and values['name'] != current_user.name:
                exception = unique_exception(exception, 'name')

        user = User.objects(email=values['email'])
        if user and values['email'] != current_user.email:
                exception = unique_exception(exception, 'email')

        if exception.children:
            raise exception

    return user_inner_validator


class UserLoginSchema(MappingSchema):
    email = SchemaNode(String(), description='Enter your email address', validator=Email())
    password = SchemaNode(String(), description='Enter your password', widget=PasswordWidget())
    tzoffset = SchemaNode(Integer(), widget=HiddenWidget())


class UserFormSchema(MappingSchema):
    name = SchemaNode(String(), descriprtion='Enter your name')
    email = SchemaNode(String(), description='Enter your email address', validator=Email())
    password = SchemaNode(String(), description='Enter your password', widget=PasswordWidget(), missing=False)
    confirm_password = SchemaNode(String(), description='Confirm your password', widget=PasswordWidget(), missing=False)
    tzoffset = SchemaNode(Integer(), widget=HiddenWidget())


class UserRegisterSchema(MappingSchema):
    name = SchemaNode(String(), descriprtion='Enter your name')
    email = SchemaNode(String(), description='Enter your email address', validator=Email())
    password = SchemaNode(String(), description='Enter your password', widget=PasswordWidget())
    confirm_password = SchemaNode(String(), description='Confirm your password', widget=PasswordWidget())
    tzoffset = SchemaNode(Integer(), widget=HiddenWidget())

class ProjectFormSchema(MappingSchema):
    name = SchemaNode(String(), descriprtion='Project name')
    token = SchemaNode(String(), description='token')
    path = SchemaNode(String(), description='Path')
    github = SchemaNode(String(), description='Github')
