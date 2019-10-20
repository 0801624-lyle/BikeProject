from django import template

register = template.Library()

# Filter for adding a css class to a Form field.
@register.filter(name="add_class")
def add_class(field, css):
    return field.as_widget(attrs={"class": css})


# Filter for adding an id to a Form field.
@register.filter(name="add_id")
def add_id(field, name):
    return field.as_widget(attrs={"id": name})