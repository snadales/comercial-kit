"""Autenticación y permisos por token de consumidor (K2)."""

from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.permissions import BasePermission
from comercial_kit.models import ConsumidorToken


class ConsumidorTokenAuthentication(BaseAuthentication):
    """Autentica solicitudes mediante Bearer token cotejando el hash SHA-256 en BD."""

    def authenticate_header(self, request):
        return 'Bearer realm="navarino-api"'

    def authenticate(self, request):

        auth = get_authorization_header(request).split()

        if not auth:
            return None

        if auth[0].lower() not in (b"bearer", b"token"):
            return None

        if len(auth) == 1:
            raise AuthenticationFailed("Token de autorización no provisto.")
        elif len(auth) > 2:
            raise AuthenticationFailed("Formato de cabecera de autorización inválido.")

        try:
            token_str = auth[1].decode("utf-8")
        except UnicodeError:
            raise AuthenticationFailed("Token con caracteres inválidos.")

        consumidor = ConsumidorToken.autenticar(token_str)
        if not consumidor:
            raise AuthenticationFailed("Token inválido o inactivo.")

        return (consumidor, token_str)


class RequiereLectura(BasePermission):
    """Permite acceso a consumidores con alcance de lectura o escritura."""

    def has_permission(self, request, view):
        user = request.user
        if isinstance(user, ConsumidorToken):
            return user.activo
        return bool(user and user.is_authenticated)


class RequiereEscritura(BasePermission):
    """Permite acceso únicamente a consumidores con alcance explícito de escritura."""

    def has_permission(self, request, view):
        user = request.user
        if isinstance(user, ConsumidorToken):
            if not user.activo:
                return False
            return user.alcance == ConsumidorToken.ALCANCE_ESCRITURA
        return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))
