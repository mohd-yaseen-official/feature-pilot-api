from django.db import models
from feedbacks.models import Feedback

class Proposal(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('applied', 'Applied'),
        ('failed', 'Failed'),
    ]
    
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE, related_name='proposals')
    proposal_data = models.JSONField()
    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    applied_at = models.DateTimeField(null=True, blank=True)
    pr_url = models.URLField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        verbose_name = 'Proposal'
        verbose_name_plural = 'Proposals'
        ordering = ['-created_at']

    def __str__(self):
        return f"Proposal for {self.feedback.title} ({self.status})"
