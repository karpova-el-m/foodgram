from django.views.generic.base import TemplateView
from django.shortcuts import render


class AboutPageView(TemplateView):
    template_name = 'frontend/src/pages/about/index.js'


class RulesPageView(TemplateView):
    template_name = 'frontend/src/pages/technologies/index.js'


def page_not_found(request, exception):
    return render(request, 'frontend/src/pages/not-found/index.js', status=404)


# def csrf_failure(request, reason=''):
#     return render(request, 'pages/403csrf.html', status=403)


# def custom_500(request):
#     return render(request, 'pages/500.html', status=500)
