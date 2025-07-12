from django.contrib import admin
from .models import Proposal

@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ('feedback', 'status', 'is_confirmed', 'created_at')
    list_filter = ('status', 'is_confirmed', 'created_at')
    search_fields = ('feedback__title', 'feedback__project__title')
