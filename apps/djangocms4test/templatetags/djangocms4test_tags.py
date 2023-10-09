from django import template
from easy_thumbnails.files import get_thumbnailer


register = template.Library()


@register.simple_tag(takes_context=True)
def get_fb_image(context):
    fb_image = None
    # header image?
    request = context["request"]
    current_page = getattr(request, "current_page", None)
    if current_page:
        placeholders = current_page.get_placeholders()
        header = placeholders.filter(slot="header_image")
        if header.count():
            plugins = header[0].get_plugins()
            for plugin in plugins:
                instance, plugin = plugin.get_plugin_instance()
                if instance and getattr(instance, "image", None):
                    fb_image = instance.image
        # first content or teaser image
        content = placeholders.filter(slot="home_content")
        if not fb_image and content.count():
            plugins = content[0].get_plugins()
            for plugin in plugins:
                instance, plugin = plugin.get_plugin_instance()
                if instance and getattr(instance, "image", None):
                    fb_image = instance.image
        # create thumb
        if fb_image:
            thumbnailer = get_thumbnailer(fb_image)
            thumbnail_options = {"crop": True}
            thumbnail_options.update({"size": (1000, 600)})
            return thumbnailer.get_thumbnail(thumbnail_options).url
    return ""
