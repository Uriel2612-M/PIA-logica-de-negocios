from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from src.domain.contrato import Contrato

# Interfaz base obligatoria para el patrón Specification
class ISpecification(ABC):
    @abstractmethod
    def is_satisfied_by(self, candidato: Contrato) -> bool:
        pass

# 1. Regla de Tiempo: Cambios Normales (> 10 días)
class LimiteCambiosSpecification(ISpecification):
    def __init__(self, fecha_actual: date):
        self.fecha_actual = fecha_actual

    def is_satisfied_by(self, contrato: Contrato) -> bool:
        dias_restantes = (contrato.fecha_evento - self.fecha_actual).days
        return dias_restantes > 10

# 2. Regla de Tiempo: Servicios Extra (> 5 días)
class ContratoAdicionalSpecification(ISpecification):
    def __init__(self, fecha_actual: date):
        self.fecha_actual = fecha_actual

    def is_satisfied_by(self, contrato: Contrato) -> bool:
        dias_restantes = (contrato.fecha_evento - self.fecha_actual).days
        return dias_restantes > 5

# 3. Regla Financiera: Bloqueo de Presupuesto
class PresupuestoSpecification(ISpecification):
    def __init__(self, presupuesto_maximo: Decimal, costo_nuevo_servicio: Decimal):
        self.presupuesto_maximo = presupuesto_maximo
        self.costo_nuevo_servicio = costo_nuevo_servicio

    def is_satisfied_by(self, contrato: Contrato) -> bool:
        # Verifica si al sumar el nuevo servicio se excede el límite
        costo_proyectado = contrato.calcular_total() + self.costo_nuevo_servicio
        return costo_proyectado <= self.presupuesto_maximo