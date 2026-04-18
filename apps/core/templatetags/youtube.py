from django import template

register = template.Library()

@register.filter
def youtube_embed(value):
    # For 'watch?v=' links, convert to embed
    if "youtube.com" in value and "watch?v=" in value:
        return value.replace("watch?v=", "embed/")
    # For youtu.be short links, convert to embed
    if "youtu.be" in value:
        return "https://www.youtube.com/embed/" + value.split('/')[-1]
    return value
