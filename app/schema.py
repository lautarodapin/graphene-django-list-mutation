import graphene
from graphene_django.forms.mutation import fields_for_form
from app.models import User
from graphene_django.types import DjangoObjectType
from django import forms
from app.utils import CustomDjangoFormMutation, ListForm
from app.models import User
from django.core.exceptions import ValidationError
from graphene_django.types import ErrorType


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['id', 'username', 'password']


class UserType(DjangoObjectType):
    class Meta:
        model = User


class Query(graphene.ObjectType):
    users = graphene.List(graphene.NonNull(UserType))
    
    def resolve_users(self, info):
        return User.objects.all()
    

class UsersForm(forms.Form):
    users = ListForm(UserForm)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.list_form = [
            field
            for field in self.fields.values()
            if isinstance(field, ListForm)
        ]
        
    def save(self):
        for form in self.list_form:
            form.save()



class CreateUsersMutation(CustomDjangoFormMutation):
    class Meta:
        form_class = UsersForm
     

class CreateUsers2Mutation(graphene.Mutation):
    class Arguments:
        input = graphene.List(graphene.NonNull(type(
            '{}Input2'.format(UserForm.__name__),
            (graphene.InputObjectType,),
            fields_for_form(UserForm(), [], []),
        )))
        
    users = graphene.List(UserType)
    errors = graphene.List(ErrorType)
    
    @staticmethod
    def mutate(self, info, input):
        forms = []
        errors = []
        for form_data in input:
            form = UserForm(form_data)
            forms.append(form)
            if not form.is_valid():
                for field, messages in form.errors.items():
                    errors.append({
                        field: [
                            ValidationError(
                                f'{form.instance} > {form.fields[field].label}: {message}',
                            )
                            for message in messages
                        ],
                    })
        if errors: raise ValidationError(errors)
        
        instances = [
            form.save()
            for form in forms
        ]

        return CreateUsers2Mutation(users=instances)


    
class Mutation(graphene.ObjectType):
    create_users = CreateUsersMutation.Field()
    create_users_2 = CreateUsers2Mutation.Field()
