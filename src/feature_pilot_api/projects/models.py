import uuid
from django.db import models
from django.contrib.auth.models import User

class Project(models.Model):
    title = models.CharField(max_length=255)
    github_token = models.CharField(max_length=255, help_text='Personal access token or deploy key')
    github_repo_path = models.CharField(max_length=255, help_text='GitHub repository in username/repo format')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    is_deleted = models.BooleanField(default=False)
    project_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    class Meta:
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
        ordering = ['title']

    def __str__(self):
        return self.title
