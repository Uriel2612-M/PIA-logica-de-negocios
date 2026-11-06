from fastapi import FastAPI, HTTPException, Path, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import date, datetime
from decimal import Decimal
import csv
import os


from src.domain.contrato import Contrato, EstadoContrato
from src.domain.specifications import ContratoAdicionalSpecification, PresupuestoSpecification


from src.infrastructure.database import engine, get_db, Base
from src.infrastructure.models import ContratoModel

app = FastAPI(
    title="Eventos Nova",
    description="Implementación PIA",
)

@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    
    db = next(get_db())
    if db.query(ContratoModel).count() == 0:
        csv_path = "data/contratos.csv"
        if os.path.exists(csv_path):
            with open(csv_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    nuevo_contrato = ContratoModel(
                        contrato_id=row['contrato_id'],
                        cliente_id=row['cliente_id'],
                        fecha_evento=datetime.strptime(row['fecha_evento'], '%Y-%m-%d').date(),
                        costo_base=Decimal(row['costo_base']),
                        estado=row.get('estado', 'COTIZADO')
                    )
                    db.add(nuevo_contrato)
            db.commit()
            print("Datos iniciales del CSV cargados exitosamente.")

class AprobarRequest(BaseModel):
    monto_recibido: Decimal

class AgregarServicioRequest(BaseModel):
    id_servicio: str
    costo: Decimal
    fecha_actual: date
    presupuesto_maximo_cliente: Decimal


@app.post("/contratos/{contrato_id}/aprobar", tags=["Coordinador"], status_code=200)
def aprobar_cotizacion(
    monto_pago: AprobarRequest,
    contrato_id: str = Path(...),
    db: Session = Depends(get_db)
):

    contrato_db = db.query(ContratoModel).filter(ContratoModel.contrato_id == contrato_id).first()
    if not contrato_db:
        raise HTTPException(status_code=404, detail="Contrato no encontrado en la base de datos")

    contrato = Contrato(
        contrato_id=contrato_db.contrato_id,
        cliente_id=contrato_db.cliente_id,
        fecha_evento=contrato_db.fecha_evento,
        costo_base=contrato_db.costo_base
    )
    contrato.estado = EstadoContrato(contrato_db.estado)

    try:
        contrato.aprobar_cotizacion(monto_pago.monto_recibido)
        
        contrato_db.estado = contrato.estado.value
        contrato_db.anticipo_pagado = contrato.anticipo_pagado
        db.commit()
        
        return {
            "mensaje": "Cotización aprobada y contrato activado.",
            "estado_actual": contrato_db.estado,
            "anticipo_registrado": float(contrato_db.anticipo_pagado)
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/contratos/{contrato_id}/servicios-extra", tags=["Coordinador"], status_code=201)
def agregar_servicio_extra(
    request: AgregarServicioRequest,
    contrato_id: str = Path(...),
    db: Session = Depends(get_db)
):
    contrato_db = db.query(ContratoModel).filter(ContratoModel.contrato_id == contrato_id).first()
    if not contrato_db:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    contrato = Contrato(
        contrato_id=contrato_db.contrato_id,
        cliente_id=contrato_db.cliente_id,
        fecha_evento=contrato_db.fecha_evento,
        costo_base=contrato_db.costo_base
    )


    regla_tiempo = ContratoAdicionalSpecification(request.fecha_actual)
    if not regla_tiempo.is_satisfied_by(contrato):
        raise HTTPException(status_code=409, detail="Rechazado: Faltan 5 días o menos para el evento.")

    regla_presupuesto = PresupuestoSpecification(request.presupuesto_maximo_cliente, request.costo)
    if not regla_presupuesto.is_satisfied_by(contrato):
        raise HTTPException(status_code=409, detail="Rechazado: El servicio supera el presupuesto autorizado.")

    contrato_db.costo_base += request.costo
    db.commit()

    return {
        "mensaje": "Servicio adicional validado e integrado al contrato.",
        "nuevo_costo_base": float(contrato_db.costo_base)
    }