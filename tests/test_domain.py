import pytest
from datetime import date
from decimal import Decimal
from src.domain.contrato import Contrato, EstadoContrato, ContratoActivadoEvent
from src.domain.specifications import (
    ContratoAdicionalSpecification,
    PresupuestoSpecification,
    ClienteActivoSpecification
)

def test_aprobar_cotizacion_calcula_anticipo():
    # Valida la historia de usuario US-04 y US-05
    contrato = Contrato("EVE-001", "CLI-001", date(2026, 12, 1), Decimal("10000.00"))
    
    # 25% de 10000 es 2500. Un pago menor debe arrojar error.
    with pytest.raises(ValueError, match="El anticipo debe ser de al menos el 25%"):
        contrato.aprobar_cotizacion(Decimal("2000.00"))

    # Pago exacto activa el contrato
    contrato.aprobar_cotizacion(Decimal("2500.00"))
    assert contrato.anticipo_pagado == Decimal("2500.00")
    assert contrato.estado == EstadoContrato.CONTRATADO

def test_domain_event_al_aprobar():
    # Valida el requisito del profesor sobre eventos de dominio
    contrato = Contrato("EVE-001", "CLI-001", date(2026, 12, 1), Decimal("10000.00"))
    contrato.aprobar_cotizacion(Decimal("3000.00"))
    
    assert len(contrato.domain_events) == 1
    assert isinstance(contrato.domain_events[0], ContratoActivadoEvent)
    assert contrato.domain_events[0].contrato_id == "EVE-001"

def test_especificacion_tiempo():
    # Valida la historia de usuario US-08 (Límite de 5 días)
    fecha_evento = date(2026, 10, 10)
    contrato = Contrato("EVE-001", "CLI-001", fecha_evento, Decimal("10000.00"))
    
    # Faltan 6 días (Pasa)
    spec_ok = ContratoAdicionalSpecification(date(2026, 10, 4))
    assert spec_ok.is_satisfied_by(contrato) is True
    
    # Faltan 5 días exactos o menos (Falla)
    spec_fail = ContratoAdicionalSpecification(date(2026, 10, 5))
    assert spec_fail.is_satisfied_by(contrato) is False

def test_especificacion_presupuesto():
    # Valida la historia de usuario US-11 (Bloqueo de presupuesto)
    contrato = Contrato("EVE-001", "CLI-001", date(2026, 12, 1), Decimal("10000.00"))
    
    # Costo 10k + 3k = 13k. Límite 15k (Pasa)
    spec_ok = PresupuestoSpecification(Decimal("15000.00"), Decimal("3000.00"))
    assert spec_ok.is_satisfied_by(contrato) is True
    
    # Costo 10k + 3k = 13k. Límite 11k (Falla)
    spec_fail = PresupuestoSpecification(Decimal("11000.00"), Decimal("3000.00"))
    assert spec_fail.is_satisfied_by(contrato) is False

def test_especificacion_compuesta_and():
    # Valida el requisito estricto del profe de combinar 3 reglas con AND
    contrato = Contrato("EVE-001", "CLI-001", date(2026, 10, 10), Decimal("10000.00"))
    
    regla_tiempo = ContratoAdicionalSpecification(date(2026, 10, 1)) 
    regla_pres = PresupuestoSpecification(Decimal("15000.00"), Decimal("2000.00")) 
    regla_cliente = ClienteActivoSpecification() 
    
    # Operador AND mágico
    regla_compuesta = regla_tiempo & regla_pres & regla_cliente
    assert regla_compuesta.is_satisfied_by(contrato) is True
    
    # Hacemos que una sola falle (el tiempo) para comprobar que bloquea todo
    regla_tiempo_falla = ContratoAdicionalSpecification(date(2026, 10, 8))
    regla_compuesta_falla = regla_tiempo_falla & regla_pres & regla_cliente
    assert regla_compuesta_falla.is_satisfied_by(contrato) is False