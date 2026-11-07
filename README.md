# Eventos Nova - Sistema de Gestión Centralizada

Este proyecto es el Producto Integrador de Aprendizaje (PIA) para la materia de Componentes de Lógica de Negocios. Consiste en una API REST robusta diseñada para resolver las fallas operativas, de comunicación y control financiero de la empresa Eventos Nova.

## Arquitectura y Patrones de Diseño

El sistema está construido bajo los principios de **Diseño Orientado a Dominios (DDD)** y Arquitectura Limpia, aislando las reglas de negocio de la infraestructura tecnológica. 

Se implementaron los siguientes patrones tácticos:
*   **Domain Model:** Entidades, Value Objects y Agregados (raíz `Contrato`) para proteger los invariantes del negocio.
*   **State Machine:** Control estricto del ciclo de vida del evento (Cotizado -> Contratado -> En Preparación).
*   **Specification Pattern:** Validación combinada (AND) para reglas de tiempo (límite de 5 días), presupuesto máximo autorizado y validación de clientes activos.
*   **Domain Events:** Emisión de eventos para notificar a proveedores cuando un contrato cambia de estado.
*   **Data Seeding:** Población automática de la base de datos a partir de archivos `.csv` maestros al arrancar el sistema.

## Stack Tecnológico

*   **Backend:** Python 3.13 + FastAPI
*   **Base de Datos:** PostgreSQL
*   **ORM:** SQLAlchemy
*   **Orquestación:** Docker + Docker Compose
*   **Calidad (CI/CD):** Pytest + GitHub Actions

## Instrucciones de Despliegue Local

El proyecto está completamente contenerizado, por lo que no es necesario instalar Python ni bases de datos localmente, únicamente Docker.

1. **Clonar el repositorio:**
   ```bash
   git clone <URL_DE_TU_REPOSITORIO>
   cd PIA-logica-de-negocios

Levantar la infraestructura:

Bash
docker-compose up -d --build
Nota: Este comando descargará las imágenes, levantará el motor de PostgreSQL, ejecutará el seeding de los archivos CSV (Operaciones y Catálogo) y encenderá la API.

Acceder a la Interfaz y Documentación:
Una vez que los contenedores estén corriendo, abre tu navegador web y dirígete a:
http://localhost:8000/docs

Apagar el sistema:

Bash
docker-compose down

Pruebas Automatizadas

El proyecto cuenta con una suite de pruebas unitarias que validan los invariantes del dominio y el comportamiento de la API.

Para ejecutarlas localmente dentro del contenedor:
Bash
docker-compose run app pytest --cov=src

Equipo de Desarrollo
José Uriel Hernández Hernández
Carlos Tomas Cárdenas Vázquez
Pamela López Martínez
Jaime Guerra Jr