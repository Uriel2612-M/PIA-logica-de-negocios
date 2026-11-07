from fastapi import FastAPI, HTTPException, Path, Depends, Form
from sqlalchemy.orm import Session
from datetime import date, datetime
from decimal import Decimal
import csv
import os

from src.domain.contrato import Contrato, EstadoContrato
from src.domain.specifications import ContratoAdicionalSpecification, PresupuestoSpecification, ClienteActivoSpecification
from src.infrastructure.database import engine, get_db, Base
from src.infrastructure.models import ContratoModel, ServicioModel 

app = FastAPI(
    title="Sistema Eventos Nova",
    description="Panel de administración para coordinadores de eventos.",
    version="1.0.0"
)

@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    
    # 1. Cargar Operaciones (Contratos)
    if db.query(ContratoModel).count() == 0:
        csv_path = "data/operaciones.csv"
        if os.path.exists(csv_path):
            with open(csv_path, mode='r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    nuevo_contrato = ContratoModel(
                        contrato_id=row['operacion_id'],  
                        cliente_id=row['actor_id'],       
                        fecha_evento=datetime.strptime(row['fecha_solicitud'], '%Y-%m-%d').date(),
                        costo_base=Decimal("10000.00"),   
                        estado=row.get('estado_inicial', 'COTIZADO')
                    )
                    db.add(nuevo_contrato)
            db.commit()
            
    # 2. Cargar Catálogo de Servicios
    if db.query(ServicioModel).count() == 0:
        csv_catalogo = "data/catalogo.csv"
        if os.path.exists(csv_catalogo):
            with open(csv_catalogo, mode='r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    nuevo_servicio = ServicioModel(
                        id_servicio=row['recurso_id'],
                        descripcion=row['descripcion'],
                        precio=Decimal(row['precio_mxn'])
                    )
                    db.add(nuevo_servicio)
            db.commit()
            print("Datos de operaciones y catálogo cargados exitosamente.")

@app.post("/cobrar-anticipo", tags=["Gestión de Eventos"], summary="Paso 1: Cobrar Anticipo", status_code=200)
def registrar_anticipo(
    folio_evento: str = Form(..., title="Folio del Evento", description="Ejemplo: EVE-O001"),
    monto_recibido: Decimal = Form(..., title="Monto del Pago (MXN)", example=2500.00),
    db: Session = Depends(get_db)
):
    contrato_db = db.query(ContratoModel).filter(ContratoModel.contrato_id == folio_evento).first()
    if not contrato_db:
        raise HTTPException(status_code=404, detail="El folio del evento no existe en la base de datos.")

    contrato = Contrato(contrato_db.contrato_id, contrato_db.cliente_id, contrato_db.fecha_evento, contrato_db.costo_base)
    contrato.estado = EstadoContrato(contrato_db.estado)

    try:
        contrato.aprobar_cotizacion(monto_recibido)
        contrato_db.estado = contrato.estado.value
        contrato_db.anticipo_pagado = contrato.anticipo_pagado
        db.commit()
        
        # Un solo return que incluye el evento de dominio
        return {
            "mensaje": "Pago registrado con éxito.", 
            "estado": contrato_db.estado,
            "evento_disparado": contrato.domain_events[0].mensaje 
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Error al procesar: {str(e)}")

@app.post("/agregar-servicio-extra", tags=["Gestión de Eventos"], summary="Paso 2: Agregar Servicio", status_code=201)
def agregar_servicio(
    folio_evento: str = Form(..., title="Folio del Evento", description="Ejemplo: EVE-O001"),
    id_servicio: str = Form(..., title="Clave del Servicio", description="Búscalo en el catálogo (ej. EVE-P009)"),
    fecha_actual: date = Form(..., title="Fecha de Hoy", example="2026-11-06"),
    presupuesto_maximo_cliente: Decimal = Form(..., title="Presupuesto Máximo Autorizado", example=15000.00),
    db: Session = Depends(get_db)
):
    contrato_db = db.query(ContratoModel).filter(ContratoModel.contrato_id == folio_evento).first()
    if not contrato_db:
        raise HTTPException(status_code=404, detail="El folio del evento no existe.")

    servicio_db = db.query(ServicioModel).filter(ServicioModel.id_servicio == id_servicio).first()
    if not servicio_db:
        raise HTTPException(status_code=404, detail="El código de servicio no existe en el catálogo.")
    
    costo_real = servicio_db.precio 

    contrato = Contrato(contrato_db.contrato_id, contrato_db.cliente_id, contrato_db.fecha_evento, contrato_db.costo_base)
    
    regla_tiempo = ContratoAdicionalSpecification(fecha_actual)
    regla_presupuesto = PresupuestoSpecification(presupuesto_maximo_cliente, costo_real)
    regla_cliente = ClienteActivoSpecification()
    
    regla_compuesta = regla_tiempo & regla_presupuesto & regla_cliente
    
    if not regla_compuesta.is_satisfied_by(contrato):
        raise HTTPException(
            status_code=409, 
            detail=f"Bloqueado por Reglas de Negocio: No se cumple el límite de 5 días, el presupuesto máximo (${presupuesto_maximo_cliente}), o el cliente es inválido."
        )

    contrato_db.costo_base += costo_real
    db.commit()
    
    return {
        "mensaje": f"Servicio '{servicio_db.descripcion}' agregado correctamente.", 
        "costo_servicio": float(costo_real),
        "nuevo_total_evento": float(contrato_db.costo_base)
    }