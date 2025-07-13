from rest_framework import serializers
from projects.models import Project


class ProjectSerializer(serializers.ModelSerializer):
    github_token = serializers.CharField(write_only=True)

    class Meta:
        model = Project
        fields = ['id', 'title', 'github_token', 'github_repo_path', 'user', 'is_deleted', 'project_key']
        read_only_fields = ['id', 'is_deleted', 'project_key', 'user']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        token = instance.github_token
        if not token or len(token) < 8:
            data['github_token'] = '*' * len(token) if token else ''
        else:
            data['github_token'] = f'{token[:4]}...{token[-4:]}'
        return data

    def create(self, validated_data):
        user = validated_data.get('user') or self.context.get('request').user
        project = Project.objects.create(
            title=validated_data['title'],
            github_token=validated_data['github_token'],
            github_repo_path=validated_data['github_repo_path'],
            user=user
        )
        return project
