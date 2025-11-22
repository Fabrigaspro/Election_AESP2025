# middleware.py
from django.utils import timezone
from .models import Profile

class ActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                profile = Profile.objects.get(user=request.user)
                profile.update_activity()
            except Profile.DoesNotExist:
                pass
        
        response = self.get_response(request)
        return response