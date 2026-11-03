"""Modelos centrales de comercial-kit (K2, K6, K7)."""

import json
import hashlib
import secrets
import logging
from django.db import models
from simple_history.models import HistoricalRecords

from comercial_kit.op_connect import resolve_op_reference
from comercial_kit.hub_alertas import HubAlertasAdapter

logger = logging.getLogger("comercial_kit.models")


class Parametro(models.Model):
    """Parámetro de configuración y negocio persistido en base de datos (K6).
    
    Todo lo que no sean las 4 variables base de entorno vive aquí.
    Soporta referencias op:// resueltas dinámicamente con 1Password Connect.
    """

    TIPO_STRING = "string"
    TIPO_INTEGER = "integer"
    TIPO_FLOAT = "float"
    TIPO_BOOLEAN = "boolean"
    TIPO_JSON = "json"

    TIPOS = [
        (TIPO_STRING, "Texto (String)"),
        (TIPO_INTEGER, "Entero (Integer)"),
        (TIPO_FLOAT, "Decimal (Float)"),
        (TIPO_BOOLEAN, "Booleano (Boolean)"),
        (TIPO_JSON, "JSON Estructurado"),
    ]

    clave = models.CharField(max_length=120, unique=True, db_index=True)
    valor = models.TextField(blank=True, default="")
    tipo = models.CharField(max_length=20, choices=TIPOS, default=TIPO_STRING)
    descripcion = models.CharField(max_length=255, blank=True, default="")
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Parámetro"
        verbose_name_plural = "Parámetros"
        ordering = ["clave"]

    def __str__(self):
        return f"{self.clave} ({self.tipo})"

    def valor_casteado(self):
        """Devuelve el valor según el tipo configurado, resolviendo op:// si aplica."""
        raw = self.valor.strip()
        # Resolución de secretos op://
        if raw.startswith("op://"):
            raw = resolve_op_reference(raw)

        if self.tipo == self.TIPO_INTEGER:
            try:
                return int(raw)
            except (ValueError, TypeError):
                return 0
        elif self.tipo == self.TIPO_FLOAT:
            try:
                return float(raw)
            except (ValueError, TypeError):
                return 0.0
        elif self.tipo == self.TIPO_BOOLEAN:
            return raw.lower() in ("true", "1", "t", "y", "yes", "si", "sí")
        elif self.tipo == self.TIPO_JSON:
            try:
                return json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                return {}
        return raw

    @classmethod
    def get(cls, clave: str, default=None):
        """Obtiene un parámetro por clave casteado a su tipo."""
        try:
            param = cls.objects.get(clave=clave)
            return param.valor_casteado()
        except cls.DoesNotExist:
            return default
        except Exception as e:
            logger.warning("Error obteniendo parámetro '%s': %s", clave, str(e))
            return default

    @classmethod
    def set(cls, clave: str, valor, tipo: str = TIPO_STRING, descripcion: str = ""):
        """Crea o actualiza un parámetro."""
        if tipo == cls.TIPO_JSON and not isinstance(valor, str):
            val_str = json.dumps(valor)
        else:
            val_str = str(valor)

        param, _ = cls.objects.update_or_create(
            clave=clave,
            defaults={"valor": val_str, "tipo": tipo, "descripcion": descripcion},
        )
        return param


class ConsumidorToken(models.Model):
    """Token de autenticación por consumidor con hash SHA-256 (K2)."""

    ALCANCE_LECTURA = "lectura"
    ALCANCE_ESCRITURA = "escritura"
    ALCANCES = [
        (ALCANCE_LECTURA, "Solo Lectura"),
        (ALCANCE_ESCRITURA, "Lectura y Escritura"),
    ]

    nombre = models.CharField(max_length=100)
    hash_token = models.CharField(max_length=64, unique=True, db_index=True)
    alcance = models.CharField(max_length=20, choices=ALCANCES, default=ALCANCE_LECTURA)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Token de Consumidor"
        verbose_name_plural = "Tokens de Consumidores"

    def __str__(self):
        return f"{self.nombre} ({self.alcance}) [{'Activo' if self.activo else 'Inactivo'}]"

    @classmethod
    def hash_str(cls, raw_token: str) -> str:
        return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()

    @classmethod
    def crear_token(cls, nombre: str, alcance: str = ALCANCE_LECTURA) -> tuple["ConsumidorToken", str]:
        """Genera un nuevo token seguro y devuelve (instancia, raw_token)."""
        raw_token = f"nav_{secrets.token_urlsafe(32)}"
        token_hash = cls.hash_str(raw_token)
        obj = cls.objects.create(nombre=nombre, hash_token=token_hash, alcance=alcance, activo=True)
        return obj, raw_token

    @classmethod
    def autenticar(cls, raw_token: str) -> "ConsumidorToken | None":
        """Busca y verifica un token activo por su hash."""
        if not raw_token:
            return None
        h = cls.hash_str(raw_token)
        try:
            return cls.objects.get(hash_token=h, activo=True)
        except cls.DoesNotExist:
            return None


class Aviso(models.Model):
    """Registro de avisos y alertas operativas (K7).
    
    Regla estricta: Solo avisos, nunca bloqueos.
    Los avisos críticos se notifican al Hub central (AgoraOS#1245).
    """

    NIVEL_INFO = "info"
    NIVEL_AVISO = "aviso"
    NIVEL_CRITICO = "critico"
    NIVELES = [
        (NIVEL_INFO, "Informativo"),
        (NIVEL_AVISO, "Aviso"),
        (NIVEL_CRITICO, "Crítico"),
    ]

    ESTADO_ABIERTO = "abierto"
    ESTADO_VISTO = "visto"
    ESTADO_CERRADO = "cerrado"
    ESTADOS = [
        (ESTADO_ABIERTO, "Abierto"),
        (ESTADO_VISTO, "Visto"),
        (ESTADO_CERRADO, "Cerrado"),
    ]

    origen = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, db_index=True)
    objeto = models.CharField(max_length=100, blank=True, default="")
    mensaje = models.TextField()
    nivel = models.CharField(max_length=20, choices=NIVELES, default=NIVEL_AVISO)
    estado = models.CharField(max_length=20, choices=ESTADOS, default=ESTADO_ABIERTO)
    metadata = models.JSONField(default=dict, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Aviso"
        verbose_name_plural = "Avisos"
        ordering = ["-creado_en"]

    def __str__(self):
        return f"[{self.nivel.upper()}] {self.codigo} ({self.objeto}): {self.mensaje[:40]}"

    def save(self, *args, **kwargs):
        es_nuevo = self.pk is None
        super().save(*args, **kwargs)
        if es_nuevo and self.nivel == self.NIVEL_CRITICO:
            try:
                HubAlertasAdapter.enviar_critico(self)
            except Exception as e:
                logger.error("Error al enviar aviso a hub: %s", str(e))

