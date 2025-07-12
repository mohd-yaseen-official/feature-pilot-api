from django.contrib import admin
from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'github_repo_path', 'user', 'is_deleted')
    search_fields = ('title', 'github_repo_path', 'user__username')
