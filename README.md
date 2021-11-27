# Django graphene example

## Create multiple instances of a model in a single transaction
\* *This can be wrap in `transaction.atomic()`*

___

### There are two ways of dealing with this problem.

## 1. Using a subclass of `BaseDjangoFormMutation` 
This example is the mutation `create_users`. Where you have to create a custom Form, that has a field that is the list of the form you wan't to use.

## 2. Using a mutation.
This way you define a mutation and in the `Argument` class you define the field as a non nullable list of the Model Input object type.

    You must have the ModelForm of the Model beforehand.
And in the `staticmethod` `mutate` you catch the data and creates the forms for each item in the list and validate that form.

    Here you could do some custom error formatting.
Then you save each form and grab the instances and return it to the output field.