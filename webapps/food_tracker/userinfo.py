import requests

GOOGLE = "google-oauth2"
FACEBOOK = "facebook"

OAUTH_PROVIDERS = [GOOGLE, FACEBOOK]

class UserInfoFetcher(object):
    def get_picture(self):
        pass
    def get_email(self):
        pass
    def get_firstname(self):
        pass
    def get_lastname(self):
        pass
    
class GoogleFetcher(UserInfoFetcher):
    GOOGLE_DISCOVERY = "https://accounts.google.com/.well-known/openid-configuration"
    USERINFO_ENDPOINT = "userinfo_endpoint"
    
    def __init__(self, request):
        access_token = get_access_token(request, GOOGLE)
        try:
            userinfo_endpoint = requests.get(self.GOOGLE_DISCOVERY)\
                                        .json()\
                                        .get(self.USERINFO_ENDPOINT)
            response = requests.get(
                userinfo_endpoint,
                params={
                    'access_token': access_token,
                }).json()
            if 'error' in response:
                print(response.get('error'))
                return None
            
            self.data = response

        except Exception as e:
            print(e)
            return None
    
    def get_picture(self):
        if not self.data: return None
        return self.data.get('picture', '')
    
    def get_email(self):
        if not self.data: return None
        return self.data.get('email', '')
    
    def get_firstname(self):
        if not self.data: return None
        return self.data.get('given_name', '')
    
    def get_lastname(self):
        if not self.data: return None
        return self.data.get('family_name', '')
    
class FacebookFetcher(UserInfoFetcher):
    API_ENDPOINT = 'https://graph.facebook.com/v13.0/me'
    PICTURE_ENDPINT = 'https://graph.facebook.com/v13.0/me/picture'

    def __init__(self, request):
        access_token = get_access_token(request, FACEBOOK)
        try:
            response = requests.get(
                self.API_ENDPOINT, 
                params={
                'fields': 'email,picture.type(large)',
                'redirect': False,
                'access_token': access_token,
            }).json()
            if 'error' in response:
                print(response.get('error'))
                return None
            
            self.data = {
                **response,
                'picture': response['picture']['data']['url'],
            }
            
            # self.data['picture'] = response['picture']['data']['url']

        except Exception as e:
            print(e)
            return None
    
    def get_picture(self):
        if not self.data: return None
        return self.data.get('picture', '')
    
    def get_email(self):
        if not self.data: return None
        return self.data.get('email', '')
    
    def get_firstname(self):
        if not self.data: return None
        return self.request.user.first_name
    
    def get_lastname(self):
        if not self.data: return None
        return self.request.user.last_name

def get_access_token(request, provider):
    return request.user.social_auth.get(provider=provider).extra_data['access_token']

def get_fetcher(provider, request):
    fetchers = {
        GOOGLE: lambda _: GoogleFetcher(request),
        FACEBOOK: lambda _: FacebookFetcher(request),
    }
    return fetchers.get(provider, lambda _: None)(None)

def get_userinfo(request):
    provider = ''
    for p in OAUTH_PROVIDERS:
        if request.user.social_auth.filter(provider=p):
            provider = p
            break

    fetcher = get_fetcher(provider, request)
    if not fetcher: return None
    
    data = {
        'picture': fetcher.get_picture(),
        'email': fetcher.get_email(),
        'first_name': fetcher.get_firstname(),
        'last_name': fetcher.get_lastname(),
    }
    
    return data