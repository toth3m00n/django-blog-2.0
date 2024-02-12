from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin

from accounts.models import Profile


@admin.register(Profile)
class MyProfile(SummernoteModelAdmin):
    summernote_fields = ('bio',)
