from datetime import datetime, timedelta

from django.conf import settings
import jwt


def generate_tokens(user):
    access_payload = {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "exp": datetime.now() + timedelta(hours=1),
        "iat": datetime.now(),
        "token_type": "access",
    }
    refresh_payload = {
        "user_id": user.id,
        "exp": datetime.now() + timedelta(days=7),
        "iat": datetime.now(),
        "token_type": "refresh",
    }

    access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm="HS256")

    refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm="HS256")

    return access_token, refresh_token
