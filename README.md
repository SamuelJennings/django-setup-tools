# Django Easy Icons

Django Easy Icons lets you easily inline SVG icons directly into your Django templates using a simple templatetag. Django Easy Icons also allows you to directly add attributes to any SVG by supplying keyword arguments to the tag OR by supplying global defaults that are applied to all icons. No need to directly edit SVG files to make them compatible with your Django project :)

## Installation

```
pip install django-account-management
```

add `account_management` to your `INSTALLED_APPS` in `settings.py`

```python
INSTALLED_APPS = [
    ...
    'account_management',
    ...
]
```

## Storing your icons

`django-account-management` uses Django's built-in template engine to render SVG icons directly into your templates. Therefore, you should store your collection of SVG icons in a directory that is discoverable by the template engine. By default, `django-account-management` looks for SVG icons in any `icons/` directory.

```bash
    your_app/
        templates/
            your_app/
                your_template.html
                ...
            icons/
                home_icon.svg
                user_icon.svg
                ...
```

## Overriding icons

Because `django-account-management` uses Django's template engine to render SVG icons, you can easily override icons provided by third-party apps by placing your own icons in the same directory. `django-account-management` will render the icon that it finds first in the template directory.

For more information, see the Django docs on [how to override templates](https://docs.djangoproject.com/en/5.0/howto/overriding-templates/#how-to-override-templates).

## Usage

To use icons in your templates, you can use the `icon` template tag.

```html
{% load account_management %}

<!-- render an icon like this -->
{% icon 'home_icon.svg' %}

<!-- specifying the .svg extension is optional -->
{% icon 'home_icon' %}

<!-- directly add attributes to the <svg> element by suppyling keywords to tag -->
{% icon 'home_icon' class="icon" id="home" width="45px" %}

```

You can also user the "icon" template tag to specify icons in your python code.

```python

from account_management.templatetags.account_management import icon
from django.views.generic import TemplateView

class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['home_icon'] = icon('home_icon', id="home", width="45px")
        return context

```

Then simply use it directly in your template

```html

{{ home_icon }}

```

## Configuration

### Default Icon Directory

You can configure the default path to the SVG icons in your `settings.py`

```python

account_management_ICONS_DIR = 'alt_icon_dir'

```

`django-account-management` will now look for SVG icons in the `alt_icon_dir` template directory of your app.

### Default SVG Attributes

By default, `django-account-management` will render SVG icons with the following attributes:

```python
{
    'height': '1em',
    'fill': 'currentColor',
}
```

These defaults allow you to easily style your icons using CSS and inline them in text. You can override these defaults by setting the `account_management_DEFAULTS` in your `settings.py`

```python

account_management_DEFAULTS = {
    'class': 'icon',
    'width': '24px',
    'height': '24px',
    'fill': 'currentColor',
    'aria-hidden': 'true',
}

```

All default attributes can be overridden by supplying keyword arguments to the `icon` template tag.


## Alternative packages

There a number of alternative packages that provide similar functionality to `django-account-management`, however, the ones I found typically rely on the staticfiles storage system to store and render SVG icons. This makes it difficult to customize the icons as you place them in the template, especially when using remote storage systems. I wanted a package that would allow me to directly customize the icons as I placed them in the template, therefore I decided to create `django-account-management`.
