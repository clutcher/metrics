import base64
import json
from typing import Optional, Dict

from django.conf import settings
from django.http import HttpResponse


class BasicAuthMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def _load_users(self) -> Optional[Dict[str, str]]:
        users = getattr(settings, 'METRICS_BASIC_AUTH_USERS', None)
        if users in (None, ''):
            return None
        if isinstance(users, dict):
            return users
        if isinstance(users, (list, tuple)):
            # unexpected type, disable to avoid breaking
            return None
        if isinstance(users, str):
            try:
                parsed = json.loads(users)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                return None
        return None

    def __call__(self, request):
        users = self._load_users()
        if not users:
            return self.get_response(request)

        auth = request.META.get('HTTP_AUTHORIZATION')
        if not auth or not auth.lower().startswith('basic '):
            return self._unauthorized()

        try:
            b64 = auth.split(' ', 1)[1]
            decoded = base64.b64decode(b64).decode('utf-8')
            if ':' not in decoded:
                return self._unauthorized()
            username, password = decoded.split(':', 1)
        except Exception:
            return self._unauthorized()

        if users.get(username) == password:
            return self.get_response(request)
        return self._unauthorized()

    @staticmethod
    def _unauthorized() -> HttpResponse:
        response = HttpResponse('Unauthorized', status=401)
        response['WWW-Authenticate'] = 'Basic realm="Restricted"'
        return response
