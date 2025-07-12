from django.urls import path
from .views import create_project, manage_project, list_projects

app_name = 'projects'

urlpatterns = [
    path('', list_projects, name='list_projects'),
    path('create/', create_project, name='create_project'),
    path('manage/<int:id>/', manage_project, name='manage_project'),
]
