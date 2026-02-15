from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

def get_jwt_user_from_cookie(request):
    token = request.COOKIES.get("access")
    if not token:
        return None

    jwt = JWTAuthentication()
    try:
        validated = jwt.get_validated_token(token)
        return jwt.get_user(validated)
    except AuthenticationFailed:
        return None
    except Exception:
        return None
