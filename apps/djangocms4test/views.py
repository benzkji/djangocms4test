from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from django.views.generic import TemplateView


class LanguageChooserEnhancerMixin(object):
    """
    this calls correct get_absolute_urls in cms's language_chooser tags!
    """

    def get(self, request, **kwargs):
        self.object = self.get_object()
        if hasattr(self.request, "toolbar"):
            self.request.toolbar.set_object(self.object)
        return super(LanguageChooserEnhancerMixin, self).get(request, **kwargs)


class AutoSlugMixin(object):
    """
    redirect if the slug is no more correct!
    """

    def get(self, request, **kwargs):
        self.object = self.get_object()
        if self.request.path != self.object.get_absolute_url():
            return HttpResponsePermanentRedirect(self.object.get_absolute_url())
        return super(AutoSlugMixin, self).get(request, **kwargs)


class PublishedViewMixin:
    """
    in edit mode, get all, otherwise only published
    """

    def get_queryset(self):
        if getattr(self.request, "toolbar", None):
            if self.request.toolbar.edit_mode:
                return self.model.objects.all()
        return self.model.objects.published()


class RobotsView(TemplateView):
    """
    flexible robots.txt, from within your base templates folder
    """

    content_type = "text/plain"

    def get_template_names(self):
        # requires 'django.contrib.sites.middleware.CurrentSiteMiddleware',
        site = self.request.site
        env = settings.ENV
        return (
            "robots_{}_{}.txt".format(site.domain, env),
            "robots_{}.txt".format(site.domain),
            "robots_{}_{}.txt".format(site.name, env),
            "robots_{}.txt".format(site.name),
            "robots_{}_{}.txt".format(site.id, env),
            "robots_{}.txt".format(site.id),
            "robots_{}.txt".format(env),
            "robots.txt",
        )
