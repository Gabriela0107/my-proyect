import streamlit as st
import requests
from datetime import datetime
import time
import pandas as pd
import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from fpdf import FPDF
import tempfile

st.set_page_config(
    page_title="Gestión de Seguridad y Salud en el Trabajo",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URL del backend
BACKEND_URL = "http://localhost:8000"

# Estado de la sesión
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user_info' not in st.session_state:
    st.session_state.user_info = {}
if 'current_page' not in st.session_state:
    st.session_state.current_page = "inicio"
if 'empresa_actual' not in st.session_state:
    st.session_state.empresa_actual = None
if 'preguntas_verificacion' not in st.session_state:
    st.session_state.preguntas_verificacion = {}
if 'previous_page' not in st.session_state:
    st.session_state.previous_page = None

# Colores principales según la imagen
COLORES = {
    "verde_bosque": "#006b3f",
    "verde_hierba": "#6bbe44",
    "gris_claro": "#f2f2f2",
    "gris_oscuro": "#333333",
    "negro": "#1a1a1a",
    "blanco": "#ffffff"
}

# Estilos CSS personalizados con la paleta de colores proporcionada
def load_css():
    st.markdown(f"""
    <style>
        :root {{
            --primary: {COLORES["verde_bosque"]};
            --secondary: {COLORES["verde_hierba"]};
            --accent: {COLORES["verde_hierba"]};
            --background: {COLORES["gris_claro"]};
            --text: {COLORES["negro"]};
            --header-text: {COLORES["blanco"]};
        }}
        
        body {{
            background-color: var(--background);
            color: var(--text);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        
        .stApp {{
            background: {COLORES["gris_claro"]};
        }}
        
        .header {{
            background-color: {COLORES["verde_bosque"]};
            color: {COLORES["blanco"]};
            padding: 1rem;
            margin-bottom: 2rem;
            border-radius: 0 0 10px 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .header-title {{
            color: {COLORES["blanco"]};
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}
        
        .header-subtitle {{
            color: {COLORES["blanco"]};
            font-size: 1.1rem;
            opacity: 0.9;
        }}
        
        .stButton>button {{
            background-color: var(--primary);
            color: white;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            border: none;
            font-weight: 500;
            transition: all 0.3s ease;
        }}
        
        .stButton>button:hover {{
            background-color: var(--accent);
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        
        .back-button {{
            background-color: {COLORES["gris_claro"]} !important;
            color: var(--primary) !important;
            border: 1px solid var(--primary) !important;
        }}
        
        .back-button:hover {{
            background-color: #e8f5e9 !important;
        }}
        
        .stTextInput>div>div>input, 
        .stTextArea>div>div>textarea, 
        .stSelectbox>div>div>select,
        .stNumberInput>div>div>input {{
            border-radius: 8px;
            border: 1px solid {COLORES["verde_hierba"]};
            padding: 0.5rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }}
        
        .sidebar .sidebar-content {{
            background-color: var(--primary);
            color: white;
            padding: 1rem;
        }}
        
        h1, h2, h3, h4 {{
            color: var(--primary);
            margin-top: 0;
        }}
        
        .custom-card {{
            background-color: white;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 1.5rem;
            border-left: 4px solid var(--accent);
        }}
        
        .pregunta-card {{
            background-color: #f8f9fa;
            border-left: 4px solid {COLORES["verde_hierba"]};
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        }}
        
        .pregunta-card:hover {{
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }}
        
        .pregunta-header {{
            color: {COLORES["verde_bosque"]};
            font-weight: 600;
            margin-bottom: 0.5rem;
            font-size: 1.1rem;
        }}
        
        .normativa-text {{
            font-size: 0.85rem;
            color: #666;
            font-style: italic;
            margin-bottom: 0.5rem;
        }}
        
        .gestion-text {{
            font-size: 0.9rem;
            font-weight: 500;
            color: {COLORES["verde_bosque"]};
            margin-bottom: 0.5rem;
        }}
        
        .observaciones-box {{
            background-color: #fff8e1;
            border-radius: 6px;
            padding: 0.75rem;
            margin-top: 0.75rem;
            border-left: 3px solid #FFC107;
        }}
        
        .success {{ color: {COLORES["verde_bosque"]}; }}
        .warning {{ color: #FF8F00; }}
        .error {{ color: #C62828; }}
        
        .stRadio>div>label {{
            margin-right: 1rem;
        }}
        
        .st-expander {{
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        
        .st-expander .streamlit-expanderHeader {{
            font-weight: 600;
            color: var(--primary);
        }}
        
        .metric-card {{
            background-color: white;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 1rem;
            border-left: 4px solid var(--accent);
        }}
        
        .verification-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 1rem;
        }}
        
        .verification-table th {{
            background-color: {COLORES["verde_bosque"]};
            color: white;
            padding: 0.5rem;
            text-align: left;
        }}
        
        .verification-table td {{
            padding: 0.5rem;
            border: 1px solid #ddd;
        }}
        
        .verification-table tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        
        .planes-section {{
            background-color: {COLORES["gris_claro"]};
            padding: 2rem;
            border-radius: 10px;
            margin-top: 2rem;
            text-align: center;
        }}
        
        .planes-title {{
            color: {COLORES["verde_bosque"]};
            font-size: 1.5rem;
            margin-bottom: 1rem;
            font-weight: 600;
        }}
        
        .planes-subtitle {{
            color: {COLORES["negro"]};
            font-size: 1.1rem;
            margin-bottom: 1.5rem;
        }}
        
        .plan-card {{
            background-color: white;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin: 1rem;
            border-top: 4px solid {COLORES["verde_hierba"]};
            transition: all 0.3s ease;
        }}
        
        .plan-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.1);
        }}
        
        .plan-name {{
            color: {COLORES["verde_bosque"]};
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }}
        
        .plan-price {{
            color: {COLORES["verde_hierba"]};
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
        }}
        
        .plan-features {{
            text-align: left;
            margin-bottom: 1.5rem;
        }}
        
        .feature-item {{
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
        }}
        
        .feature-icon {{
            color: {COLORES["verde_hierba"]};
            margin-right: 0.5rem;
        }}
    </style>
    """, unsafe_allow_html=True)

load_css()

def show_header():
    st.markdown(f"""
    <div class="header">
        <div class="header-title">GESTIÓN DE SEGURIDAD Y SALUD EN EL TRABAJO</div>
        <div class="header-subtitle">CONSULTA NUESTROS PLANES EMPRESARIALES Y PREMIUM</div>
        <div class="header-subtitle">PARA EMPRESAS PEQUEÑAS, MEDIANAS Y GRANDES CON TODO TIPO DE MESSOS.</div>
    </div>
    """, unsafe_allow_html=True)

def go_back():
    if st.session_state.previous_page:
        st.session_state.current_page = st.session_state.previous_page
        st.rerun()
    else:
        st.session_state.current_page = "dashboard"
        st.rerun()

# Página de inicio de sesión
def login_page():
    show_header()
    
    st.markdown("### Desafío")
    st.markdown("""
    Bienvenido al sistema de gestión de seguridad y salud en el trabajo. 
    Por favor inicie sesión para acceder a todas las funcionalidades.
    """)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image("https://via.placeholder.com/300x200?text=Logo+Empresa", width=250)
    
    with col2:
        with st.form("login_form"):
            cedula = st.text_input("Cédula", placeholder="Ingrese su número de cédula", key="cedula_input")
            password = st.text_input("Contraseña", type="password", placeholder="Ingrese su contraseña", key="password_input")
            submit_button = st.form_submit_button("Iniciar Sesión", type="primary")
            
            if submit_button:
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/token",
                        data={"username": cedula, "password": password},
                        headers={"Content-Type": "application/x-www-form-urlencoded"}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.logged_in = True
                        st.session_state.token = data["access_token"]
                        st.session_state.user_info = {
                            "nombre": data["nombre"],
                            "cedula": cedula,
                            "rol": data.get("rol", "inspector")
                        }
                        st.session_state.current_page = "dashboard"
                        st.rerun()
                    else:
                        st.error("Cédula o contraseña incorrecta")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error al conectar con el servidor: {str(e)}")

# Página principal
def dashboard_page():
    show_header()
    
    st.sidebar.title("Menú Principal")
    st.sidebar.markdown(f"""
    **Usuario:** {st.session_state.user_info['nombre']}  
    **Rol:** {st.session_state.user_info['rol'].capitalize()}
    """)
    
    menu_options = {
        "🏠 Inicio": "dashboard",
        "🏢 Gestión de Empresas": "gestion_empresas",
        "📋 Formulario de Verificación": "formulario_verificacion",
        "📊 Reportes y Estadísticas": "reportes"
    }
    
    for option, page in menu_options.items():
        if st.sidebar.button(option, key=f"menu_{page}"):
            st.session_state.previous_page = st.session_state.current_page
            st.session_state.current_page = page
            st.rerun()
    
    if st.sidebar.button("🔒 Cerrar Sesión", type="primary"):
        st.session_state.logged_in = False
        st.session_state.token = None
        st.session_state.current_page = "inicio"
        st.rerun()
    
    st.title(f"Bienvenido, {st.session_state.user_info['nombre']}")
    st.markdown("---")
    
    st.markdown("""
    ### Sistema Integral de Gestión de Seguridad y Salud en el Trabajo
    
    Ofrecemos soluciones completas para la gestión y verificación del cumplimiento 
    de normativas de seguridad en el ambiente laboral para empresas de todos los tamaños.
    """)
    
    # Sección de planes empresariales
    st.markdown("""
    <div class="planes-section">
        <div class="planes-title">NUESTROS PLANES EMPRESARIALES</div>
        <div class="planes-subtitle">Soluciones adaptadas a las necesidades de su empresa</div>
        
        <div style="display: flex; justify-content: center; flex-wrap: wrap;">
            <div class="plan-card" style="flex: 1; min-width: 300px;">
                <div class="plan-name">PLAN BÁSICO</div>
                <div class="plan-price">$99/mes</div>
                <div class="plan-features">
                    <div class="feature-item"><span class="feature-icon">✓</span> Hasta 10 trabajadores</div>
                    <div class="feature-item"><span class="feature-icon">✓</span> Gestión documental básica</div>
                    <div class="feature-item"><span class="feature-icon">✓</span> Soporte por correo</div>
                </div>
                <button class="stButton">Contratar</button>
            </div>
            
            <div class="plan-card" style="flex: 1; min-width: 300px;">
                <div class="plan-name">PLAN EMPRESARIAL</div>
                <div class="plan-price">$199/mes</div>
                <div class="plan-features">
                    <div class="feature-item"><span class="feature-icon">✓</span> Hasta 50 trabajadores</div>
                    <div class="feature-item"><span class="feature-icon">✓</span> Gestión documental completa</div>
                    <div class="feature-item"><span class="feature-icon">✓</span> Soporte prioritario</div>
                    <div class="feature-item"><span class="feature-icon">✓</span> Informes mensuales</div>
                </div>
                <button class="stButton">Contratar</button>
            </div>
            
            <div class="plan-card" style="flex: 1; min-width: 300px;">
                <div class="plan-name">PLAN PREMIUM</div>
                <div class="plan-price">$399/mes</div>
                <div class="plan-features">
                    <div class="feature-item"><span class="feature-icon">✓</span> Trabajadores ilimitados</div>
                    <div class="feature-item"><span class="feature-icon">✓</span> Gestión integral</div>
                    <div class="feature-item"><span class="feature-icon">✓</span> Soporte 24/7</div>
                    <div class="feature-item"><span class="feature-icon">✓</span> Auditorías periódicas</div>
                    <div class="feature-item"><span class="feature-icon">✓</span> Capacitaciones incluidas</div>
                </div>
                <button class="stButton">Contratar</button>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

load_css()

def go_back():
    if st.session_state.previous_page:
        st.session_state.current_page = st.session_state.previous_page
        st.rerun()
    else:
        st.session_state.current_page = "dashboard"
        st.rerun()

# Página de inicio de sesión
def login_page():
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image("https://via.placeholder.com/300x200?text=SESACO+Logo", width=250)
    
    with col2:
        st.title("SESACO - Seguridad Industrial S.A.")
        st.markdown("---")
        
        with st.form("login_form"):
            cedula = st.text_input("Cédula", placeholder="1722212253", key="cedula_input")
            password = st.text_input("Contraseña", type="password", placeholder="1722212253", key="password_input")
            submit_button = st.form_submit_button("Iniciar Sesión", type="primary")
            
            if submit_button:
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/token",
                        data={"username": cedula, "password": password},
                        headers={"Content-Type": "application/x-www-form-urlencoded"}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.logged_in = True
                        st.session_state.token = data["access_token"]
                        st.session_state.user_info = {
                            "nombre": data["nombre"],
                            "cedula": cedula,
                            "rol": data.get("rol", "inspector")
                        }
                        st.session_state.current_page = "dashboard"
                        st.rerun()
                    else:
                        st.error("Cédula o contraseña incorrecta")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error al conectar con el servidor: {str(e)}")

# Página principal
def dashboard_page():
    st.sidebar.title("Menú Principal")
    st.sidebar.markdown(f"""
    **Usuario:** {st.session_state.user_info['nombre']}  
    **Rol:** {st.session_state.user_info['rol'].capitalize()}
    """)
    
    menu_options = {
        "🏠 Inicio": "dashboard",
        "🏢 Gestión de Empresas": "gestion_empresas",
        "📋 Formulario de Verificación": "formulario_verificacion",
        "📊 Reportes y Estadísticas": "reportes"
    }
    
    for option, page in menu_options.items():
        if st.sidebar.button(option, key=f"menu_{page}"):
            st.session_state.previous_page = st.session_state.current_page
            st.session_state.current_page = page
            st.rerun()
    
    if st.sidebar.button("🔒 Cerrar Sesión", type="primary"):
        st.session_state.logged_in = False
        st.session_state.token = None
        st.session_state.current_page = "inicio"
        st.rerun()
    
    st.title(f"Bienvenido, {st.session_state.user_info['nombre']}")
    st.markdown("---")
    
    st.markdown("""
    ### Sistema Integral de Verificación de Seguridad Industrial
    
    **SESACO Seguridad Industrial S.A.** ofrece soluciones completas para la gestión y verificación 
    del cumplimiento de normativas de seguridad en el ambiente laboral.
    """)
    
    # Tarjeta de métricas
    with st.container():
        st.markdown("""
        <div class='custom-card'>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Empresas Registradas", "28", "+3 este mes")
        col2.metric("Verificaciones", "156", "15% más que el mes pasado")
        col3.metric("Cumplimiento Promedio", "82%", "5% mejor que el promedio")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("### Acciones Rápidas")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Buscar Empresa", use_container_width=True):
            st.session_state.previous_page = st.session_state.current_page
            st.session_state.current_page = "gestion_empresas"
            st.rerun()
    
    with col2:
        if st.button("📝 Nuevo Formulario", use_container_width=True):
            st.session_state.previous_page = st.session_state.current_page
            st.session_state.current_page = "formulario_verificacion"
            st.rerun()
    
    with col3:
        if st.button("📊 Generar Reporte", use_container_width=True):
            st.session_state.previous_page = st.session_state.current_page
            st.session_state.current_page = "reportes"
            st.rerun()

# Gestión de empresas
def gestion_empresas_page():
    if st.button("← Regresar", key="back_gestion", type="secondary", use_container_width=True, 
                help="Volver a la página anterior", on_click=go_back):
        return
    
    st.title("🏢 Gestión de Empresas")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["🔍 Buscar Empresa", "➕ Registrar Nueva Empresa"])
    
    with tab1:
        st.subheader("Buscar Empresa por RUC")
        ruc = st.text_input("Ingrese el RUC de la empresa", key="buscar_ruc")
        
        if st.button("Buscar", key="buscar_empresa_btn"):
            if ruc:
                try:
                    response = requests.get(
                        f"{BACKEND_URL}/empresas/{ruc}",
                        headers={"Authorization": f"Bearer {st.session_state.token}"}
                    )
                    if response.status_code == 200:
                        empresa = response.json()
                        st.session_state.empresa_actual = empresa
                        st.success("Empresa encontrada")
                    else:
                        st.warning("No se encontró una empresa con ese RUC")
                except requests.exceptions.RequestException:
                    st.error("Error al conectar con el servidor")
            else:
                st.warning("Por favor ingrese un RUC")
        
        if 'empresa_actual' in st.session_state and st.session_state.empresa_actual:
            display_empresa_info(st.session_state.empresa_actual)
    
    with tab2:
        st.subheader("Registrar Nueva Empresa")
        with st.form("empresa_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                inspeccion = st.text_input("Inspección")
                fecha = st.date_input("Fecha")
                re_inspeccion = st.text_input("Re-inspección", placeholder="Ej: L-V 01/01/2000")
                fecha_inspeccion = st.date_input("Fecha de Re-inspección")
                fecha_informacion = st.text_input("Fecha Máxima para remitir información", placeholder="Ej: L-V 01/01/2000")
                tipo_empresa = st.selectbox("Tipo de Empresa", ["Privada", "Pública"])
                empleador = st.text_input("Empleador")
                razon_social = st.text_input("Razón Social*", help="Nombre legal de la empresa")
                ruc = st.text_input("RUC*", help="Número de RUC de 13 dígitos")
                telefono = st.text_input("Número de Teléfono")
                correo = st.text_input("Correo Electrónico")
                actividad_economica = st.text_input("Actividad Económica Principal")
                
            with col2:
                tipo_centro = st.selectbox("Tipo de Centro de Trabajo*", ["Matriz", "Sucursal"])
                direccion = st.text_area("Dirección del Centro de Trabajo*")
                total_trabajadores = st.number_input("Total de Trabajadores/Servidores*", min_value=1, value=200)
                num_trabajadores_centro = st.number_input("Número de Trabajadores/Servidores del Centro de Trabajo*", min_value=1, value=10)
                consolidado_planilla = st.selectbox("Consolidado de Planilla IESS*", ["Sí", "No"])
                
                st.subheader("Estadísticas de Trabajadores", divider="green")
                col3, col4 = st.columns(2)
                with col3:
                    hombres = st.number_input("Hombres", min_value=0, value=0)
                    mujeres = st.number_input("Mujeres", min_value=0, value=0)
                    embarazadas = st.number_input("Embarazadas", min_value=0, value=0)
                    mujeres_en_lactancia = st.number_input("Mujeres en Lactancia", min_value=0, value=0)
                    extranjeros = st.number_input("Extranjeros", min_value=0, value=0)
                    adolescentes = st.number_input("Adolescentes", min_value=0, value=0)
                
                with col4:
                    teletrabajadores = st.number_input("Teletrabajadores", min_value=0, value=0)
                    niños = st.number_input("Menores de edad", min_value=0, value=0)
                    adultos_mayores = st.number_input("Adultos Mayores", min_value=0, value=0)
                
                numeros_centros_abiertos = st.text_input("Número de Centros de Trabajo Abiertos")
                horario_trabajo = st.text_input("Horario de Trabajo Principal", placeholder="Ej: L-V 08:00-17:00")
                entrevistados = st.text_area("Personas Entrevistadas (separar por comas)").split(",")
                
            if st.form_submit_button("Registrar Empresa", type="primary"):
                if not all([ruc, razon_social, tipo_centro, direccion]):
                    st.error("Por favor complete los campos obligatorios (*)")
                else:
                    estadisticas = {
                        "hombres": hombres,
                        "mujeres": mujeres,
                        "embarazadas": embarazadas,
                        "teletrabajadores": teletrabajadores,
                        "niños": niños,
                        "adultos_mayores": adultos_mayores,
                        "mujeres_en_lactancia": mujeres_en_lactancia,
                        "extranjeros": extranjeros,
                        "adolescentes": adolescentes
                    }
                    
                    empresa_data = {
                        "inspeccion": inspeccion,
                        "fecha": str(fecha) if fecha else None,
                        "re_inspeccion": re_inspeccion,
                        "fecha_inspeccion": str(fecha_inspeccion) if fecha_inspeccion else None,
                        "fecha_informacion": fecha_informacion,
                        "tipo": tipo_empresa,
                        "empleador": empleador,
                        "razon_social": razon_social,
                        "ruc": ruc,
                        "telefono": telefono,
                        "correo": correo,
                        "actividad_economica": actividad_economica,
                        "tipo_centro": tipo_centro,
                        "direccion": direccion,
                        "total_trabajadores": total_trabajadores,
                        "num_trabajadores_centro": num_trabajadores_centro,
                        "consolidado_planilla": consolidado_planilla == "Sí",
                        "estadisticas": estadisticas,
                        "horario_trabajo": horario_trabajo,
                        "entrevistados": [e.strip() for e in entrevistados if e.strip()],
                        "numeros_centros_abiertos": numeros_centros_abiertos
                    }
                    
                    try:
                        response = requests.post(
                            f"{BACKEND_URL}/empresas/",
                            json=empresa_data,
                            headers={"Authorization": f"Bearer {st.session_state.token}"}
                        )
                        if response.status_code == 200:
                            st.success("✅ Empresa registrada exitosamente!")
                            time.sleep(2)
                            st.session_state.empresa_actual = response.json()
                            st.rerun()
                        else:
                            st.error(f"Error al registrar empresa: {response.text}")
                    except requests.exceptions.RequestException:
                        st.error("Error al conectar con el servidor")

def display_empresa_info(empresa):
    st.markdown(f"""
    <div class='custom-card'>
        <h3>📋 {empresa['razon_social']}</h3>
        <p><small>RUC: {empresa['ruc']} | Registrada el: {empresa['fecha_registro'].split('T')[0]}</small></p>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Tipo:** {empresa['tipo']}")
        st.markdown(f"**Empleador:** {empresa['empleador']}")
        st.markdown(f"**Teléfono:** {empresa['telefono']}")
        st.markdown(f"**Correo:** {empresa['correo']}")
        st.markdown(f"**Actividad Económica:** {empresa['actividad_economica']}")
        st.markdown(f"**Tipo de Centro:** {empresa['tipo_centro']}")
    
    with col2:
        st.markdown(f"**Dirección:** {empresa['direccion']}")
        st.markdown(f"**Total Trabajadores:** {empresa['total_trabajadores']}")
        st.markdown(f"**Planilla IESS:** {'Sí' if empresa['consolidado_planilla'] else 'No'}")
        st.markdown(f"**Horario:** {empresa['horario_trabajo']}")
        st.markdown(f"**Entrevistados:** {', '.join(empresa['entrevistados'])}")
    
    st.markdown("---")
    st.subheader("📊 Estadísticas de Trabajadores")
    
    estadisticas = empresa['estadisticas']
    df_estadisticas = pd.DataFrame.from_dict(estadisticas, orient='index', columns=['Cantidad'])
    st.bar_chart(df_estadisticas)
    
    st.markdown("</div>", unsafe_allow_html=True)

def formulario_verificacion_page():
    if st.button("← Regresar", key="back_formulario", type="secondary", use_container_width=True, 
                help="Volver a la página anterior", on_click=go_back):
        return
    
    st.title("📋 Formulario de Verificación")
    st.markdown("---")
    
    # Paso 1: Seleccionar empresa
    st.subheader("1. Seleccione la empresa a verificar")
    ruc = st.text_input("Ingrese el RUC de la empresa", key="form_ruc_input")
    
    if st.button("Cargar Empresa", key="cargar_empresa_btn"):
        if ruc:
            try:
                response = requests.get(
                    f"{BACKEND_URL}/empresas/{ruc}",
                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                )
                if response.status_code == 200:
                    empresa = response.json()
                    st.session_state.empresa_actual = empresa
                    st.success(f"Empresa cargada: {empresa['razon_social']}")
                else:
                    st.warning("No se encontró una empresa con ese RUC")
            except requests.exceptions.RequestException:
                st.error("Error al conectar con el servidor")
        else:
            st.warning("Por favor ingrese un RUC")
    
    if 'empresa_actual' in st.session_state and st.session_state.empresa_actual:
        empresa = st.session_state.empresa_actual
        display_empresa_info(empresa)
        
        # Paso 2: Cargar estructura del formulario
        st.subheader("2. Complete el formulario de verificación")

        # Definir la estructura del formulario
        PREGUNTAS_SST = {
            "gestion_administrativa": {
                "title": "Gestión Administrativa",
                "questions": [
                    {
                        "id": "ga1",
                        "normativa": "Acuerdo Ministerial 196 (2024) Art. 4 y Art.18. Decisión 584 (2004) Art. 11. Código del Trabajo (2005) Art. 434.",
                        "pregunta": "¿Cuenta con un Plan de Prevención de Riesgos Laborales (hasta 9 trabajadores) aprobado y registrado en el SUT?",
                        "requisitos": "Documento aprobado por la máxima autoridad y registrado en el Sistema Único de Trabajo (SUT)"
                    },
                    {
                        "id": "ga2",
                        "normativa": "Acuerdo Ministerial 196 (2024) Art. 4, 19. Decisión 584 (2004) Art. 11. Decreto Ejecutivo 256 (2024) Art. 19.",
                        "pregunta": "¿Cuenta con un Reglamento de Higiene y seguridad (más de 10 trabajadores) aprobado y registrado en el SUT?",
                        "requisitos": "Debe contener: Política de SST, organización, responsabilidades, procedimientos y registros obligatorios"
                    },
                    {
                        "id": "ga3",
                        "normativa": "Acuerdo Ministerial 196 (2024) Art. 18 y 19. Decreto Ejecutivo 256 (2024) Art. 20.",
                        "pregunta": "¿Se ha socializado a todos los trabajadores la Política de seguridad y salud en el trabajo?",
                        "requisitos": "Evidencia de socialización (actas, registros de asistencia, comunicados)"
                    },
                    {
                    "id": "ga4",
                    "normativa": "Acuerdo Ministerial 196 (2024) Art. 18 y 19. Decreto Ejecutivo 256 (2024) Art. 25.",
                    "pregunta": "¿Cuenta con el registro del Modelo de Seguridad e Higiene del Trabajo en la Plataforma SUT?",
                    "requisitos": "Captura de pantalla del registro vigente en el SUT"
                    },
                    {
                    "id": "ga5",
                    "normativa": "Acuerdo Ministerial 196 (2024) Art. 14",
                    "pregunta": "¿Cuenta con el registro del Texto del Trabajo en la Plataforma SUT?",
                    "requisitos": "Documento que contenga las condiciones de trabajo registrado en el SUT"
                    },
                    {
                    "id": "ga6",
                    "normativa": "Decreto Ejecutivo 256 (2024) Art. 21.",
                    "pregunta": "¿Cuenta con el registro del Servicio Externo de Seguridad e Higiene del Trabajo en la Plataforma SUT?",
                    "requisitos": "Contrato vigente y registro en SUT del servicio externo"
                    },
                    {
                    "id": "ga7",
                    "normativa": "Decreto Ejecutivo 256 (2024) Art. 33.",
                    "pregunta": "¿Cuenta con informe de actividades realizadas por técnico o servicio externo de seguridad e higiene del trabajo?",
                    "requisitos": "Informe con: Objetivo, estadísticas básicas, actividades ejecutadas, horas de gestión, conclusiones, fotos y firmas"
                    },
                    {
                    "id": "ga8",
                    "normativa": "Decreto Ejecutivo 256 (2024) Art. 32.",
                    "pregunta": "¿Cuenta con el registro del profesional médico en la Plataforma SUT?",
                    "requisitos": "Registro vigente del médico ocupacional en el SUT"
                    },
                    {
                    "id": "ga9",
                    "normativa": "Resolución 657 (2008) Art. 10, 13, 14.",
                    "pregunta": "¿Cuenta con el registro del Delegado de Seguridad y Salud en la plataforma SUT?",
                    "requisitos": "Acta de elección y registro en SUT del delegado"
                    },
                    {
                    "id": "ga10",
                    "normativa": "Decreto Ejecutivo 256 (2024) Art. 36. Art. 38.",
                    "pregunta": "¿Cuenta con el registro del Comité de Seguridad y Salud en la plataforma SUT?",
                    "requisitos": "Acta de constitución y registro en SUT del comité"
                }
            ]
         },
            "gestion_tecnica": {
                "title": "Gestión Técnica",
                "questions": [
                    {
                        "id": "gt1",
                        "normativa": "Decisión 584. Art. 11. Art. 19. Código del Trabajo Art. 42. Decreto Ejecutivo 255 (2024) Art. 28.",
                        "pregunta": "¿Se dispone de un descriptivo por puesto de trabajo?",
                        "requisitos": "Debe incluir: N° de trabajadores, actividades, tareas específicas, horas diarias, recursos utilizados (máquinas, equipos, agentes químicos/biológicos)"
                    },  
                    {
                        "id": "gt2",
                        "normativa": "Decisión 584. Art. 11.",
                        "pregunta": "¿Cuenta con un mapa de riesgos del lugar, y/o, centro de trabajo?",
                        "requisitos": "Debe contener: Señalización de SST, EPP, dispositivos de parada de emergencia"
                    },
                    {
                        "id": "gt3",
                        "normativa": "Decisión 584 (2004) Art. 11. Resolución 957 (2008) Art. 1. Decreto Ejecutivo 255 (2024) Art. 27 y 28, 47.",
                        "pregunta": "¿Cuenta con una matriz de identificación de peligros y evaluación de riesgos laborales por puesto de trabajo con metodología reconocida?",
                        "requisitos": "Matriz con metodología validada (INSHT, NTP, ISO, etc.)"
                    },
                    {
                        "id": "gt4",
                        "normativa": "Decisión 584 (2004) Art. 11,12, 18. Resolución 957 (2008) Art. 1. Decreto Ejecutivo 255 (2024) Art. 48 Acuerdo Ministerial 196 (2024)",
                        "pregunta": "¿Cuenta con informe de medición de agentes físico, químico y/o biológico del puesto de trabajo?",
                        "requisitos": "Informe con: Fecha, puesto, trabajadores expuestos, agente, metodología, resultados, comparación con normativa, firmas, certificados de calibración, fotos"
                    },
                    {
                        "id": "gt5",
                        "normativa": "Decisión 584 (2004) Art. 11, 12, 18 Resolución 957 (2008) Art. 1 Decreto Ejecutivo 255 (2024) Art. 44, 45 y 46. Acuerdo Ministerial 196 (2024).",
                        "pregunta": "¿Cuenta con informe de evaluación de riesgos de seguridad, ergonómicos y psicosociales?",
                        "requisitos": "Informe con: Fecha, puesto, trabajadores, riesgo identificado, metodología, resultados, comparación normativa, firmas, fotos"
                    },
                    {
                        "id": "gt6",
                        "normativa": "Decisión 584 (2004) Art. 11 Resolución 957 (2008) Art. 1 Código del Trabajo Art. 412 Decreto Ejecutivo 255 (2024) Art. 49",
                        "pregunta": "¿Cuenta con informe de medidas de prevención y protección implementadas por puesto de trabajo?",
                        "requisitos": "Informe con: Fecha, medidas implementadas (eliminación, sustitución, controles), fechas implementación, resultados, seguimiento, firmas, fotos"
                    },
                    {
                        "id": "gt7",
                        "normativa": "Resolución 957 (2008) Art. 1.",
                        "pregunta": "¿Cuenta con el cálculo del riesgo residual en la matriz de identificación de peligros?",
                        "requisitos": "Matriz actualizada con valoración de riesgo residual post-implementación de controles"
                    },
                    {
                        "id": "gt8",
                        "normativa": "Decisión 584 (2004) Art. 11.",
                        "pregunta": "¿Se ha verificado in situ la implementación de medidas de prevención y protección?",
                        "requisitos": "Checklist o informe de verificación con evidencias fotográficas"
                    },
                    {
                        "id": "gt9",
                        "normativa": "Acuerdo Ministerial 196 (2024) Anexo 3",
                        "pregunta": "¿Se ha realizado la limpieza y mantenimiento periódico de luminarias?",
                        "requisitos": "Registro de mantenimiento con fechas y responsables"
                    },
                    {
                        "id": "gt10",
                        "normativa": "Acuerdo Ministerial 196 (2024) Anexo 3",
                        "pregunta": "¿Se ha realizado mantenimiento periódico de los sistemas de ventilación?",
                        "requisitos": "Registro de mantenimiento y mediciones de calidad de aire"
                    },
                    {
                        "id": "gt11",
                        "normativa": "Acuerdo Ministerial 196 (2024) Anexo 3",
                        "pregunta": "¿Se han clasificado los agentes químicos según su categorización de peligros?",
                        "requisitos": "Inventario de químicos con clasificación GHS"
                    },
                    {
                        "id": "gt12",
                        "normativa": "Acuerdo Ministerial 196 (2024) Anexo 3",
                        "pregunta": "¿Los recipientes con agentes químicos cuentan con tapas adecuadas?",
                        "requisitos": "Verificación visual de recipientes correctamente cerrados"
                    },
                    {
                        "id": "gt13",
                        "normativa": "Acuerdo Ministerial 196 (2024) Anexo 3",
                        "pregunta": "¿Se almacenan agentes químicos en áreas específicas según su compatibilidad?",
                        "requisitos": "Áreas de almacenamiento segregadas según compatibilidad química"
                    },
                    {
                        "id": "gt14",
                        "normativa": "Acuerdo Ministerial 196 (2024) Anexo 3",
                        "pregunta": "¿Se dispone de fichas de datos de seguridad de los agentes químicos accesibles?",
                        "requisitos": "Fichas SDS actualizadas y en lugar accesible para trabajadores"
                    },
                    {
                        "id": "gt15",
                        "normativa": "Acuerdo Ministerial 196 (2024) Anexo 3",
                        "pregunta": "¿Se ha etiquetado adecuadamente los agentes químicos con información en español?",
                        "requisitos": "Etiquetas con pictogramas, frases H y P, en español"
                    },
                    {
                        "id": "gt16",
                        "normativa": "Acuerdo Ministerial 196 (2024) Anexo 3",
                        "pregunta": "¿Se aplican lineamientos de transporte, almacenamiento y manejo de productos químicos?",
                        "requisitos": "Procedimientos documentados y evidencias de cumplimiento"
                    },
                    {
                        "id": "gt17",
                        "normativa": "Acuerdo Ministerial 196 (2024) Anexo 3",
                        "pregunta": "¿Se aplican medidas de bioseguridad para agentes biológicos?",
                        "requisitos": "Protocolos de bioseguridad según nivel de riesgo"
                    },
                    {
                        "id": "gt18",
                        "normativa": "Acuerdo Ministerial 196 (2024) Anexo 3",
                        "pregunta": "¿Se ha dispuesto área específica para desechos biológicos?",
                        "requisitos": "Área con contenedores diferenciados y protocolos de disposición"
                    },
                    {
                        "id": "gt19",
                        "normativa": "Acuerdo Ministerial 196 (2024) Anexo 3",
                        "pregunta": "¿Se ha implementado control de plagas y vectores?",
                        "requisitos": "Contrato o registros de control de plagas"
                    },
                    {
                        "id": "gt20",
                        "normativa": "Acuerdo Ministerial 196 (2024) Anexo 3",
                        "pregunta": "¿Los lugares de trabajo se encuentran ordenados y limpios?",
                        "requisitos": "Verificación visual de condiciones de orden y limpieza"
                    },
                    {
                        "id": "gt21",
                        "normativa": "Acuerdo Ministerial 196 (2024) Anexo 3",
                        "pregunta": "¿Las áreas de circulación cuentan con niveles mínimos de iluminación?",
                        "requisitos": "Mediciones de iluminación según NTE INEN 2 250"
                    },
                    {
                        "id": "gt22",
                        "normativa": "Acuerdo Ministerial 196 (2024) Anexo 3",
                        "pregunta": "¿Se han delimitado áreas para circulación del personal y/o vehículos?",
                        "requisitos": "Marcaje visible de zonas de circulación"
                    },
                    {
                        "id": "gt23",
                        "normativa": "Acuerdo Ministerial 196 (2024) Anexo 3",
                        "pregunta": "¿Se han delimitado áreas para emplazamiento de máquinas?",
                        "requisitos": "Áreas señalizadas para ubicación de equipos"
                    },
                    {
                        "id": "gt24",
                        "normativa": "Acuerdo Ministerial 196 (2024) Anexo 3",
                        "pregunta": "¿Las rampas están diseñadas conforme a la norma?",
                        "requisitos": "Cumplimiento de pendientes y medidas de seguridad"
                    },
                    {
                        "id": "gt25",
                        "normativa": "Acuerdo Ministerial 196 (2024) Anexo 3",
                        "pregunta": "¿La estructura de prevención contra caídas está en buen estado?",
                        "requisitos": "Inspección de barandillas, plataformas, escaleras, etc."
                    },
                    {
                        "id": "gt26",
                        "normativa": "Acuerdo Ministerial 196 (2024) Anexo 3",
                        "pregunta": "¿Los dispositivos de parada de emergencia están señalizados y accesibles?",
                        "requisitos": "Verificación visual de señalización y accesibilidad"
                    },
                    {
                        "id": "gt27",
                        "normativa": "Acuerdo Ministerial 196 (2024) Anexo 3",
                        "pregunta": "¿Las partes móviles de motores y transmisión están protegidas?",
                        "requisitos": "Verificación de resguardos y protecciones"
                    },
                    {
                        "id": "gt28",
                        "normativa": "Acuerdo Ministerial 196 (2024) Anexo 3",
                        "pregunta": "¿Las puertas y salidas están señalizadas y libres de obstáculos?",
                        "requisitos": "Verificación visual de señalización y despeje"
                    },
                    {
                        "id": "gt29",
                        "normativa": "NTE INEN-ISO 3864-1.",
                        "pregunta": "¿Cumple con la normativa de señalización preventiva?",
                        "requisitos": "Señales amarillas con pictogramas según norma"
                    },
                    {
                        "id": "gt30",
                        "normativa": "NTE INEN-ISO 3864-1.",
                        "pregunta": "¿Cumple con la normativa de señalización prohibitiva?",
                        "requisitos": "Señales rojas con pictogramas según norma"
                    },
                    {
                        "id": "gt31",
                        "normativa": "NTE INEN-ISO 3864-1.",
                        "pregunta": "¿Cumple con la normativa de señalización de obligación?",
                        "requisitos": "Señales azules con pictogramas según norma"
                    },
                    {
                        "id": "gt32",
                        "normativa": "NTE INEN-ISO 3864-1.",
                        "pregunta": "¿Cumple con la normativa de señalización de equipos contra incendio?",
                        "requisitos": "Señales rojas para equipos contra incendio"
                    },
                    {
                        "id": "gt33",
                        "normativa": "Decreto Ejecutivo 255 (2024) Art. 58. Decisión 584 (2004) Art. 11.",
                        "pregunta": "¿Existe señalización para evacuación en caso de emergencia?",
                        "requisitos": "Señalización fotoluminiscente según normativa"
                    },
                    {
                        "id": "gt34",
                        "normativa": "Decreto Ejecutivo 255 (2024) Art. 58. Decisión 584 (2004) Art. 11.",
                        "pregunta": "¿Cuenta con procedimiento para trabajos especiales?",
                        "requisitos": "Procedimiento con: objetivo, responsable, definición de puesto, riesgos, controles, EPP, formato de permiso"
                    },
                    {
                        "id": "gt35",
                        "normativa": "Decreto Ejecutivo 255 (2024) Art. 58. Decisión 584 (2004) Art. 11.",
                        "pregunta": "¿Se emiten los permisos de trabajo conforme el procedimiento?",
                        "requisitos": "Registros de permisos emitidos completos"
                    },
                    {
                        "id": "gt36",
                        "normativa": "Decreto Ejecutivo 255 (2024) Art. 58 Acuerdo Ministerial (2017) 174. Acuerdo Ministerial (2017) 13.",
                        "pregunta": "¿Cuenta con registros de apertura y cierre de permisos para trabajos especiales?",
                        "requisitos": "Registros completos con fechas, responsables y cierres"
                    }
                ]
            },
            "gestion_talento_humano": {
                "title": "Gestión del Talento Humano ",
                "questions": [
                    {
                        "id": "gth1",
                        "normativa": "Constitución de la República del Ecuador (2008) Art. 35. Decisión 584 (2004) Art. 11, 18, 25. Ley Orgánica de Discapacidades (2012) Art. 16, 19, 45, 52. Código del Trabajo (2005) Art. 42.",
                        "pregunta": "¿Se ha identificado a trabajadores en grupos de atención prioritaria?",
                        "requisitos": "Adultos mayores, mujeres en lactancia, embarazadas, con discapacidad, enfermedades catastróficas"
                    },
                    {
                        "id": "gth2",
                        "normativa": "Decisión 584 (2004) Art. 11, 27. Decreto Ejecutivo 255 (2024) Art. 15.",
                        "pregunta": "¿Se evidencia implementación de medidas para grupos prioritarios?",
                        "requisitos": "Adaptaciones físicas, horarias o de funciones según necesidades"
                    },
                    {
                        "id": "gth3",
                        "normativa": "Acuerdo Ministerial (2017) 174. Decreto Ejecutivo 255 (2024) Art. 15.",
                        "pregunta": "¿Cuenta con certificación de PRL para construcción?",
                        "requisitos": "Certificado vigente para actividades de alto riesgo"
                    },
                    {
                        "id": "gth4",
                        "normativa": "Acuerdo Ministerial (2017) 13. Decreto Ejecutivo 255 (2024) Art. 15.",
                        "pregunta": "¿Cuenta con certificación de PRL para energía eléctrica?",
                        "requisitos": "Certificado vigente para trabajos eléctricos"
                    },
                    {
                        "id": "gth5",
                        "normativa": "Reglamento a Ley de Transporte Terrestre, Tránsito y Seguridad Vial (2012) Art. 132. Decreto Ejecutivo 255 (2024) Art. 51.",
                        "pregunta": "¿El personal que opera vehículos cuenta con licencia adecuada?",
                        "requisitos": "Licencias vigentes según categoría del vehículo/maquinaria"
                    },
                    {
                        "id": "gth6",
                        "normativa": "Decisión 584 (2004) Art. 11, 23. Resolución 957 (2008) Art 1. Decreto Ejecutivo 255 (2024) Art. 15.",
                        "pregunta": "¿Cuenta con registro de asistencia a inducciones de SST?",
                        "requisitos": "Registro con: fecha, tema, nombres, cédula, firmas, material, evaluación"
                    },
                    {
                        "id": "gth7",
                        "normativa": "Decisión 584 (2004) Art. 19 Resolución 957 (2008) Art 1.",
                        "pregunta": "¿Se han efectuado campañas de comunicación en SST?",
                        "requisitos": "Evidencias de campañas realizadas (fotos, materiales)"
                    },
                    {
                        "id": "gth8",
                        "normativa": "Decisión 584 (2004) Art. 11, 23. Resolución 957 (2008) Art 1. Decreto Ejecutivo. 255 Art. 15, 16, 28. Acuerdo Ministerial 196 Art. 4.",
                        "pregunta": "¿Cuenta con programa de formación en SST?",
                        "requisitos": "Programa con: objetivos, diagnóstico, contenido, cronograma, metodología, duración, responsables"
                    },
                    {
                    "id": "gth9",
                    "normativa": "Decisión 584 (2004) Art. 11 literal h), i), Art. 23. Resolución 957 (2008) Art 1 literal c). Decreto Ejecutivo 255 (2024) Art. 15, 16,28.",
                    "pregunta": "¿Cuenta con registro de asistencia a capacitaciones?",
                    "requisitos": "Registro con: fecha, tema, participantes, firmas, material, evaluación"
                    },
                    {
                    "id": "gth10",
                    "normativa": "Decisión 584 (2004) Art. 11, 23. Resolución 957 (2008) Art 1. Decreto Ejecutivo 255 (2024) Art. 15, 16, 28.",
                    "pregunta": "¿Las capacitaciones están registradas en la plataforma SUT?",
                    "requisitos": "Capturas de pantalla del registro en SUT"
                    }
                ]
            },
            "procedimientos_operativos": {
                 "title": "Procedimientos Operativos Básicos ",
                    "questions": [
                    {
                        "id": "po1",
                        "normativa": "Decisión 584 (2004) Art. 14 y 22. Resolución 957 (2008) Art 5. Reglamento a la LOSEP (2011) Art. 230. Código del Trabajo (2005) Art. 412. Decreto Ejecutivo 255 (2024) Art. 15.",
                        "pregunta": "¿Cuenta con matriz de exámenes médico ocupacionales por puesto?",
                        "requisitos": "Matriz con: puesto, n° trabajadores, riesgo, tipo examen, frecuencia, responsable"
                    },
                    {
                        "id": "po2",
                        "normativa": "Decisión 584 (2004) Art. 14 y 22. Resolución 957 (2008) Art 5. Reglamento a la LOSEP (2011) Art. 230. Código del Trabajo (2005) Art. 412 . Decreto Ejecutivo 255 (2024) Art. 15.",
                        "pregunta": "¿Cuenta con cronograma de exámenes médico ocupacionales?",
                        "requisitos": "Cronograma anual con fechas programadas"
                    },
                    {
                        "id": "po3",
                        "normativa": "Decisión 584 (2004) Art. 14 y 22. Resolución 957 (2008) Art 5. Reglamento a la LOSEP (2011) Art. 230. Código del Trabajo (2005) Art. 412. Decreto Ejecutivo 255 (2024) Art. 15.",
                        "pregunta": "¿Cuenta con informe de resultados de exámenes médicos?",
                        "requisitos": "Informe con: fecha, periodo, puesto, n° exámenes, tipo, resultados generales, acciones, firmas"
                    },
                    {
                        "id": "po4",
                        "normativa": "Decisión 584 (2004) Art. 14 y 22. Resolución 957 (2008) Art 5. Reglamento a la LOSEP (2011) Art. 230. Código del Trabajo (2005) Art. 412. Decreto Ejecutivo (2024) 255 Art. 15.",
                        "pregunta": "¿Cuenta con certificados de aptitud médica laboral?",
                        "requisitos": "Certificados con firma del médico y aceptación del trabajador"
                    },
                    {
                        "id": "po5",
                        "normativa": "Resolución 957 (2008) Art 5. Decreto Ejecutivo 255 (2024) Art. 15.",
                        "pregunta": "¿Cuenta con informe trimestral de indicadores de salud?",
                        "requisitos": "Informe con: enfermedad común, profesional y accidentes de trabajo"
                    },
                    {
                        "id": "po6",
                        "normativa": "Decisión 584 (2004) Art. 11. Resolución 957 (2008) Art. 1, Art. 5. Código del Trabajo (2005) Art. 42. Reglamento a la LOSEP (2011) Art. 230. Resolución del IESS CD 513 (2016), Art. 56.",
                        "pregunta": "¿Cuenta con procedimiento de investigación de accidentes?",
                        "requisitos": "Procedimiento con: objetivos, alcance, responsabilidades, metodología, acciones correctivas"
                    },
                    {
                        "id": "po7",
                        "normativa": "Decisión 584 (2004) Art. 1. Resolución 957 (2008) Art. 15. Resolución del IESS CD 513 (2016) Art. 1, 12, 47.",
                        "pregunta": "¿Cuenta con registro interno de incidentes y accidentes?",
                        "requisitos": "Registro con: fecha, hora, trabajador, puesto, lugar, descripción, consecuencias"
                    },
                    {
                        "id": "po8",
                        "normativa": "Resolución del IESS. CD 513 (2016) Art. 47",
                        "pregunta": "¿Cuenta con informe de investigación de accidentes?",
                        "requisitos": "Informe con: fecha, hora, lugar, trabajador, descripción, testigos, causas, acciones"
                    },
                    {
                        "id": "po9",
                        "normativa": "Resolución del IESS. CD 513 (2016) Art. 44.",
                        "pregunta": "¿Se ha reportado el accidente a la autoridad competente?",
                        "requisitos": "Copia del reporte al IESS o autoridad correspondiente"
                    },
                    {
                        "id": "po10",
                        "normativa": "Resolución del IESS. CD 513 (2016) Art. 63.",
                        "pregunta": "¿Se han aplicado medidas para evitar nuevos accidentes?",
                        "requisitos": "Evidencia de implementación de medidas correctivas"
                    },
                    {
                        "id": "po11",
                        "normativa": "Decisión 584 (2004) Art. 11. Resolución 957 (2008) Art. 5. Código del Trabajo (2005) Art. 42. Reglamento a la LOSEP (2011) Art. 230. Resolución del IESS. CD 513 (2016) Art. 47.",
                        "pregunta": "¿Cuenta con procedimiento de investigación de enfermedades profesionales?",
                        "requisitos": "Procedimiento documentado y aprobado"
                    },
                    {
                        "id": "po12",
                        "normativa": "Resolución del IESS. CD 513 (2016) Art. 45. Código del Trabajo (2005) Art. 42. Acuerdo Ministerial 174 (2008) Art. 11, 136, 137.",
                        "pregunta": "¿Se ha reportado la presunción de enfermedad profesional?",
                        "requisitos": "Copia del reporte al IESS"
                    },
                    {
                        "id": "po13",
                        "normativa": "Resolución del IESS. CD 513 (2016) Art. Código del Trabajo (2005) Art. 42. Resolución 957 (2009) Art.1. Dedición 584 (2004) Art. 4. Decreto Ejecutivo 255 (2024) Art. 28.",
                        "pregunta": "¿Se han aplicado medidas para evitar nuevas enfermedades profesionales?",
                        "requisitos": "Evidencia de implementación de medidas correctivas"
                    },
                    {
                        "id": "po14",
                        "normativa": "Decisión 584 (2004) Art. 16. Resolución 957 (2009) Art. 1. Reglamento de prevención, mitigación y protección contra incendios (2009) Art. 17. Acuerdo Ministerial 174 (2017) Art. 134.",
                        "pregunta": "¿Cuenta con plan de emergencias implementado?",
                        "requisitos": "Plan con: objetivos, alcance, amenazas, procedimientos, mapas, cronogramas, brigadas"
                    },
                    {
                        "id": "po15",
                        "normativa": "Decisión 584 (2004) Art. 11, 23. Resolución 957 (2009) Art.1. Decreto Ejecutivo 255 (2024) Art. 15. Acuerdo Ministerial 196 (2024) Art. 4",
                        "pregunta": "¿Cuenta con informe anual de simulacros realizados?",
                        "requisitos": "Informe con: fecha, objetivo, tipo, categoría, duración, participantes, incidentes, lecciones"
                    },
                    {
                        "id": "po16",
                        "normativa": "Decisión 584 (2004) Art. 11, 23. Resolución 957 (2009) Art. 1, 23. Decreto Ejecutivo 255 (2024) Art. 15. Acuerdo Ministerial 196 Art. 4. Decreto Ejecutivo 255 (2024) Art. 50.",
                        "pregunta": "¿Se evidencia implementación del plan de emergencia?",
                        "requisitos": "Evidencias de implementación (fotos, registros)"
                    },
                    {
                        "id": "po17",
                        "normativa": "Decisión 584 (2004) Art 11 literal c). Decreto Ejecutivo 256 Capítulo II Art. 56",
                        "pregunta": "¿Cuenta con procedimiento de adquisición de EPP y ropa de trabajo?",
                        "requisitos": "Procedimiento con: objetivo, alcance, responsabilidades, identificación de necesidades, especificaciones"
                    },
                    {
                        "id": "po18",
                        "normativa": "Decisión 584 (2004) Art 11 literal d). Decreto Ejecutivo 256 Capítulo II Art. 56",
                        "pregunta": "¿Cuenta con registro de entrega de EPP y ropa de trabajo?",
                        "requisitos": "Registro con: fecha, trabajador, cédula, detalle de EPP, firmas, devoluciones"
                    },
                    {
                        "id": "po19",
                        "normativa": "Decisión 584 (2004) Art 11. Decreto Ejecutivo 255 (2024) Art. 56.",
                        "pregunta": "¿Se evidencia correcta utilización de EPP?",
                        "requisitos": "Verificación in situ del uso adecuado"
                    },
                    {
                        "id": "po20",
                        "normativa": "Acuerdo Ministerial 032 (2017) Art. G. Acuerdo Ministerial 398 VIII-SIDA (2006), Acuerdo Ministerial 244. (2021)",
                        "pregunta": "¿Se ha implementado programa de prevención de riesgo psicosocial?",
                        "requisitos": "Programa con al menos 12 actividades implementadas"
                    },
                    {
                        "id": "po21",
                        "normativa": "Acuerdo Ministerial 032 (2017) Art. 9.",
                        "pregunta": "¿Se ha implementado programa de prevención de consumo de alcohol, tabaco y drogas?",
                        "requisitos": "Programa con actividades documentadas"
                    },
                    {
                        "id": "po22",
                        "normativa": "Acuerdo Interministerial 038 (2019).",
                        "pregunta": "¿Se ha registrado el programa de prevención de consumo en el SUT?",
                        "requisitos": "Captura de pantalla del registro en SUT"
                    }
                ]
            },
           "servicios_permanentes": {
                "title": "Servicios Permanentes ",
                    "questions": [
                    {
                        "id": "sp1",
                        "normativa": "Código de Trabajo (2005) Art. 430",
                        "pregunta": "¿Cuenta con botiquín de emergencia para primeros auxilios?",
                        "requisitos": "Botiquín completo, accesible y con productos vigentes"
                    },
                    {
                        "id": "sp2",
                        "normativa": "Código de Trabajo (2005) Art. 42.",
                        "pregunta": "¿El comedor cuenta con adecuada salubridad y ambientación?",
                        "requisitos": "Limpieza, ventilación, mobiliario en buen estado"
                    },
                    {
                        "id": "sp3",
                        "normativa": "Acuerdo Ministerial 196 (2024), Anexo 3",
                        "pregunta": "¿Aplica para centros con 50+ trabajadores a 2km de población?",
                        "requisitos": "Solo si cumple las condiciones de distancia y número de trabajadores"
                    },
                    {
                        "id": "sp4",
                        "normativa": "Acuerdo Ministerial 196 (2024), Anexo 3",
                        "pregunta": "¿En caso de existir cocina, cuenta con salubridad adecuada?",
                        "requisitos": "Limpieza, almacenamiento adecuado de alimentos"
                    },
                    {
                        "id": "sp5",
                        "normativa": "Acuerdo Ministerial 196 (2024), Anexo 3",
                        "pregunta": "¿Se dispone de abastecimiento de agua para consumo humano?",
                        "requisitos": "Agua potable disponible para los trabajadores"
                    },
                    {
                        "id": "sp6",
                        "normativa": "Acuerdo Ministerial 196 (2024), Anexo 3",
                        "pregunta": "¿Cuenta con servicios higiénicos en buenas condiciones?",
                        "requisitos": "Limpios, funcionando, separados por sexo"
                    },
                    {
                        "id": "sp7",
                        "normativa": "Acuerdo Ministerial 196 (2024), Anexo 3",
                        "pregunta": "¿Cuenta con duchas en buenas condiciones?",
                        "requisitos": "Funcionando, limpias, con agua"
                    },
                    {
                        "id": "sp8",
                        "normativa": "Acuerdo Ministerial 196 (2024), Anexo 3",
                        "pregunta": "¿Cuenta con lavabos en buenas condiciones y con útiles?",
                        "requisitos": "Lavabos funcionando con jabón y toallas"
                    },
                    {
                        "id": "sp9",
                        "normativa": "Acuerdo Ministerial 196 (2024), Anexo 3",
                        "pregunta": "¿Se dispone de vestuarios separados por sexo?",
                        "requisitos": "Vestuarios limpios y en buen estado"
                    },
                    {
                        "id": "sp10",
                        "normativa": "Acuerdo Ministerial 196 (2024), Anexo 3",
                        "pregunta": "¿Cuenta campamentos en buenas condiciones?",
                        "requisitos": "Con luz, ventilación, agua, servicios higiénicos, comedores"
                    }
                ]
            } 
        }

        with st.form("formulario_verificacion"):
             # Iterar por cada sección
            for seccion, datos_seccion in PREGUNTAS_SST.items():
                st.markdown(f"## 🏛️ {seccion}")
                
                with st.expander(f"### 📌 {datos_seccion['title']}", expanded=False):
                    # Mostrar cada pregunta en formato de tabla
                    st.markdown("""
                    <table class="verification-table">
                        <thead>
                            <tr>
                                <th>N°</th>
                                <th>CUMPLIMIENTO LEGAL / MEDIOS DE VERIFICACIÓN</th>
                                <th>VERIFICACIÓN</th>
                            </tr>
                        </thead>
                        <tbody>
                    """, unsafe_allow_html=True)
                    
                    for pregunta in datos_seccion['questions']:
                        st.markdown(f"""
                        <tr>
                            <td>{pregunta['id']}</td>
                            <td>
                                <div class='gestion-text'>{datos_seccion['title']}</div>
                                <div class='pregunta-header'>{pregunta['pregunta']}</div>
                                <div class='normativa-text'>Normativa: {pregunta['normativa']}</div>
                            </td>
                            <td>
                        """, unsafe_allow_html=True)

                        # Opción única de selección (corregida)
                        opcion = st.radio(
                            "Seleccione:",
                            ["✅ Cumple", "❌ No cumple", "➖ No aplica"],
                            key=f"opcion_{pregunta['id']}",
                            horizontal=True,
                            index=None
                        )
                        
                        obs = st.text_input(
                            "Observaciones",
                            key=f"obs_{pregunta['id']}",
                            placeholder="Opcional"
                        )
                        
                        st.markdown("""
                            </td>
                        </tr>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("""
                        </tbody>
                    </table>
                    """, unsafe_allow_html=True)

            # Botón de envío
            submitted = st.form_submit_button("💾 Guardar Formulario Completo", type="primary")
            
            if submitted:
                # Procesar respuestas
                preguntas_respuestas = []
                for seccion, datos_seccion in PREGUNTAS_SST.items():
                    for pregunta in datos_seccion['questions']:
                        respuesta = st.session_state.get(f"opcion_{pregunta['id']}", "No seleccionado")
                        
                        preguntas_respuestas.append({
                            "id": int(''.join(filter(str.isdigit, pregunta["id"]))),
                            "seccion": seccion,
                            "categoria": datos_seccion['title'],
                            "pregunta": pregunta["pregunta"],
                            "normativa": pregunta["normativa"],
                            "respuesta": respuesta,
                            "observaciones": st.session_state.get(f"obs_{pregunta['id']}", "")
                        })
                
                # Crear objeto formulario
                formulario = {
                    "empresa_ruc": empresa["ruc"],
                    "inspector_cedula": st.session_state.user_info["cedula"],
                    "preguntas": preguntas_respuestas
                }

                try:
                    response = requests.post(
                        f"{BACKEND_URL}/formularios/",
                        json=formulario,
                        headers={"Authorization": f"Bearer {st.session_state.token}"}
                    )
                    if response.status_code == 200:
                        st.success("✅ Formulario guardado exitosamente!")
                        time.sleep(2)
                        st.session_state.current_page = "reportes"
                        st.rerun()
                    else:
                        st.error(f"Error al guardar formulario: {response.text}")
                except requests.exceptions.RequestException:
                    st.error("Error al conectar con el servidor")

def generate_pdf_report(empresa, estadisticas, preguntas, observaciones_generales):
    """Genera un PDF del reporte con encabezado y firma"""
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Configurar fuente compatible (solución sin necesidad de fuente externa)
    pdf.set_font("Arial", size=12)
    
    # Función para limpiar texto de caracteres especiales
    def clean_text(text):
        if text is None:
            return ""
        if not isinstance(text, str):
            text = str(text)
        # Reemplazo de caracteres especiales
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
            'ñ': 'n', 'Ñ': 'N', 'ü': 'u', 'Ü': 'U',
            '´': '', '`': '', '¨': '', '¿': '', '¡': ''
        }
        for orig, repl in replacements.items():
            text = text.replace(orig, repl)
        return text
    
    # Encabezado con logo
    try:
        pdf.image("https://via.placeholder.com/150x50?text=SESACO+Logo", x=10, y=8, w=40)
    except:
        pass
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, clean_text("REPORTE DE VERIFICACION DE SEGURIDAD INDUSTRIAL"), ln=1, align='C')
    pdf.set_font("Arial", size=12)
    
    # Información de la empresa
    pdf.cell(0, 10, clean_text(f"Empresa: {empresa['razon_social']}"), ln=1)
    pdf.cell(0, 10, clean_text(f"RUC: {empresa['ruc']}"), ln=1)
    pdf.cell(0, 10, clean_text(f"Fecha de generacion: {datetime.now().strftime('%d/%m/%Y %H:%M')}"), ln=1)
    pdf.ln(10)
    
    # Información general
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, clean_text("Resumen Ejecutivo"), ln=1)
    pdf.set_font("Arial", size=12)
    
    cumplimiento = estadisticas['cumplimiento_promedio']
    pdf.multi_cell(0, 8, clean_text(f"Cumplimiento general: {cumplimiento}%"))
    
    if cumplimiento >= 80:
        evaluacion = "EXCELENTE"
    elif cumplimiento >= 50:
        evaluacion = "MODERADO"
    else:
        evaluacion = "BAJO"
    
    pdf.cell(0, 8, clean_text(f"Evaluacion: {evaluacion}"), ln=1)
    
    # Observaciones generales
    if observaciones_generales:
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, clean_text("Observaciones Generales:"), ln=1)
        pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 8, clean_text(observaciones_generales))
    
    # Detalle por sección
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, clean_text("Detalle por Area"), ln=1)
    pdf.set_font("Arial", size=10)
    
    for seccion, datos in estadisticas["secciones"].items():
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, clean_text(f"Area: {seccion}"), ln=1)
        pdf.set_font("Arial", size=10)
        
        total_aplicable = datos["total"] - datos["no_aplica"]
        porcentaje = (datos["cumple"] / total_aplicable) * 100 if total_aplicable > 0 else 0
        
        pdf.cell(90, 8, clean_text(f"Porcentaje de cumplimiento: {porcentaje:.1f}%"))
        pdf.cell(90, 8, clean_text(f"No conformidades: {datos['no_cumple']}"), ln=1)
        
        # Preguntas problemáticas
        preguntas_no_cumplen = [p for p in preguntas if p["seccion"] == seccion and p["respuesta"] == "❌ No cumple"]
        
        if preguntas_no_cumplen:
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 8, clean_text("No conformidades identificadas:"), ln=1)
            pdf.set_font("Arial", size=9)
            
            for p in preguntas_no_cumplen:
                pdf.multi_cell(0, 6, clean_text(f"- {p['pregunta']}"))
                pdf.multi_cell(0, 6, clean_text(f"  Normativa: {p['normativa']}"))
                if p['observaciones']:
                    pdf.multi_cell(0, 6, clean_text(f"  Observaciones: {p['observaciones']}"))
                pdf.ln(2)
    
    # Firma y sello
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, clean_text("Firma y Sello del Inspector"), ln=1)
    pdf.ln(20)
    
    # Línea para firma
    pdf.cell(80, 10, clean_text(f"Nombre: {st.session_state.user_info['nombre']}"), ln=1)
    pdf.cell(80, 10, clean_text("Cedula: _________________________"), ln=1)
    pdf.cell(80, 10, clean_text("Firma:  _________________________"), ln=1)
    pdf.ln(20)
    
    # Pie de página
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 10, clean_text("Documento generado automaticamente por el sistema SESACO - Seguridad Industrial S.A."), 0, 0, 'C')
    
    return pdf.output(dest='S').encode('latin1')

