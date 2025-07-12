from django.urls import path
from .views import list_project_proposals, confirm_proposal, list_all_proposals

app_name = 'proposals'

urlpatterns = [
    path('', list_all_proposals, name='list_all_proposals'),
    path('<int:project_id>/', list_project_proposals, name='list_project_proposals'),
    # path('manage/<int:proposal_id>/', view_proposal, name='view_proposal'),
    path('<int:proposal_id>/confirm/', confirm_proposal, name='confirm_proposal'),
]
