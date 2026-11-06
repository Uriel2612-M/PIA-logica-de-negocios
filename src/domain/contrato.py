from enum import Enum
from decimal import Decimal
from typing import List
from datetime import date

# 1. Definición de la Máquina de Estados requerida
class EstadoContrato(Enum):
    COTIZADO = "COTIZADO"
    CONTRATADO = "CONTRATADO"
    EN_PREPARACION = "EN_PREPARACION"
    REALIZADO = "REALIZADO"
    CANCELADO = "CANCELADO"

class ServicioExtra:
    def __init__(self, id_servicio: str, costo: Decimal):
        self.id_servicio = id_servicio
        self.costo = costo

# 2. Agregado Principal (Aggregate Root)
class Contrato:
    def __init__(self, contrato_id: str, cliente_id: str, fecha_evento: date, costo_base: Decimal):
        self.contrato_id = contrato_id
        self.cliente_id = cliente_id
        self.fecha_evento = fecha_evento
        self.costo_base = costo_base
        self.estado = EstadoContrato.COTIZADO
        self.anticipo_pagado = Decimal("0.00")
        self.servicios_adicionales: List[ServicioExtra] = []

    def calcular_total(self) -> Decimal:
        """Calcula el costo total sumando costo base y servicios adicionales."""
        total_extras = sum(servicio.costo for servicio in self.servicios_adicionales)
        return self.costo_base + total_extras

    def calcular_anticipo_requerido(self) -> Decimal:
        """Calcula automáticamente el 25% de anticipo requerido."""
        return self.calcular_total() * Decimal("0.25")

    def aprobar_cotizacion(self, monto_recibido: Decimal):
        """
        Transición de Estado: COTIZADO -> CONTRATADO
        Valida que el monto recibido sea al menos el 25% requerido.
        """
        if self.estado != EstadoContrato.COTIZADO:
            raise ValueError(f"El contrato no puede aprobarse desde el estado {self.estado.value}")
        
        anticipo_requerido = self.calcular_anticipo_requerido()
        
        if monto_recibido < anticipo_requerido:
            raise ValueError(f"Anticipo insuficiente. Se requiere al menos el 25% (${anticipo_requerido})")
        
        self.anticipo_pagado = monto_recibido
        self.estado = EstadoContrato.CONTRATADO