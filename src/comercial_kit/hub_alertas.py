"""Adaptador para el Hub Central de Alertas (K7, AgoraOS#1245)."""

import logging
from typing import Any

logger = logging.getLogger("comercial_kit.hub_alertas")


class HubAlertasAdapter:
    """Adaptador detrás de interfaz para enviar avisos críticos al hub."""

    @classmethod
    def enviar_critico(cls, aviso: Any) -> bool:
        """Registra el aviso crítico en el log estructurado y lo envía al hub si está configurado.
        
        NUNCA lanza excepciones ni bloquea la acción.
        """
        try:
            logger.critical(
                "Aviso crítico recibido para hub central: [%s] %s - %s",
                getattr(aviso, "codigo", "CRIT"),
                getattr(aviso, "objeto", "SIN-OBJETO"),
                getattr(aviso, "mensaje", ""),
                extra={
                    "evento": "aviso_critico_hub",
                    "codigo": getattr(aviso, "codigo", ""),
                    "objeto": getattr(aviso, "objeto", ""),
                    "origen": getattr(aviso, "origen", ""),
                },
            )
            # En el futuro, si hay endpoint configurado en Parametro('hub_alertas.url'):
            # se hace POST a Alertmanager. Por ahora el adaptador registra en el log.
            return True
        except Exception as e:
            logger.error("Error no bloqueante en HubAlertasAdapter: %s", str(e))
            return False
