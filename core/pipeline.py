from core.models import UserProfile

def create_user_profile(backend, user, response, *args, **kwargs):
    """
    Creates a user profile for social authentication users if they don't already have one.
    By default, users created through social auth will be clients.
    """
    # Check if user profile already exists
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # If profile is newly created, set default values
    if created:
        profile.is_client = True
        profile.is_freelancer = False
        profile.save()
    
    return {'profile': profile} 