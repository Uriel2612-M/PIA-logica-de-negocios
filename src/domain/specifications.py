from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal

class Specification(ABC):
    @abstractmethod
    def is_satisfied_by(self, candidato) -> bool:
        pass

    # Operador AND (Requisito del profe)
    def __and__(self, other):
        return AndSpecification(self, other)

class AndSpecification(Specification):
    def __init__(self, spec1: Specification, spec2: Specification):
        self.spec1 = spec1
        self.spec2 = spec2

    def is_satisfied_by(self, candidato) -> bool:
        return self.spec1.is_satisfied_by(candidato) and self.spec2.is_satisfied_by(candidato)

# 1. Specification de Tiempo
class ContratoAdicionalSpecification(Specification):
    def __init__(self, fecha_actual: date):
        self.fecha_actual = fecha_actual

    def is_satisfied_by(self, contrato) -> bool:
        dias_restantes = (contrato.fecha_evento - self.fecha_actual).days
        return dias_restantes > 5

# 2. Specification de Presupuesto
class PresupuestoSpecification(Specification):
    def __init__(self, presupuesto_maximo: Decimal, costo_adicional: Decimal):
        self.presupuesto_maximo = presupuesto_maximo
        self.costo_adicional = costo_adicional

    def is_satisfied_by(self, contrato) -> bool:
        return (contrato.costo_base + self.costo_adicional) <= self.presupuesto_maximo

# 3. Specification de Cliente Activo (Tercera regla requerida)
class ClienteActivoSpecification(Specification):
    def is_satisfied_by(self, contrato) -> bool:
        # El cliente es válido si tiene un ID asignado
        return contrato.cliente_id is not None and contrato.cliente_id.strip() != ""