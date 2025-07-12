from rest_framework import serializers
from proposals.models import Proposal

class ProposalSerializer(serializers.ModelSerializer):
    feedback_title = serializers.CharField(source='feedback.title', read_only=True)
    project_title = serializers.CharField(source='feedback.project.title', read_only=True)
    
    class Meta:
        model = Proposal
        fields = [
            'id', 'feedback', 'feedback_title', 'project_title',
            'proposal_data', 'is_confirmed', 'created_at', 
            'applied_at', 'pr_url', 'status'
        ]
        read_only_fields = [
            'id', 'feedback_title', 'project_title', 'proposal_data',
            'created_at', 'applied_at', 'pr_url', 'status'
        ]
