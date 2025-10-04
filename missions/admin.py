from django.contrib import admin

from missions.models import Mission, Target, Note

admin.site.register(Mission)
admin.site.register(Target)
admin.site.register(Note)
