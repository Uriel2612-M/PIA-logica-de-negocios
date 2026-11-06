import pytest
from datetime import date
from decimal import Decimal
from src.domain.contrato import Contrato, EstadoContrato, ServicioExtra
from src.domain.specifications import LimiteCambiosSpecification, PresupuestoSpecification

def test_calcular_anticipo_requerido(): 
    contrato = Contrato("EVT-001", "CLI-999", date(2026, 12, 15), Decimal("10000.00"))
    
    anticipo = contrato.calcular_anticipo_requerido()
    
    assert anticipo == Decimal("2500.00") # 25% de 10,000

def test_aprobar_cotizacion_cambia_estado():
    contrato = Contrato("EVT-001", "CLI-999", date(2026, 12, 15), Decimal("10000.00"))
    contrato.aprobar_cotizacion(Decimal("2500.00"))
    
    assert contrato.estado == EstadoContrato.CONTRATADO
    assert contrato.anticipo_pagado == Decimal("2500.00")

def test_aprobar_cotizacion_rechaza_anticipo_insuficiente():
    contrato = Contrato("EVT-001", "CLI-999", date(2026, 12, 15), Decimal("10000.00"))
    
    with pytest.raises(ValueError, match="Anticipo insuficiente"):
        contrato.aprobar_cotizacion(Decimal("1000.00"))

def test_specification_bloquea_exceso_presupuesto():
    contrato = Contrato("EVT-001", "CLI-999", date(2026, 12, 15), Decimal("10000.00"))
    regla = PresupuestoSpecification(presupuesto_maximo=Decimal("12000.00"), costo_nuevo_servicio=Decimal("3000.00"))
    
    assert regla.is_satisfied_by(contrato) is False