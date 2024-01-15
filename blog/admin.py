from django.contrib import admin
from .models import Post, Comment


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'author', 'publish', 'status', 'tag_list')
    list_filter = ('status', 'created', 'publish', 'author')
    search_fields = ('title', 'body', 'author__username')
    prepopulated_fields = {'slug': ('title', )}
    # autocomplete_fields = ('author', )
    raw_id_fields = ('author',)
    date_hierarchy = 'publish'
    ordering = ('status', 'publish', 'author')

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('tags')

    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'post', 'created', 'active')
    list_filter = ('active', 'created', 'updated')
    search_fields = ('name', 'email', 'body')
