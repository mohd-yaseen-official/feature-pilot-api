from rest_framework import serializers
from feedbacks.models import Feedback

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['id', 'title', 'created_at', 'project']
        read_only_fields = ['id', 'created_at']
