from django.contrib.auth import logout

GOOGLE = 'google-oauth2'
FACEBOOK = 'facebook'

def social_user(backend, uid, user=None, *args, **kwargs):
    provider = backend.name
    social = backend.strategy.storage.user.get_social_auth(provider, uid)
    if social:
        if user and social.user != user:
            logout(backend.strategy.request)
        elif not user:
            user = social.user
    return {'social': social,
            'user': user,
            'is_new': user is None,
            'new_association': False}

def load_extra_data(backend, details, response, uid, user, *args, **kwargs):
    social = kwargs.get('social') or \
             backend.strategy.storage.user.get_social_auth(backend.name, uid)
    if social:
        extra_data = backend.extra_data(user, uid, response, details,
                                        *args, **kwargs)
        social.set_extra_data(extra_data)
        set_userdata(backend, extra_data['access_token'], user, *args, **kwargs)

def set_userdata(backend, access_token, user, *args, **kwargs):
    if not user: return
    
    data = backend.user_data(access_token, *args, **kwargs)
    print(data)
    
    if backend.name == GOOGLE:
        user.image_url = data['picture']
    elif backend.name == FACEBOOK:
        user.image_url = data['picture']['data']['url']

    user.save()