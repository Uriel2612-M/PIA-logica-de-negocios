from enum import Enum
from datetime import date
from decimal import Decimal

class EstadoContrato(Enum):
    COTIZADO = "COTIZADO"
    CONTRATADO = "CONTRATADO"
    EN_PREPARACION = "EN_PREPARACION"
    REALIZADO = "REALIZADO"
    CANCELADO = "CANCELADO"

# --- DOMAIN EVENTS (Requisito de la Rúbrica) ---
class DomainEvent:
    pass

class ContratoActivadoEvent(DomainEvent):
    def __init__(self, contrato_id: str):
        self.contrato_id = contrato_id
        self.mensaje = f"EVENTO DE DOMINIO: El contrato {contrato_id} pasó a CONTRATADO. Notificando a proveedores."
# -----------------------------------------------

class Contrato:
    def __init__(self, contrato_id: str, cliente_id: str, fecha_evento: date, costo_base: Decimal):
        self.contrato_id = contrato_id
        self.cliente_id = cliente_id
        self.fecha_evento = fecha_evento
        self.costo_base = costo_base
        self.estado = EstadoContrato.COTIZADO
        self.anticipo_pagado = Decimal("0.00")
        self.domain_events = [] # Aquí se guardan los eventos que ocurren

    def aprobar_cotizacion(self, monto_recibido: Decimal):
        anticipo_requerido = self.costo_base * Decimal("0.25")
        if monto_recibido < anticipo_requerido:
            raise ValueError(f"El anticipo debe ser de al menos el 25% (${anticipo_requerido}).")
        
        self.anticipo_pagado = monto_recibido
        self.estado = EstadoContrato.CONTRATADO
        
        # Disparamos el Domain Event al cambiar de estado
        self.domain_events.append(ContratoActivadoEvent(self.contrato_id))