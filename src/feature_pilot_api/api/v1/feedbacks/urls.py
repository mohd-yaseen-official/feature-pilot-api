from django.urls import path
from .views import create_feedback, list_feedbacks, list_all_feedbacks

app_name = 'feedbacks'

urlpatterns = [
    path('', list_all_feedbacks, name='list_all_feedbacks'),
    path('<int:project_id>/', list_feedbacks, name='list_feedbacks'),
    path('create/', create_feedback, name='create_feedback'),
]
