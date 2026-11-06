from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel
from datetime import date
from decimal import Decimal
from src.domain.contrato import Contrato, ServicioExtra, EstadoContrato
from src.domain.specifications import ContratoAdicionalSpecification, PresupuestoSpecification

app = FastAPI(
    title="API Eventos Nova",
    description="Implementación DDD y CQRS para Producto Integrador de Aprendizaje (PIA)",
    version="1.0.0"
)

# Simulador de Base de Datos en memoria para probar la lógica
fake_db = {
    "EVT-001": Contrato(
        contrato_id="EVT-001",
        cliente_id="CLI-999",
        fecha_evento=date(2026, 12, 15),
        costo_base=Decimal("10000.00")
    )
}

# --- Esquemas de Pydantic (Para Swagger UI) ---
class AprobarRequest(BaseModel):
    monto_recibido: Decimal

class AgregarServicioRequest(BaseModel):
    id_servicio: str
    costo: Decimal
    fecha_actual: date
    presupuesto_maximo_cliente: Decimal

# --- Endpoints ---

@app.post("/contratos/{contrato_id}/aprobar", tags=["Coordinador"], status_code=200)
def aprobar_cotizacion(
    monto_pago: AprobarRequest,
    contrato_id: str = Path(..., description="ID del contrato (ej. EVT-001)")
):
    """
    **Aprobar Cotización Inicial**
    Valida el anticipo recibido. Si cubre al menos el 25% del total, 
    cambia el estado de COTIZADO a CONTRATADO.
    """
    contrato = fake_db.get(contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    try:
        # Lógica del Agregado
        contrato.aprobar_cotizacion(monto_pago.monto_recibido)
        return {
            "mensaje": "Cotización aprobada y contrato activado exitosamente.",
            "estado_actual": contrato.estado.value,
            "anticipo_registrado": float(contrato.anticipo_pagado)
        }
    except ValueError as e:
        # Retorna 400 o 422 si se rompe la regla de negocio
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/contratos/{contrato_id}/servicios-extra", tags=["Coordinador"], status_code=201)
def agregar_servicio_extra(
    request: AgregarServicioRequest,
    contrato_id: str = Path(..., description="ID del contrato (ej. EVT-001)")
):
    """
    **Agregar Servicio Adicional**
    Aplica el patrón Specification para validar dos reglas de negocio:
    1. Faltan más de 5 días para el evento.
    2. El costo no excede el presupuesto autorizado por el cliente.
    """
    contrato = fake_db.get(contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    # 1. Ejecutar Specification de Tiempo
    regla_tiempo = ContratoAdicionalSpecification(request.fecha_actual)
    if not regla_tiempo.is_satisfied_by(contrato):
        raise HTTPException(
            status_code=409, 
            detail="Cambio rechazado: Faltan 5 días o menos para el evento."
        )

    # 2. Ejecutar Specification de Presupuesto
    regla_presupuesto = PresupuestoSpecification(
        request.presupuesto_maximo_cliente, request.costo
    )
    if not regla_presupuesto.is_satisfied_by(contrato):
        raise HTTPException(
            status_code=409, 
            detail="Límite financiero excedido: El servicio supera el presupuesto autorizado."
        )

    # Si pasa las Specifications, se agrega el servicio
    nuevo_servicio = ServicioExtra(request.id_servicio, request.costo)
    contrato.servicios_adicionales.append(nuevo_servicio)

    return {
        "mensaje": "Servicio adicional enlazado al contrato exitosamente.",
        "nuevo_total": float(contrato.calcular_total()),
        "cantidad_servicios_extra": len(contrato.servicios_adicionales)
    }