from django.apps import AppConfig


class AiAgentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_agent'
    verbose_name = 'AI Agent'

    def ready(self):
        """Import signals when the app is ready"""
        import ai_agent.signals
