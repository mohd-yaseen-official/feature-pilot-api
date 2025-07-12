from django.urls import path
from .views import create_feedback, list_feedbacks

app_name = 'feedbacks'

urlpatterns = [
    path('<int:id>/', list_feedbacks, name='list_feedbacks'),
    path('create/', create_feedback, name='create_feedback'),
]
