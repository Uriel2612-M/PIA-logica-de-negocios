from sqlalchemy import Column, String, Date, Numeric
from src.infrastructure.database import Base

class ContratoModel(Base):
    __tablename__ = "contratos"

    contrato_id = Column(String, primary_key=True, index=True)
    cliente_id = Column(String, index=True)
    fecha_evento = Column(Date, nullable=False)
    
    costo_base = Column(Numeric(10, 2), nullable=False)
    estado = Column(String, default="COTIZADO", nullable=False)
    anticipo_pagado = Column(Numeric(10, 2), default=0.00)

from sqlalchemy import Column, String, Numeric

class ServicioModel(Base):
    __tablename__ = "catalogo_servicios"
    
    id_servicio = Column(String, primary_key=True, index=True)
    descripcion = Column(String, nullable=False)
    precio = Column(Numeric(10, 2), nullable=False)