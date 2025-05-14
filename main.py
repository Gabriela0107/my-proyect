from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from passlib.context import CryptContext
import json
import os
import uvicorn
import sqlite3
from sqlite3 import Connection
import pandas as pd 

# Configuración inicial
app = FastAPI(
    title="SESACO - Seguridad Industrial S.A.",
    description="Sistema de Gestión de Verificación de Seguridad Industrial",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None
)

# Configuración de seguridad
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Modelos de datos
class Usuario(BaseModel):
    cedula: str
    hashed_password: str
    nombre: str
    rol: str = "inspector"

class Empresa(BaseModel):
    tipo: str  # Pública/Privada
    empleador: str
    razon_social: str
    ruc: str
    telefono: str
    correo: str
    actividad_economica: str
    tipo_centro: str  # Matriz/Sucursal
    direccion: str
    total_trabajadores: int
    consolidado_planilla: bool
    estadisticas: Dict[str, int]  # {hombres: int, mujeres: int, ...}
    horario_trabajo: str
    entrevistados: List[str]
    fecha_registro: datetime = datetime.now()

class PreguntaVerificacion(BaseModel):
    id: int
    seccion: str
    categoria: str
    pregunta: str
    normativa: str
    respuesta: Optional[str] = None  # Cumple/No cumple/No aplica
    observaciones: Optional[str] = None

class FormularioVerificacion(BaseModel):
    empresa_ruc: str
    inspector_cedula: str
    fecha: datetime = datetime.now()
    preguntas: List[PreguntaVerificacion]

# Base de datos inicial
DATABASE = {
    "usuarios": {
        "1722212253": Usuario(
            cedula="1722212253",
            hashed_password=pwd_context.hash("1722212253"),
            nombre="Inspector Principal",
            rol="admin"
        ).dict()
    },
    "empresas": {},
    "formularios": {}
}

# Cargar preguntas de verificación
def cargar_preguntas():
    try:
        with open("preguntas_verificacion.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"preguntas": []}

# Funciones de ayuda
def verificar_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_usuario(cedula: str) -> Optional[Usuario]:
    if cedula in DATABASE["usuarios"]:
        return Usuario(**DATABASE["usuarios"][cedula])
    return None

# Endpoints de Autenticación
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    usuario = get_usuario(form_data.username)
    if not usuario or not verificar_password(form_data.password, usuario.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cédula o contraseña incorrecta",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        "access_token": usuario.cedula,
        "token_type": "bearer",
        "nombre": usuario.nombre,
        "rol": usuario.rol
    }

@app.get("/usuarios/me")
async def read_usuario_actual(cedula: str = Depends(oauth2_scheme)):
    usuario = get_usuario(cedula)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

# Endpoints de Empresas
@app.get("/empresas/", response_model=List[Empresa])
async def listar_empresas(cedula: str = Depends(oauth2_scheme)):
    return list(DATABASE["empresas"].values())

@app.get("/empresas/{ruc}", response_model=Empresa)
async def buscar_empresa(ruc: str, cedula: str = Depends(oauth2_scheme)):
    if ruc in DATABASE["empresas"]:
        return DATABASE["empresas"][ruc]
    raise HTTPException(status_code=404, detail="Empresa no encontrada")

@app.post("/empresas/", response_model=Empresa)
async def crear_empresa(empresa: Empresa, cedula: str = Depends(oauth2_scheme)):
    if empresa.ruc in DATABASE["empresas"]:
        raise HTTPException(status_code=400, detail="Empresa ya registrada")
    DATABASE["empresas"][empresa.ruc] = empresa.dict()
    return empresa

# Endpoints de Formularios
@app.get("/formularios/estructura", response_model=Dict)
async def obtener_estructura_formulario():
    preguntas = cargar_preguntas()["preguntas"]
    estructura = {}
    for p in preguntas:
        if p["seccion"] not in estructura:
            estructura[p["seccion"]] = {}
        if p["categoria"] not in estructura[p["seccion"]]:
            estructura[p["seccion"]][p["categoria"]] = []
        estructura[p["seccion"]][p["categoria"]].append(p)
    return estructura

@app.post("/formularios/", response_model=FormularioVerificacion)
async def guardar_formulario(
    formulario: FormularioVerificacion, 
    cedula: str = Depends(oauth2_scheme)
):
    formulario.inspector_cedula = cedula
    formulario_id = f"{formulario.empresa_ruc}_{formulario.fecha.isoformat()}"
    DATABASE["formularios"][formulario_id] = formulario.dict()
    return formulario

@app.get("/formularios/{empresa_ruc}", response_model=List[FormularioVerificacion])
async def obtener_formularios_empresa(
    empresa_ruc: str, 
    cedula: str = Depends(oauth2_scheme)
):
    return [
        FormularioVerificacion(**f) 
        for f in DATABASE["formularios"].values() 
        if f["empresa_ruc"] == empresa_ruc
    ]

# Endpoint para generar reportes
@app.get("/reportes/{empresa_ruc}", response_model=Dict)
async def generar_reporte_empresa(
    empresa_ruc: str,
    cedula: str = Depends(oauth2_scheme)
):
    if empresa_ruc not in DATABASE["empresas"]:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    formularios = [
        FormularioVerificacion(**f)
        for f in DATABASE["formularios"].values()
        if f["empresa_ruc"] == empresa_ruc
    ]
    
    if not formularios:
        raise HTTPException(status_code=404, detail="No hay formularios para esta empresa")
    
    # Procesar estadísticas
    estadisticas = {
        "total_verificaciones": len(formularios),
        "ultima_verificacion": max(f.fecha for f in formularios).isoformat(),
        "cumplimiento_promedio": 0,
        "secciones": {}
    }
    
    preguntas_totales = 0
    cumplimientos_totales = 0
    
    for formulario in formularios:
        for pregunta in formulario.preguntas:
            if pregunta.respuesta == "✅ Cumple":
                cumplimientos_totales += 1
            preguntas_totales += 1
            
            # Estadísticas por sección
            if pregunta.seccion not in estadisticas["secciones"]:
                estadisticas["secciones"][pregunta.seccion] = {
                    "total": 0,
                    "cumple": 0,
                    "no_cumple": 0,
                    "no_aplica": 0
                }
            
            estadisticas["secciones"][pregunta.seccion]["total"] += 1
            if pregunta.respuesta == "✅ Cumple":
                estadisticas["secciones"][pregunta.seccion]["cumple"] += 1
            elif pregunta.respuesta == "❌ No cumple":
                estadisticas["secciones"][pregunta.seccion]["no_cumple"] += 1
            else:
                estadisticas["secciones"][pregunta.seccion]["no_aplica"] += 1
    
    if preguntas_totales > 0:
        estadisticas["cumplimiento_promedio"] = round(
            (cumplimientos_totales / preguntas_totales) * 100, 2
        )
    
    return {
        "empresa": DATABASE["empresas"][empresa_ruc],
        "estadisticas": estadisticas,
        "ultimo_formulario": formularios[-1].dict()
    }

@app.get("/matriz-riesgos/{empresa_ruc}", response_model=List[FormularioVerificacion])
async def obtener_matriz_riesgos(
    empresa_ruc: str, 
    cedula: str = Depends(oauth2_scheme)
):
    # Implementación básica - puedes personalizar esto según tus necesidades
    return [
        FormularioVerificacion(**f) 
        for f in DATABASE["formularios"].values() 
        if f["empresa_ruc"] == empresa_ruc
    ]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    