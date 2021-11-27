from typing import OrderedDict
from django.forms.fields import JSONField
import graphene
from graphene.types.utils import yank_fields_from_attrs
from graphene_django.forms.converter import convert_form_field
from graphene_django.forms.mutation import BaseDjangoFormMutation, DjangoFormMutationOptions, fields_for_form
from graphene_django.types import ErrorType
from django.core.exceptions import ValidationError


def custom_fields_for_form(form, only_fields, exclude_fields):
    fields = OrderedDict()
    for name, field in form.fields.items():
        is_not_in_only = only_fields and name not in only_fields
        is_excluded = name in exclude_fields

        if is_not_in_only or is_excluded:
            continue
        fields[name] = convert_form_field(field, _type=field.OutputType)
    return fields


class CustomDjangoFormMutation(BaseDjangoFormMutation):
    class Meta:
        abstract = True

    errors = graphene.List(ErrorType)

    @classmethod
    def __init_subclass_with_meta__(
        cls, form_class=None, only_fields=(), exclude_fields=(), **options
    ):

        if not form_class:
            raise Exception("form_class is required for DjangoFormMutation")

        form = form_class()
        input_fields = fields_for_form(form, only_fields, exclude_fields)
        output_fields = custom_fields_for_form(form, only_fields, exclude_fields)
        _meta = DjangoFormMutationOptions(cls)
        _meta.form_class = form_class
        _meta.fields = yank_fields_from_attrs(output_fields, _as=graphene.Field)

        input_fields = yank_fields_from_attrs(input_fields, _as=graphene.InputField)
        super().__init_subclass_with_meta__(
            _meta=_meta, input_fields=input_fields, **options
        )

    @classmethod
    def perform_mutate(cls, form, info):
        form.save()
        return cls(errors=[], **form.cleaned_data)


class ListForm(JSONField):
    def __init__(self, form_class ,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_class = form_class
        
        input_fields = fields_for_form(form_class(), only_fields=(), exclude_fields=())
        output_fields = fields_for_form(form_class(), only_fields=(), exclude_fields=())
        self.InputType = type(
            '{}Input'.format(form_class.__name__),
            (graphene.InputObjectType,),
            input_fields
        )
        self.OutputType = type(
            '{}Output'.format(form_class.__name__),
            (graphene.ObjectType,),
            output_fields
        )
        
    def clean(self, value):
        value = super().clean(value)

        self.forms = [
            self.form_class(form_data)
            for form_data in value
        ]
        errors = []
        for form in self.forms:
            if not form.is_valid():
                for field, messages in form.errors.items():
                    errors.append({
                        field: [ValidationError(message) for message in messages]
                    })

        if errors:
            raise ValidationError(errors)

        return value
    
    def save(self):
        for form in self.forms:
            form.save()


@convert_form_field.register(ListForm)
def convert_list_form_field(field, _type=None, **kwargs):
    return graphene.List(graphene.NonNull(_type if _type else field.InputType), required=field.required)