def reportes_page():
    if st.button("← Regresar", key="back_reportes", type="secondary", use_container_width=True, 
                help="Volver a la página anterior", on_click=go_back):
        return
    
    st.title("📊 Reportes y Estadísticas")
    st.markdown("---")
    
    if 'empresa_actual' in st.session_state and st.session_state.empresa_actual:
        empresa = st.session_state.empresa_actual
        
        try:
            # Obtener reporte de la empresa
            response = requests.get(
                f"{BACKEND_URL}/reportes/{empresa['ruc']}",
                headers={"Authorization": f"Bearer {st.session_state.token}"}
            )
            
            if response.status_code == 200:
                reporte = response.json()
                estadisticas = reporte["estadisticas"]
                ultimo_formulario = reporte["ultimo_formulario"]
                
                st.subheader(f"Reporte para: {empresa['razon_social']}")
                
                # Manejo seguro de la fecha
                fecha_verificacion = ultimo_formulario.get('fecha_verificacion', 'Fecha no disponible')
                st.caption(f"Última verificación: {fecha_verificacion}")
                
                # Sección para observaciones generales
                observaciones_generales = st.text_area("Observaciones Generales:", 
                                                      placeholder="Ingrese observaciones generales para el informe...")
                
                # Métricas principales
                with st.container():
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📋 Total Verificaciones", 
                                estadisticas["total_verificaciones"],
                                help="Número total de verificaciones realizadas")
                    with col2:
                        st.metric("✅ Cumplimiento Promedio", 
                                f"{estadisticas['cumplimiento_promedio']}%",
                                help="Porcentaje promedio de cumplimiento")
                    with col3:
                        st.metric("📝 Preguntas Evaluadas", 
                                sum(sec['total'] for sec in estadisticas['secciones'].values()),
                                help="Total de preguntas evaluadas en todas las secciones")
                # Gráfico general de cumplimiento
                st.markdown("### 📈 Distribución General de Cumplimiento")
                try:
                    # Calcular totales
                    total_cumple = sum(s['cumple'] for s in estadisticas['secciones'].values())
                    total_no_cumple = sum(s['no_cumple'] for s in estadisticas['secciones'].values())
                    total_no_aplica = sum(s['no_aplica'] for s in estadisticas['secciones'].values())
                    
                    # Crear gráfico de pastel
                    fig_pie, ax_pie = plt.subplots(figsize=(8, 6))
                    sizes = [total_cumple, total_no_cumple, total_no_aplica]
                    labels = ['Cumple', 'No Cumple', 'No Aplica']
                    colors = ['#4CAF50', '#F44336', '#FFC107']
                    
                    wedges, texts, autotexts = ax_pie.pie(
                        sizes, 
                        labels=labels, 
                        colors=colors, 
                        autopct='%1.1f%%',
                        startangle=90,
                        explode=(0.05, 0, 0),
                        shadow=True,
                        textprops={'fontsize': 12}
                    )
                    
                    plt.setp(autotexts, size=12, weight="bold")
                    ax_pie.axis('equal')
                    ax_pie.set_title('Distribución de Cumplimiento', pad=20, fontweight='bold')
                    
                    st.pyplot(fig_pie)
                    
                    # Leyenda mejorada
                    st.markdown("""
                    <div style="
                        background-color: #f8f9fa;
                        padding: 12px;
                        border-radius: 8px;
                        margin: 15px 0;
                        border-left: 4px solid #2E7D32;
                    ">
                        <strong style="color: #2E7D32">📌 Leyenda:</strong><br>
                        <span style="color: #4CAF50">● Cumple:</span> Preguntas que cumplen con todos los requisitos<br>
                        <span style="color: #F44336">● No Cumple:</span> Preguntas con no conformidades detectadas<br>
                        <span style="color: #FFC107">● No Aplica:</span> Preguntas no relevantes para este centro de trabajo
                    </div>
                    """, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"⚠️ No se pudo generar el gráfico: {str(e)}")

                # Gráfico de barras por sección
                st.markdown("### 📊 Cumplimiento por Área")
                df_secciones = pd.DataFrame([
                    {
                        "Sección": seccion,
                        "Cumplimiento (%)": (datos["cumple"] / (datos["total"] - datos["no_aplica"])) * 100 
                                          if (datos["total"] - datos["no_aplica"]) > 0 else 0,
                        "Cumple": datos["cumple"],
                        "No Cumple": datos["no_cumple"],
                        "No Aplica": datos["no_aplica"],
                        "Total": datos["total"]
                    }
                    for seccion, datos in estadisticas["secciones"].items()
                ])
                
                # Ordenar por cumplimiento
                df_secciones = df_secciones.sort_values("Cumplimiento (%)", ascending=False)
                
                # Gráfico de barras
                fig_bar, ax_bar = plt.subplots(figsize=(10, 6))
                bars = ax_bar.barh(
                    df_secciones["Sección"], 
                    df_secciones["Cumplimiento (%)"],
                    color=['#4CAF50' if x > 70 else '#FFC107' if x > 40 else '#F44336' for x in df_secciones["Cumplimiento (%)"]]
                )
                
                # Añadir etiquetas a las barras
                ax_bar.bar_label(bars, fmt='%.1f%%', padding=3, fontsize=10)
                ax_bar.set_xlim(0, 100)
                ax_bar.set_xlabel('Porcentaje de Cumplimiento')
                ax_bar.set_title('Cumplimiento por Área de Verificación', pad=20, fontweight='bold')
                ax_bar.grid(axis='x', linestyle='--', alpha=0.7)
                
                st.pyplot(fig_bar)

                # Detalle por sección con gráficos individuales
                st.markdown("### 📑 Detalle por Sección")
                
                for seccion, datos in estadisticas["secciones"].items():
                    with st.expander(f"🔍 {seccion} - {datos['cumple']}/{datos['total'] - datos['no_aplica']} cumplen", expanded=False):
                        # Calcula porcentaje de cumplimiento (excluyendo no aplica)
                        total_aplicable = datos["total"] - datos["no_aplica"]
                        porcentaje = (datos["cumple"] / total_aplicable) * 100 if total_aplicable > 0 else 0
                        
                        # Columnas para métricas y gráfico
                        col_metrics, col_chart = st.columns([1, 2])
                        
                        with col_metrics:
                            st.metric("📈 Porcentaje de Cumplimiento", f"{porcentaje:.1f}%")
                            st.metric("✅ Cumple", datos["cumple"])
                            st.metric("❌ No Cumple", datos["no_cumple"])
                            st.metric("➖ No Aplica", datos["no_aplica"])
                        
                        with col_chart:
                            # Gráfico de pastel por sección
                            fig_sec, ax_sec = plt.subplots(figsize=(6, 6))
                            sizes_sec = [datos["cumple"], datos["no_cumple"], datos["no_aplica"]]
                            labels_sec = ['Cumple', 'No Cumple', 'No Aplica']
                            colors_sec = ['#4CAF50', '#F44336', '#FFC107']
                            
                            wedges_sec = ax_sec.pie(
                                sizes_sec, 
                                labels=labels_sec, 
                                colors=colors_sec, 
                                autopct='%1.1f%%',
                                startangle=90,
                                textprops={'fontsize': 10}
                            )
                            
                            ax_sec.set_title(f'Distribución en {seccion}', fontsize=12)
                            st.pyplot(fig_sec)
                        
                        # Mostrar preguntas problemáticas con más detalle
                        preguntas_no_cumplen = [
                            p for p in ultimo_formulario["preguntas"] 
                            if p["seccion"] == seccion and p["respuesta"] == "❌ No cumple"
                        ]
                        
                        if preguntas_no_cumplen:
                            st.warning(f"🚨 {len(preguntas_no_cumplen)} no conformidades encontradas en esta sección:")
                            
                            for idx, p in enumerate(preguntas_no_cumplen, 1):
                                with st.container():
                                    st.markdown(f"""
                                    <div style='
                                        background-color: #fff3e0;
                                        border-radius: 8px;
                                        padding: 1rem;
                                        margin-bottom: 1rem;
                                        border-left: 4px solid #FB8C00;
                                    '>
                                        <div style='font-weight: 600; color: #E65100;'>
                                            No conformidad {idx}: {p['pregunta']}
                                        </div>
                                        <div style='font-size: 0.85rem; color: #666; font-style: italic; margin-top: 0.5rem;'>
                                            <strong>Normativa:</strong> {p['normativa']}
                                        </div>
                                        <div style='margin-top: 0.5rem; font-size: 0.9rem;'>
                                            <strong>Categoría:</strong> {p['categoria']}
                                        </div>
                                        {f"<div style='margin-top: 0.5rem; font-size: 0.9rem;'>📝 <strong>Observaciones:</strong> {p['observaciones']}</div>" if p['observaciones'] else ""}
                                    </div>
                                    """, unsafe_allow_html=True)
                        else:
                            st.success("🎉 Todas las preguntas aplicables en esta sección cumplen con la normativa")

                # Sección de exportación a PDF
                st.markdown("---")
                st.subheader("📤 Exportar Reporte Completo")

                # Opciones de exportación
                export_col1, export_col2 = st.columns(2)

                with export_col1:
                    # Generar PDF
                    if st.button("🖨️ Generar Reporte PDF", type="primary", use_container_width=True):
                        with st.spinner("Generando reporte PDF..."):
                            # Asegurar que las observaciones no sean None
                            obs_generales = observaciones_generales or "Sin observaciones"
                            
                            # Generar el PDF
                            pdf_bytes = generate_pdf_report(
                                empresa,
                                estadisticas,
                                ultimo_formulario["preguntas"],
                                obs_generales
                            )
                            # Crear enlace de descarga
                            b64 = base64.b64encode(pdf_bytes).decode()
                            href = f'<a href="data:application/octet-stream;base64,{b64}" download="reporte_{empresa["ruc"]}_{datetime.now().strftime("%Y%m%d")}.pdf">Descargar Reporte PDF</a>'
                
                            st.markdown(href, unsafe_allow_html=True)
                            st.success("✅ Reporte PDF generado exitosamente")
                            st.balloons() 
                        
                            
                            
                            # Crear enlace de descarga
                            #b64 = base64.b64encode(pdf_bytes).decode()
                            #href = f'<a href="data:application/octet-stream;base64,{b64}" download="reporte_{empresa["ruc"]}_{datetime.now().strftime("%Y%m%d")}.pdf">Descargar Reporte PDF</a>'
                            
                            #st.markdown(href, unsafe_allow_html=True)
                            #st.success("✅ Reporte PDF generado exitosamente")
                            #st.balloons()

                with export_col2:
                    # Exportar datos a Excel
                    if st.button("📊 Exportar a Excel", use_container_width=True):
                        with st.spinner("Preparando datos para Excel..."):
                            # Crear DataFrame con los datos del reporte
                            report_data = []
                            
                            for pregunta in ultimo_formulario["preguntas"]:
                                report_data.append({
                                    "Sección": pregunta["seccion"],
                                    "Categoría": pregunta["categoria"],
                                    "Pregunta": pregunta["pregunta"],
                                    "Normativa": pregunta["normativa"],
                                    "Resultado": pregunta["respuesta"],
                                    "Observaciones": pregunta["observaciones"]
                                })
                            
                            df_report = pd.DataFrame(report_data)
                            
                            # Crear archivo Excel en memoria
                            output = BytesIO()
                            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                                df_report.to_excel(writer, sheet_name='Reporte', index=False)
                            
                            excel_data = output.getvalue()
                            b64 = base64.b64encode(excel_data).decode()
                            href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="reporte_{empresa["ruc"]}_{datetime.now().strftime("%Y%m%d")}.xlsx">Descargar Reporte Excel</a>'
                            
                            st.markdown(href, unsafe_allow_html=True)
                            st.success("✅ Datos preparados para exportar a Excel")
                
                # Resumen ejecutivo
                st.markdown("---")
                st.subheader("📋 Resumen Ejecutivo")
                
                # Calcular resumen de cumplimiento
                cumplimiento_total = estadisticas['cumplimiento_promedio']
                total_no_conformidades = sum(sec['no_cumple'] for sec in estadisticas['secciones'].values())
                
                if cumplimiento_total >= 80:
                    st.success(f"🌟 Excelente cumplimiento general: {cumplimiento_total}%")
                    st.markdown("""
                    La empresa muestra un alto nivel de cumplimiento con las normativas de seguridad y salud en el trabajo. 
                    Se recomienda mantener las buenas prácticas y realizar revisiones periódicas para asegurar la continuidad.
                    """)
                elif cumplimiento_total >= 50:
                    st.warning(f"⚠️ Cumplimiento moderado: {cumplimiento_total}%")
                    st.markdown(f"""
                    La empresa tiene un nivel de cumplimiento aceptable pero con {total_no_conformidades} no conformidades identificadas. 
                    Se recomienda:
                    - Priorizar la corrección de las no conformidades críticas
                    - Implementar un plan de mejora continua
                    - Capacitar al personal en las áreas con menor cumplimiento
                    """)
                else:
                    st.error(f"🚨 Bajo cumplimiento: {cumplimiento_total}%")
                    st.markdown(f"""
                    Se han identificado {total_no_conformidades} no conformidades que requieren atención inmediata. 
                    Acciones recomendadas:
                    - Elaborar un plan de acción correctivo urgente
                    - Asignar recursos para abordar las deficiencias
                    - Solicitar asesoría especializada si es necesario
                    - Programar una re-inspección en el corto plazo
                    """)
                
            else:
                st.warning("⚠️ No hay suficientes datos para generar un reporte completo")
                st.info("Complete al menos una verificación para generar reportes detallados")
                
        except requests.exceptions.RequestException as e:
            st.error(f"🔴 Error de conexión: {str(e)}")
            st.warning("Verifique su conexión a internet o intente nuevamente más tarde")
            
    else:
        st.warning("👈 Seleccione una empresa primero en la página de Formulario de Verificación")
        st.button("Ir a Formulario de Verificación", on_click=lambda: st.session_state.update({"current_page": "formulario_verificacion"}))

# Menu principal
if not st.session_state.logged_in:
    login_page()
else:
    if st.session_state.current_page == "dashboard":
        dashboard_page()
    elif st.session_state.current_page == "gestion_empresas":
        gestion_empresas_page()
    elif st.session_state.current_page == "formulario_verificacion":
        formulario_verificacion_page()
    elif st.session_state.current_page == "reportes":
        reportes_page()

