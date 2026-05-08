"""
DASHBOARD DE MANTENIMIENTO PREDICTIVO
Torno Horizontal - Sistema de Consenso XGBoost + Random Forest
Diseño: Fondo oscuro industrial, tarjetas semafóricas, múltiples gráficos
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import time
import os
import ssl
import queue
from datetime import datetime
from typing import Any, Optional, Dict, Tuple
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import joblib

# ── CAMBIO 1: Imports de Firebase ──────────────────────────────────────────────
import firebase_admin
from firebase_admin import credentials, firestore
# ───────────────────────────────────────────────────────────────────────────────

import warnings
warnings.filterwarnings('ignore')

try:
    import paho.mqtt.client as mqtt
    from paho.mqtt.client import Client as MQTTClient
except ImportError:
    st.error("Instala paho-mqtt: pip install paho-mqtt")
    st.stop()

# ============================================
# CONFIGURACION DE PAGINA
# ============================================
st.set_page_config(
    page_title="Mantenimiento Predictivo - Torno",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CSS PROFESIONAL - TEMA OSCURO INDUSTRIAL
# ============================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=Share+Tech+Mono&family=Exo+2:wght@300;400;600;700&display=swap');

    .stApp {
        background: linear-gradient(135deg, #0a0e1a 0%, #0d1b2a 40%, #0a1628 70%, #060d18 100%);
        font-family: 'Exo 2', sans-serif;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #060d18 0%, #0a1525 100%) !important;
        border-right: 1px solid #1e3a5f !important;
    }
    [data-testid="stSidebar"] * { color: #a8c8e8 !important; }

    .main-header {
        font-family: 'Rajdhani', sans-serif;
        font-size: 36px; font-weight: 700; color: #00d4ff;
        text-align: center; padding: 15px 0 5px 0;
        letter-spacing: 4px; text-transform: uppercase;
        text-shadow: 0 0 30px rgba(0,212,255,0.5), 0 0 60px rgba(0,212,255,0.2);
    }
    .sub-header {
        font-family: 'Share Tech Mono', monospace;
        font-size: 13px; color: #4a90d9;
        text-align: center; margin-bottom: 20px; letter-spacing: 2px;
    }
    .neon-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #00d4ff, #0066ff, #00d4ff, transparent);
        margin: 10px 0 20px 0;
        box-shadow: 0 0 8px rgba(0,212,255,0.6);
    }
    .card-base { border-radius:12px; padding:20px; margin:5px 0; border:1px solid; position:relative; overflow:hidden; }

    .card-normal  { background:linear-gradient(135deg,#0a2a1a 0%,#0d3520 100%); border-color:#00c853; box-shadow:0 0 20px rgba(0,200,83,0.25),inset 0 0 30px rgba(0,200,83,0.05); }
    .card-normal  .estado-titulo { color:#00e676; font-family:'Rajdhani',sans-serif; font-size:22px; font-weight:700; letter-spacing:2px; text-shadow:0 0 15px rgba(0,230,118,0.7); }
    .card-normal  .estado-icon   { font-size:40px; }
    .card-normal  .accion-text   { color:#69f0ae; font-size:13px; }

    .card-aviso   { background:linear-gradient(135deg,#2a1a00 0%,#3d2800 100%); border-color:#ffab00; box-shadow:0 0 20px rgba(255,171,0,0.25),inset 0 0 30px rgba(255,171,0,0.05); animation:pulse-yellow 2s infinite; }
    .card-aviso   .estado-titulo { color:#ffd740; font-family:'Rajdhani',sans-serif; font-size:22px; font-weight:700; letter-spacing:2px; text-shadow:0 0 15px rgba(255,215,64,0.7); }
    .card-aviso   .estado-icon   { font-size:40px; }
    .card-aviso   .accion-text   { color:#ffe57f; font-size:13px; }

    .card-alerta  { background:linear-gradient(135deg,#2a0000 0%,#3d0000 100%); border-color:#ff1744; box-shadow:0 0 20px rgba(255,23,68,0.35),inset 0 0 30px rgba(255,23,68,0.08); animation:pulse-red 1s infinite; }
    .card-alerta  .estado-titulo { color:#ff5252; font-family:'Rajdhani',sans-serif; font-size:22px; font-weight:700; letter-spacing:2px; text-shadow:0 0 15px rgba(255,82,82,0.9); }
    .card-alerta  .estado-icon   { font-size:40px; }
    .card-alerta  .accion-text   { color:#ff8a80; font-size:13px; }

    @keyframes pulse-red    { 0%,100%{box-shadow:0 0 20px rgba(255,23,68,0.35);} 50%{box-shadow:0 0 40px rgba(255,23,68,0.7),0 0 60px rgba(255,23,68,0.3);} }
    @keyframes pulse-yellow { 0%,100%{box-shadow:0 0 20px rgba(255,171,0,0.25);} 50%{box-shadow:0 0 35px rgba(255,171,0,0.5),0 0 50px rgba(255,171,0,0.2);} }

    .counter-card-normal { background:linear-gradient(135deg,#0a2a1a 0%,#0d3520 100%); border:1px solid #00c853; border-radius:12px; padding:20px; text-align:center; box-shadow:0 0 15px rgba(0,200,83,0.2); }
    .counter-card-aviso  { background:linear-gradient(135deg,#2a1a00 0%,#3d2800 100%); border:1px solid #ffab00; border-radius:12px; padding:20px; text-align:center; box-shadow:0 0 15px rgba(255,171,0,0.2); }
    .counter-card-alerta { background:linear-gradient(135deg,#2a0000 0%,#3d0000 100%); border:1px solid #ff1744; border-radius:12px; padding:20px; text-align:center; box-shadow:0 0 15px rgba(255,23,68,0.2); }

    .counter-number-normal { font-family:'Rajdhani',sans-serif; font-size:52px; font-weight:700; color:#00e676; text-shadow:0 0 20px rgba(0,230,118,0.6); line-height:1; }
    .counter-number-aviso  { font-family:'Rajdhani',sans-serif; font-size:52px; font-weight:700; color:#ffd740; text-shadow:0 0 20px rgba(255,215,64,0.6); line-height:1; }
    .counter-number-alerta { font-family:'Rajdhani',sans-serif; font-size:52px; font-weight:700; color:#ff5252; text-shadow:0 0 20px rgba(255,82,82,0.6); line-height:1; }

    .counter-label        { font-family:'Exo 2',sans-serif; font-size:11px; letter-spacing:2px; text-transform:uppercase; margin-top:8px; font-weight:600; }
    .counter-label-normal { color:#69f0ae; }
    .counter-label-aviso  { color:#ffe57f; }
    .counter-label-alerta { color:#ff8a80; }
    .counter-icon         { font-size:28px; margin-bottom:8px; display:block; }

    .section-title { font-family:'Rajdhani',sans-serif; font-size:16px; font-weight:700; color:#4a90d9; letter-spacing:3px; text-transform:uppercase; margin-bottom:12px; display:flex; align-items:center; gap:8px; }
    .section-title::before { content:''; display:inline-block; width:4px; height:16px; background:#00d4ff; border-radius:2px; box-shadow:0 0 8px rgba(0,212,255,0.6); }

    .pred-model-name { font-family:'Rajdhani',sans-serif; font-size:14px; letter-spacing:2px; color:#4a90d9; text-transform:uppercase; margin-bottom:5px; }
    .pred-value-safe   { color:#00e676; text-shadow:0 0 15px rgba(0,230,118,0.5); }
    .pred-value-danger { color:#ff5252; text-shadow:0 0 15px rgba(255,82,82,0.5); }

    .firebase-badge {
        display:inline-flex; align-items:center; gap:6px;
        background:rgba(255,193,7,0.1); border:1px solid rgba(255,193,7,0.3);
        border-radius:6px; padding:4px 10px;
        font-family:'Share Tech Mono',monospace; font-size:11px; color:#ffc107;
        letter-spacing:1px;
    }
    .firebase-badge-ok {
        background:rgba(0,200,83,0.1); border-color:rgba(0,200,83,0.3); color:#00e676;
    }

    .footer { font-family:'Share Tech Mono',monospace; text-align:center; color:#2a5080; font-size:11px; padding:15px; letter-spacing:1px; border-top:1px solid #1e3a5f; margin-top:20px; }

    .stMetric label { color:#4a90d9 !important; font-family:'Exo 2',sans-serif !important; }
    .stMetric [data-testid="metric-container"] { background:rgba(10,21,37,0.6); border:1px solid #1e3a5f; border-radius:8px; padding:10px; }
    h1,h2,h3 { color:#a8c8e8 !important; font-family:'Rajdhani',sans-serif !important; }
    .stButton > button { font-family:'Rajdhani',sans-serif !important; font-weight:600 !important; letter-spacing:2px !important; text-transform:uppercase !important; border-radius:6px !important; }
    [data-testid="stMarkdownContainer"] p { color:#a8c8e8; }
</style>
""", unsafe_allow_html=True)

# ============================================
# TIPOS
# ============================================
ResultadoDict = Dict[str, Any]
ConfigDict    = Dict[str, Any]

# ============================================
# CARGA DE MODELOS
# ============================================
@st.cache_resource
def cargar_modelos() -> Tuple[Any, Any, Any, float, float, bool, Optional[str]]:
    try:
        modelo_xgb = joblib.load('modelos/xgboost_model_opt.pkl')
        modelo_rf  = joblib.load('modelos/random_forest_advanced.pkl')
        scaler     = joblib.load('modelos/scaler.pkl')
        with open('modelos/best_threshold.txt', 'r') as f:
            umbral_xgb = float(f.read().strip())
        with open('modelos/best_threshold_rf_advanced.txt', 'r') as f:
            umbral_rf = float(f.read().strip())
        return modelo_xgb, modelo_rf, scaler, umbral_xgb, umbral_rf, True, None
    except Exception as e:
        return None, None, None, 0.5, 0.5, False, str(e)

def obtener_config_mqtt() -> ConfigDict:
    return {
        "broker":   st.secrets["broker"]["url"],
        "port":     int(st.secrets["broker"]["port"]),
        "username": st.secrets["credenciales"]["username"],
        "password": st.secrets["credenciales"]["password"],
        "topicos":  {
            "sensores":   st.secrets["topicos"]["sensores"],
            "prediccion": st.secrets["topicos"]["prediccion"],
            "estado":     st.secrets["topicos"]["estado"],
            "alerta":     st.secrets["topicos"]["alerta"],
            "aviso":      st.secrets["topicos"]["aviso"]
        }
    }

modelo_xgb, modelo_rf, scaler, umbral_xgb, umbral_rf, modelos_ok, error_msg = cargar_modelos()

# ============================================
# CAMBIO 2: INICIALIZAR FIREBASE
# ============================================
firebase_disponible = False
db = None
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate('firebase-key.json')
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    firebase_disponible = True
    print("[FIREBASE] Conectado correctamente")
except Exception as e:
    print(f"[FIREBASE] No disponible: {e}")

# ============================================
# VARIABLES DE SESIÓN
# ============================================
defaults = {
    'historial': [], 'contador_normal': 0, 'contador_aviso': 0, 'contador_alerta': 0,
    'probabilidades_xgb': [], 'probabilidades_rf': [], 'mqtt_client': None,
    'mqtt_conectado': False, 'config': None, 'simulacion_activa': False,
    'ultimo_resultado': None, 'lecturas_procesadas': 0, 'modo': "Simulacion",
    'temperaturas': [], 'rpms': [], 'torques': [], 'desgastes': [],
    'timestamps_hist': [],
    'firebase_guardados': 0,   # contador de docs guardados en Firebase
    'mqtt_queue': queue.Queue(),
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================
# FUNCIÓN DE PREDICCIÓN CON CONSENSO
# ============================================
def predecir_consenso(datos: dict) -> ResultadoDict:
    columnas = [
        'Type_encoded', 'Air temperature [K]', 'Process temperature [K]',
        'Rotational speed [rpm]', 'Torque [Nm]', 'Tool wear [min]'
    ]
    df = pd.DataFrame([datos])
    X  = df[columnas]
    X_scaled = scaler.transform(X)                         # type: ignore

    proba_xgb = modelo_xgb.predict_proba(X_scaled)[0, 1]  # type: ignore
    pred_xgb  = 1 if proba_xgb >= umbral_xgb else 0
    proba_rf  = modelo_rf.predict_proba(X_scaled)[0, 1]   # type: ignore
    pred_rf   = 1 if proba_rf  >= umbral_rf  else 0
    votos     = pred_xgb + pred_rf

    if votos == 2:
        estado = "🔴 ALERTA ROJA — FALLA DETECTADA"
        accion = "⛔ DETENER MÁQUINA — Notificar mantenimiento inmediatamente"
        clase  = "card-alerta"; icono = "🚨"
    elif votos == 1:
        estado = "🟡 AVISO PREVENTIVO"
        accion = "⚠️ Monitorear de cerca — Programar inspección"
        clase  = "card-aviso";  icono = "⚠️"
    else:
        estado = "🟢 OPERACIÓN NORMAL"
        accion = "✅ Continuar operación — Sin intervención requerida"
        clase  = "card-normal"; icono = "✅"

    return {
        "timestamp":   datetime.now().strftime("%H:%M:%S"),
        "fecha":       datetime.now().strftime("%Y-%m-%d"),
        "temperatura": float(datos.get('Air temperature [K]', 0)),
        "rpm":         int(datos.get('Rotational speed [rpm]', 0)),
        "torque":      float(datos.get('Torque [Nm]', 0)),
        "desgaste":    int(datos.get('Tool wear [min]', 0)),
        "tipo":        int(datos.get('Type_encoded', 0)),
        "proba_xgb":   round(float(proba_xgb), 4),
        "proba_rf":    round(float(proba_rf),   4),
        "pred_xgb":    int(pred_xgb),
        "pred_rf":     int(pred_rf),
        "votos":       int(votos),
        "estado":      estado,
        "accion":      accion,
        "clase_css":   clase,
        "icono":       icono,
    }

# ============================================
# FUNCIONES MQTT
# ============================================
def conectar_mqtt() -> Tuple[Optional[MQTTClient], bool, Optional[ConfigDict]]:
    try:
        config = obtener_config_mqtt()
        client = mqtt.Client(
            client_id=f"dashboard_torno_{int(time.time())}",
            protocol=mqtt.MQTTv5
        )
        client.tls_set(
            ca_certs=None, certfile=None, keyfile=None,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLS, ciphers=None
        )
        client.username_pw_set(config['username'], config['password'])
        client.connect(config['broker'], int(config['port']), keepalive=60)
        client.loop_start()
        time.sleep(2)
        if client.is_connected():
            return client, True, config
        return None, False, None
    except Exception as e:
        return None, False, str(e)  # type: ignore

def publicar_sensores(client, config, datos):
    client.publish(config['topicos']['sensores'], json.dumps(datos), qos=1)

def publicar_resultado(client, config, resultado):
    payload = json.dumps(resultado, indent=2)
    client.publish(config['topicos']['prediccion'], payload, qos=1)
    if resultado['votos'] == 2:
        client.publish(config['topicos']['alerta'], payload, qos=1)
    elif resultado['votos'] == 1:
        client.publish(config['topicos']['aviso'],  payload, qos=1)
    else:
        client.publish(config['topicos']['estado'], payload, qos=1)

# ============================================
# GUARDAR REGISTRO LOCAL (CSV)
# ============================================
def guardar_registro(resultado):
    try:
        archivo = 'output/registro_eventos.csv'
        os.makedirs('output', exist_ok=True)
        df_r = pd.DataFrame([{
            'fecha':       resultado['fecha'],
            'hora':        resultado['timestamp'],
            'temperatura': resultado['temperatura'],
            'rpm':         resultado['rpm'],
            'torque':      resultado['torque'],
            'desgaste':    resultado['desgaste'],
            'proba_xgb':   resultado['proba_xgb'],
            'proba_rf':    resultado['proba_rf'],
            'votos':       resultado['votos'],
            'estado':      resultado['estado'],
        }])
        modo = 'w' if not os.path.exists(archivo) else 'a'
        df_r.to_csv(archivo, index=False, mode=modo, header=(modo == 'w'))
    except Exception:
        pass

# ============================================
# CAMBIO 3: GUARDAR EN FIREBASE (solo avisos/alertas en producción)
# ============================================
def guardar_en_firebase(resultado: ResultadoDict) -> None:
    """
    Guarda SOLO AVISOS (votos=1) y ALERTAS (votos=2) en Firebase Firestore.
    - No guarda operaciones normales (votos=0).
    - Solo guarda en modo Producción, no en simulación.
    """
    if not firebase_disponible or db is None:
        return

    # Solo guardar incidencias relevantes
    if resultado['votos'] == 0:
        return

    # Solo en modo Producción
    if st.session_state.get('modo', '') != 'Produccion':
        return

    try:
        doc_ref = db.collection('alertas_torno').document()
        doc_ref.set({
            'fecha':           resultado['fecha'],
            'hora':            resultado['timestamp'],
            'temperatura_k':   resultado['temperatura'],
            'temperatura_c':   round(resultado['temperatura'] - 273.15, 2),
            'rpm':             resultado['rpm'],
            'torque_nm':       resultado['torque'],
            'desgaste_min':    resultado['desgaste'],
            'tipo':            resultado['tipo'],
            'proba_xgb':       resultado['proba_xgb'],
            'proba_rf':        resultado['proba_rf'],
            'votos':           resultado['votos'],
            'estado':          resultado['estado'],
            'accion':          resultado['accion'],
            'nivel':           'alerta' if resultado['votos'] == 2 else 'aviso',
            'creado': firestore.SERVER_TIMESTAMP,  # type: ignore
        })
        st.session_state.firebase_guardados += 1
        print(f"[FIREBASE] Guardado: {resultado['estado']}")
    except Exception as e:
        print(f"[FIREBASE] Error al guardar: {e}")

# ============================================
# PROCESAR LECTURA (llamar SOLO desde el hilo principal de Streamlit)
# ============================================
def procesar_lectura(datos, client=None, config=None):
    resultado = predecir_consenso(datos)

    if resultado['votos'] == 2:
        st.session_state.contador_alerta += 1
    elif resultado['votos'] == 1:
        st.session_state.contador_aviso  += 1
    else:
        st.session_state.contador_normal += 1

    st.session_state.historial.append(resultado)
    if len(st.session_state.historial) > 100:
        st.session_state.historial = st.session_state.historial[-100:]

    st.session_state.probabilidades_xgb.append(resultado['proba_xgb'])
    st.session_state.probabilidades_rf.append(resultado['proba_rf'])
    st.session_state.temperaturas.append(resultado['temperatura'])
    st.session_state.rpms.append(resultado['rpm'])
    st.session_state.torques.append(resultado['torque'])
    st.session_state.desgastes.append(resultado['desgaste'])
    st.session_state.timestamps_hist.append(resultado['timestamp'])

    for lista in ['probabilidades_xgb','probabilidades_rf','temperaturas',
                  'rpms','torques','desgastes','timestamps_hist']:
        if len(st.session_state[lista]) > 60:
            st.session_state[lista] = st.session_state[lista][-60:]

    st.session_state.ultimo_resultado   = resultado
    st.session_state.lecturas_procesadas += 1

    if client is not None and client.is_connected() and config is not None:
        publicar_resultado(client, config, resultado)

    guardar_registro(resultado)
    # CAMBIO 4: llamar a Firebase después del registro local
    guardar_en_firebase(resultado)

    return resultado

# ============================================
# HEADER PRINCIPAL
# ============================================
st.markdown('<p class="main-header">⚙ SISTEMA DE MANTENIMIENTO PREDICTIVO</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">TORNO HORIZONTAL  ◆  CONSENSO XGBOOST + RANDOM FOREST  ◆  HIVEMQ CLOUD</p>', unsafe_allow_html=True)

# Badge de estado Firebase junto al header
if firebase_disponible:
    st.markdown(
        '<div style="text-align:center;margin-bottom:8px;">'
        '<span class="firebase-badge firebase-badge-ok">🔥 FIREBASE CONECTADO</span>'
        '</div>',
        unsafe_allow_html=True
    )
else:
    st.markdown(
        '<div style="text-align:center;margin-bottom:8px;">'
        '<span class="firebase-badge">🔥 FIREBASE NO DISPONIBLE</span>'
        '</div>',
        unsafe_allow_html=True
    )

st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)

if not modelos_ok:
    st.error(f"⛔ ERROR AL CARGAR MODELOS: {error_msg}")
    st.error("Verifica que los archivos .pkl estén en la carpeta 'modelos/'")
    st.stop()

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.markdown("## ⚙️ CONFIGURACIÓN")

    modo_opciones = ["🎮 Simulación (Demo)", "🏭 Producción (Sensores Reales)"]
    modo_sel = st.radio("Modo de operación:", modo_opciones, index=0)
    st.session_state.modo = (
        "Simulacion" if ("Simulación" in (modo_sel or "") or "Simulacion" in (modo_sel or ""))
        else "Produccion"
    )
    es_simulacion = "imulaci" in (modo_sel or "")

    st.markdown("---")

    if es_simulacion:
        st.markdown("### 🎛️ Parámetros de Simulación")
        velocidad      = st.slider("Velocidad (lecturas/seg):", 0.5, 5.0, 1.0, 0.5)
        num_lecturas   = st.number_input("Cantidad de lecturas:", 10, 500, 100, 10)
        incluir_fallas = st.checkbox("Incluir datos de falla", value=True)
        balancear_demo = st.checkbox("Balancear 50/50 para demo", value=False,
            help="Toma igual cantidad de fallos y normales para una demostración más impactante")

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            iniciar = st.button("▶ INICIAR",  type="primary", use_container_width=True)
            detener = st.button("⏹ DETENER", use_container_width=True)
        with col2:
            pausar = st.button("⏸ PAUSAR", use_container_width=True)

        if iniciar: st.session_state.simulacion_activa = True
        if pausar:  st.session_state.simulacion_activa = False
        if detener:
            st.session_state.simulacion_activa = False
            for k in ['historial','probabilidades_xgb','probabilidades_rf',
                      'temperaturas','rpms','torques','desgastes','timestamps_hist']:
                st.session_state[k] = []
            st.session_state.contador_normal   = 0
            st.session_state.contador_aviso    = 0
            st.session_state.contador_alerta   = 0
            st.session_state.lecturas_procesadas = 0
            st.rerun()
    else:
        st.markdown("### 📡 Conexión MQTT")
        st.info("Modo Producción: esperando datos reales del ESP32")
        if st.button("🔗 CONECTAR BROKER", type="primary", use_container_width=True):
            st.session_state.mqtt_queue = queue.Queue()
            client, conectado, config = conectar_mqtt()
            st.session_state.mqtt_client    = client
            st.session_state.mqtt_conectado = conectado
            st.session_state.config         = config

            if conectado and client is not None and config is not None:
                def _on_message(cli, userdata, msg):
                    try:
                        payload = msg.payload.decode()
                        datos   = json.loads(payload)
                        if ('Air temperature [K]'   in datos and
                                'Rotational speed [rpm]' in datos):
                            st.session_state.mqtt_queue.put(datos)
                    except Exception:
                        pass

                client.on_message = _on_message
                client.subscribe(config['topicos']['sensores'], qos=1)
                st.success("✅ Conectado a HiveMQ Cloud")
            else:
                st.error(f"❌ Error: {config}")

    # Conexión MQTT opcional en modo simulación
    if es_simulacion and not st.session_state.mqtt_conectado:
        st.markdown("---")
        if st.button("📡 Conectar MQTT (opcional)", use_container_width=True):
            client, conectado, config = conectar_mqtt()
            st.session_state.mqtt_client    = client
            st.session_state.mqtt_conectado = conectado
            st.session_state.config         = config

    st.markdown("---")
    st.markdown("### 📊 ESTADO DEL SISTEMA")
    st.metric("Lecturas procesadas", st.session_state.lecturas_procesadas)

    total      = max(1, st.session_state.lecturas_procesadas)
    pct_normal = st.session_state.contador_normal / total * 100
    pct_aviso  = st.session_state.contador_aviso  / total * 100
    pct_alerta = st.session_state.contador_alerta / total * 100
    st.markdown(f"🟢 Normal: **{pct_normal:.1f}%**")
    st.markdown(f"🟡 Aviso:  **{pct_aviso:.1f}%**")
    st.markdown(f"🔴 Alerta: **{pct_alerta:.1f}%**")

    # Estado Firebase en sidebar
    st.markdown("---")
    if firebase_disponible:
        st.success(f"🔥 Firebase: Conectado")
        st.metric("Eventos en Firestore", st.session_state.firebase_guardados)
        st.caption("Solo avisos y alertas en modo Producción")
    else:
        st.warning("🔥 Firebase: No disponible")

    if st.session_state.mqtt_conectado:
        st.success("📡 MQTT: Conectado")
    else:
        st.warning("📡 MQTT: Desconectado")

    if st.button("🔄 RESET CONTADORES", use_container_width=True):
        for k in ['contador_normal','contador_aviso','contador_alerta',
                  'lecturas_procesadas','firebase_guardados']:
            st.session_state[k] = 0
        for k in ['probabilidades_xgb','probabilidades_rf','temperaturas',
                  'rpms','torques','desgastes','timestamps_hist']:
            st.session_state[k] = []
        st.rerun()

# ============================================
# FILA 1: ESTADO + SENSORES + PREDICCIONES
# ============================================
col_estado, col_sensores, col_pred = st.columns([1.2, 1, 1])

with col_estado:
    st.markdown('<div class="section-title">ESTADO ACTUAL</div>', unsafe_allow_html=True)
    if st.session_state.ultimo_resultado is not None:
        u = st.session_state.ultimo_resultado
        st.markdown(f"""
        <div class="card-base {u['clase_css']}">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
                <span class="estado-icon">{u['icono']}</span>
                <span class="estado-titulo">{u['estado'].split('—')[0].strip()}</span>
            </div>
            <div class="accion-text">{u['accion']}</div>
            <div style="margin-top:12px;font-family:'Share Tech Mono',monospace;font-size:11px;color:#4a90d9;opacity:0.7;">
                ⏱ {u['timestamp']} &nbsp;|&nbsp; 📅 {u['fecha']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        riesgo_pct  = max(u['proba_xgb'], u['proba_rf']) * 100
        color_gauge = "#00e676" if riesgo_pct < 40 else ("#ffd740" if riesgo_pct < 70 else "#ff5252")
        fig_gauge   = go.Figure(go.Indicator(
            mode="gauge+number", value=riesgo_pct,
            number={'suffix':'%','font':{'size':28,'color':color_gauge,'family':'Rajdhani'}},
            title={'text':"NIVEL DE RIESGO",'font':{'size':12,'color':'#4a90d9','family':'Exo 2'}},
            gauge={
                'axis':{'range':[0,100],'tickcolor':'#4a90d9','tickfont':{'color':'#4a90d9','size':9}},
                'bar':{'color':color_gauge,'thickness':0.25},
                'bgcolor':'rgba(0,0,0,0)','borderwidth':0,
                'steps':[
                    {'range':[0,40],  'color':'rgba(0,200,83,0.12)'},
                    {'range':[40,70], 'color':'rgba(255,171,0,0.12)'},
                    {'range':[70,100],'color':'rgba(255,23,68,0.12)'},
                ],
                'threshold':{'line':{'color':color_gauge,'width':3},'thickness':0.8,'value':riesgo_pct},
            }
        ))
        fig_gauge.update_layout(
            height=200, margin=dict(l=20,r=20,t=30,b=10),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font={'color':'#a8c8e8'}
        )
        st.plotly_chart(fig_gauge, use_container_width=True)
    else:
        st.info("⏳ Esperando primera lectura...")

with col_sensores:
    st.markdown('<div class="section-title">ÚLTIMA LECTURA DE SENSORES</div>', unsafe_allow_html=True)
    if st.session_state.ultimo_resultado is not None:
        u = st.session_state.ultimo_resultado
        sensores = [
            ("🌡️", "TEMPERATURA",   f"{u['temperatura']:.1f} K", f"= {u['temperatura']-273.15:.1f} °C"),
            ("⚡",  "VELOCIDAD RPM", f"{u['rpm']}",               "revoluciones/min"),
            ("🔧", "TORQUE",         f"{u['torque']:.1f} Nm",      "par de torsión"),
            ("⏱️", "DESGASTE HERR.", f"{u['desgaste']} min",       "tiempo de uso"),
            ("🏷️", "TIPO MÁQUINA",  f"Tipo {u['tipo']}",          "clasificación"),
        ]
        for icono, label, valor, sub in sensores:
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                        padding:10px 15px;margin:4px 0;border-radius:8px;
                        background:rgba(10,21,37,0.8);border:1px solid rgba(30,58,95,0.6);">
                <div>
                    <span style="font-size:18px;">{icono}</span>
                    <span style="color:#4a90d9;font-size:11px;letter-spacing:1px;
                                 text-transform:uppercase;margin-left:8px;font-family:'Exo 2',sans-serif;">{label}</span>
                    <div style="color:#607d8b;font-size:10px;margin-left:30px;margin-top:2px;">{sub}</div>
                </div>
                <div style="font-family:'Share Tech Mono',monospace;color:#00d4ff;font-size:18px;font-weight:bold;">{valor}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Sin datos de sensores")

with col_pred:
    st.markdown('<div class="section-title">PREDICCIONES DE MODELOS</div>', unsafe_allow_html=True)
    if st.session_state.ultimo_resultado is not None:
        u = st.session_state.ultimo_resultado
        for modelo, proba, pred, umbral in [
            ("XGBoost",      u['proba_xgb'], u['pred_xgb'], umbral_xgb),
            ("Random Forest",u['proba_rf'],  u['pred_rf'],  umbral_rf),
        ]:
            clase_val   = "pred-value-danger" if pred == 1 else "pred-value-safe"
            estado_txt  = "⛔ FALLO" if pred == 1 else "✅ NORMAL"
            color_barra = "#ff5252" if pred == 1 else "#00e676"
            pct         = proba * 100
            st.markdown(f"""
            <div style="background:rgba(10,21,37,0.8);border:1px solid rgba(30,58,95,0.6);
                        border-radius:10px;padding:15px;margin-bottom:10px;">
                <div class="pred-model-name">{modelo}</div>
                <div class="{clase_val}" style="font-family:'Share Tech Mono',monospace;
                     font-size:34px;font-weight:bold;line-height:1.1;">{pct:.1f}%</div>
                <div style="font-size:12px;color:{'#ff8a80' if pred==1 else '#69f0ae'};
                            margin:5px 0;font-family:'Exo 2',sans-serif;">{estado_txt}</div>
                <div style="background:rgba(255,255,255,0.05);border-radius:4px;height:6px;margin-top:8px;">
                    <div style="background:{color_barra};height:6px;border-radius:4px;
                                width:{pct:.1f}%;box-shadow:0 0 8px {color_barra};"></div>
                </div>
                <div style="display:flex;justify-content:space-between;margin-top:4px;
                            font-size:10px;color:#4a90d9;font-family:'Share Tech Mono',monospace;">
                    <span>0%</span><span>Umbral: {umbral*100:.1f}%</span><span>100%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        votos = u['votos']
        colores_voto = {0:"#00e676", 1:"#ffd740", 2:"#ff5252"}
        # Indicador de si fue guardado en Firebase
        firebase_nota = ""
        if firebase_disponible and votos > 0 and st.session_state.modo == 'Produccion':
            firebase_nota = '<div style="font-size:10px;color:#ffc107;margin-top:6px;">🔥 Evento guardado en Firestore</div>'
        st.markdown(f"""
        <div style="background:rgba(0,212,255,0.05);border:1px solid rgba(0,212,255,0.2);
                    border-radius:8px;padding:12px;text-align:center;">
            <div style="font-family:'Rajdhani',sans-serif;font-size:13px;color:#4a90d9;letter-spacing:2px;">VOTOS POR FALLO</div>
            <div style="font-family:'Share Tech Mono',monospace;font-size:32px;
                        color:{colores_voto[votos]};text-shadow:0 0 15px {colores_voto[votos]};">
                {votos} / 2
            </div>
            <div style="font-size:10px;color:#607d8b;font-family:'Exo 2',sans-serif;">
                {'Consenso de falla detectado' if votos==2 else ('Un modelo detecta riesgo' if votos==1 else 'Sin detección de falla')}
            </div>
            {firebase_nota}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Sin predicciones aún")

# ============================================
# FILA 2: CONTADORES SEMAFÓRICOS
# ============================================
st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)
col_n, col_a, col_r = st.columns(3)
with col_n:
    st.markdown(f"""
    <div class="counter-card-normal">
        <span class="counter-icon">🟢</span>
        <div class="counter-number-normal">{st.session_state.contador_normal}</div>
        <div class="counter-label counter-label-normal">OPERACIÓN NORMAL</div>
        <div style="font-size:11px;color:#2e7d50;margin-top:6px;font-family:'Exo 2',sans-serif;">Todo funciona correctamente</div>
    </div>""", unsafe_allow_html=True)
with col_a:
    st.markdown(f"""
    <div class="counter-card-aviso">
        <span class="counter-icon">🟡</span>
        <div class="counter-number-aviso">{st.session_state.contador_aviso}</div>
        <div class="counter-label counter-label-aviso">AVISOS PREVENTIVOS</div>
        <div style="font-size:11px;color:#7a5c00;margin-top:6px;font-family:'Exo 2',sans-serif;">Revisar antes de continuar</div>
    </div>""", unsafe_allow_html=True)
with col_r:
    st.markdown(f"""
    <div class="counter-card-alerta">
        <span class="counter-icon">🔴</span>
        <div class="counter-number-alerta">{st.session_state.contador_alerta}</div>
        <div class="counter-label counter-label-alerta">ALERTAS CRÍTICAS</div>
        <div style="font-size:11px;color:#7a0000;margin-top:6px;font-family:'Exo 2',sans-serif;">Detener máquina inmediatamente</div>
    </div>""", unsafe_allow_html=True)

# ============================================
# FILA 3: GRÁFICO PRINCIPAL DE PROBABILIDADES
# ============================================
st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">📈 PROBABILIDAD DE FALLO EN TIEMPO REAL</div>', unsafe_allow_html=True)

if len(st.session_state.probabilidades_xgb) > 1:
    xs = list(range(len(st.session_state.probabilidades_xgb)))
    fig_prob = go.Figure()
    fig_prob.add_trace(go.Scatter(
        x=xs, y=st.session_state.probabilidades_xgb, name='XGBoost',
        mode='lines+markers', line=dict(color='#00d4ff', width=2.5),
        marker=dict(size=5, color='#00d4ff', symbol='circle'),
        fill='tozeroy', fillcolor='rgba(0,212,255,0.08)'
    ))
    fig_prob.add_trace(go.Scatter(
        x=xs, y=st.session_state.probabilidades_rf, name='Random Forest',
        mode='lines+markers', line=dict(color='#69f0ae', width=2.5),
        marker=dict(size=5, color='#69f0ae', symbol='diamond'),
        fill='tozeroy', fillcolor='rgba(105,240,174,0.08)'
    ))
    fig_prob.add_hline(y=umbral_xgb, line_dash="dash", line_color="#00d4ff", line_width=1.5,
                       annotation_text=f"Umbral XGB ({umbral_xgb:.2f})",
                       annotation_font_color="#00d4ff", annotation_font_size=11)
    fig_prob.add_hline(y=umbral_rf, line_dash="dash", line_color="#69f0ae", line_width=1.5,
                       annotation_text=f"Umbral RF ({umbral_rf:.2f})",
                       annotation_font_color="#69f0ae", annotation_font_size=11)
    fig_prob.add_hrect(y0=max(umbral_xgb, umbral_rf), y1=1.0,
                       fillcolor="rgba(255,23,68,0.06)", line_width=0,
                       annotation_text="⚠ ZONA CRÍTICA", annotation_position="top left",
                       annotation_font_color="#ff5252", annotation_font_size=10)
    fig_prob.update_layout(
        height=320, margin=dict(l=10,r=10,t=20,b=10),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(10,21,37,0.6)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(color='#a8c8e8', family='Exo 2', size=11),
                    bgcolor='rgba(0,0,0,0)', bordercolor='rgba(0,0,0,0)'),
        yaxis=dict(range=[0,1.05], title="Probabilidad de Fallo",
                   gridcolor='rgba(30,58,95,0.4)', tickfont=dict(color='#4a90d9', size=10),
                   titlefont=dict(color='#4a90d9', size=12), zeroline=False),
        xaxis=dict(title="Número de Lectura",
                   gridcolor='rgba(30,58,95,0.4)', tickfont=dict(color='#4a90d9', size=10),
                   titlefont=dict(color='#4a90d9', size=12)),
        font=dict(family='Exo 2')
    )
    st.plotly_chart(fig_prob, use_container_width=True)
else:
    st.info("⏳ Esperando datos para el gráfico de probabilidades...")

# ============================================
# FILA 4: GRÁFICOS DE SENSORES (2x2)
# ============================================
st.markdown('<div class="section-title">📊 VARIABLES DE SENSORES EN TIEMPO REAL</div>', unsafe_allow_html=True)

if len(st.session_state.temperaturas) > 1:
    xs = list(range(len(st.session_state.temperaturas)))
    fig_sensores = make_subplots(
        rows=2, cols=2,
        subplot_titles=("🌡️ Temperatura del Aire (K)", "⚡ Velocidad de Rotación (RPM)",
                        "🔧 Torque (Nm)",              "⏱️ Desgaste de Herramienta (min)"),
        vertical_spacing=0.18, horizontal_spacing=0.1
    )
    trazas = [
        (st.session_state.temperaturas, '#ff6b6b', 'rgba(255,107,107,0.1)', 'Temp',    1, 1),
        (st.session_state.rpms,         '#4ecdc4', 'rgba(78,205,196,0.1)',  'RPM',     1, 2),
        (st.session_state.torques,      '#ffd93d', 'rgba(255,217,61,0.1)', 'Torque',  2, 1),
        (st.session_state.desgastes,    '#c77dff', 'rgba(199,125,255,0.1)','Desgaste',2, 2),
    ]
    for datos_y, color, fill_color, nombre, row, col in trazas:
        fig_sensores.add_trace(go.Scatter(
            x=xs, y=datos_y, name=nombre, mode='lines', fill='tozeroy',
            line=dict(color=color, width=2), fillcolor=fill_color
        ), row=row, col=col)
    fig_sensores.update_layout(
        height=420, showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(10,21,37,0.6)',
        margin=dict(l=10,r=10,t=40,b=10),
        font=dict(color='#a8c8e8', family='Exo 2', size=10)
    )
    fig_sensores.update_annotations(font_size=12, font_color='#4a90d9')
    for row in [1,2]:
        for col in [1,2]:
            fig_sensores.update_xaxes(gridcolor='rgba(30,58,95,0.4)', zeroline=False,
                                      tickfont=dict(color='#4a90d9', size=9), row=row, col=col)
            fig_sensores.update_yaxes(gridcolor='rgba(30,58,95,0.4)', zeroline=False,
                                      tickfont=dict(color='#4a90d9', size=9), row=row, col=col)
    st.plotly_chart(fig_sensores, use_container_width=True)
else:
    st.info("⏳ Esperando datos de sensores para los gráficos...")

# ============================================
# FILA 5: PASTEL + BARRAS
# ============================================
if st.session_state.lecturas_procesadas > 0:
    col_pie, col_bar = st.columns(2)
    with col_pie:
        st.markdown('<div class="section-title">🎯 DISTRIBUCIÓN DE ESTADOS</div>', unsafe_allow_html=True)
        fig_pie = go.Figure(go.Pie(
            labels=['✅ Normal','⚠️ Aviso','🔴 Alerta'],
            values=[st.session_state.contador_normal,
                    st.session_state.contador_aviso,
                    st.session_state.contador_alerta],
            hole=0.55,
            marker=dict(colors=['#00e676','#ffd740','#ff5252'],
                        line=dict(color='#060d18', width=3)),
            textfont=dict(family='Exo 2', size=12, color='white'),
            hovertemplate='<b>%{label}</b><br>Cantidad: %{value}<br>Porcentaje: %{percent}<extra></extra>'
        ))
        fig_pie.add_annotation(
            text=f"<b>{st.session_state.lecturas_procesadas}</b><br><span style='font-size:10px'>lecturas</span>",
            x=0.5, y=0.5, font=dict(size=16, color='#a8c8e8', family='Rajdhani'), showarrow=False
        )
        fig_pie.update_layout(
            height=300, margin=dict(l=20,r=20,t=20,b=20),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            showlegend=True,
            legend=dict(font=dict(color='#a8c8e8', family='Exo 2', size=11), bgcolor='rgba(0,0,0,0)')
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_bar:
        st.markdown('<div class="section-title">📉 COMPARATIVA DE MODELOS</div>', unsafe_allow_html=True)
        if len(st.session_state.probabilidades_xgb) > 0:
            p_xgb = np.array(st.session_state.probabilidades_xgb)
            p_rf  = np.array(st.session_state.probabilidades_rf)
            categorias = ['Mínimo','Promedio','Máximo','Actual']
            vals_xgb = [float(p_xgb.min()), float(p_xgb.mean()), float(p_xgb.max()), float(p_xgb[-1])]
            vals_rf  = [float(p_rf.min()),  float(p_rf.mean()),  float(p_rf.max()),  float(p_rf[-1])]
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                name='XGBoost', x=categorias, y=[v*100 for v in vals_xgb],
                marker=dict(color='#00d4ff', opacity=0.85, line=dict(color='#00d4ff', width=1)),
                text=[f"{v*100:.1f}%" for v in vals_xgb], textposition='outside',
                textfont=dict(color='#00d4ff', size=11, family='Share Tech Mono')
            ))
            fig_bar.add_trace(go.Bar(
                name='Random Forest', x=categorias, y=[v*100 for v in vals_rf],
                marker=dict(color='#69f0ae', opacity=0.85, line=dict(color='#69f0ae', width=1)),
                text=[f"{v*100:.1f}%" for v in vals_rf], textposition='outside',
                textfont=dict(color='#69f0ae', size=11, family='Share Tech Mono')
            ))
            fig_bar.add_hline(y=umbral_xgb*100, line_dash="dot", line_color="#00d4ff", line_width=1,
                              annotation_text="Umbral XGB",
                              annotation_font_color="#00d4ff", annotation_font_size=10)
            fig_bar.update_layout(
                height=300, barmode='group',
                margin=dict(l=10,r=10,t=20,b=10),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(10,21,37,0.6)',
                legend=dict(font=dict(color='#a8c8e8', family='Exo 2', size=11), bgcolor='rgba(0,0,0,0)'),
                yaxis=dict(range=[0,115], gridcolor='rgba(30,58,95,0.4)',
                           tickfont=dict(color='#4a90d9', size=9),
                           title='Probabilidad (%)', titlefont=dict(color='#4a90d9', size=11),
                           zeroline=False),
                xaxis=dict(gridcolor='rgba(30,58,95,0.4)', tickfont=dict(color='#4a90d9', size=10))
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Sin datos suficientes")

# ============================================
# FILA 6: HISTORIAL
# ============================================
st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">📋 HISTORIAL DE PREDICCIONES (últimas 20)</div>', unsafe_allow_html=True)

if len(st.session_state.historial) > 0:
    df_hist = pd.DataFrame(st.session_state.historial[-20:])
    df_hist = df_hist[['timestamp','temperatura','rpm','torque','desgaste',
                        'proba_xgb','proba_rf','votos','estado']].copy()
    df_hist.columns = ['Hora','Temp (K)','RPM','Torque (Nm)','Desgaste','XGB %','RF %','Votos','Estado']
    df_hist['XGB %'] = (df_hist['XGB %'] * 100).round(1)
    df_hist['RF %']  = (df_hist['RF %']  * 100).round(1)

    def color_fila(val):
        if 'ALERTA' in str(val) or 'ROJA' in str(val):
            return 'background-color:#2a0000;color:#ff5252;font-weight:bold'
        elif 'AVISO' in str(val) or 'PREVENT' in str(val):
            return 'background-color:#2a1a00;color:#ffd740;font-weight:bold'
        return 'background-color:#0a2a1a;color:#00e676'

    st.dataframe(df_hist.style.map(color_fila, subset=['Estado']),
                 use_container_width=True, height=300)
else:
    st.info("⏳ Sin historial todavía")

# ============================================
# LÓGICA DE SIMULACIÓN
# ============================================
if (es_simulacion and
        st.session_state.simulacion_activa and
        st.session_state.mqtt_conectado and
        st.session_state.config is not None):
    try:
        df_sim = pd.read_csv('datos/ai4i2020_clean.csv')
        if not incluir_fallas:
            df_sim = df_sim[df_sim['Machine failure'] == 0]
        if balancear_demo and incluir_fallas:
            fallos   = df_sim[df_sim['Machine failure'] == 1]
            normales = df_sim[df_sim['Machine failure'] == 0].sample(n=len(fallos), random_state=42)
            df_sim   = pd.concat([fallos, normales]).sample(frac=1, random_state=42)

        n_muestra  = int(min(num_lecturas, len(df_sim)))
        df_muestra = df_sim.sample(n=n_muestra)
        progress_bar = st.progress(0)
        status_text  = st.empty()

        for i, (_, row) in enumerate(df_muestra.iterrows()):
            if not st.session_state.simulacion_activa:
                break
            datos = {
                "Type_encoded":            int(row['Type_encoded']),
                "Air temperature [K]":     float(row['Air temperature [K]']),
                "Process temperature [K]": float(row['Process temperature [K]']),
                "Rotational speed [rpm]":  int(row['Rotational speed [rpm]']),
                "Torque [Nm]":             float(row['Torque [Nm]']),
                "Tool wear [min]":         int(row['Tool wear [min]']),
                "timestamp":               datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            if st.session_state.mqtt_client is not None and st.session_state.config is not None:
                publicar_sensores(st.session_state.mqtt_client, st.session_state.config, datos)

            resultado = procesar_lectura(datos, st.session_state.mqtt_client, st.session_state.config)
            progress_bar.progress((i + 1) / n_muestra)
            status_text.text(f"📡 Lectura {i+1}/{n_muestra} | {resultado['estado']}")
            time.sleep(1.0 / velocidad)
            st.rerun()

        st.session_state.simulacion_activa = False
        progress_bar.empty()
        status_text.success(f"✅ Simulación completada: {n_muestra} lecturas procesadas")
        st.rerun()

    except Exception as e:
        st.error(f"❌ Error en simulación: {e}")
        st.session_state.simulacion_activa = False

# ============================================
# MODO PRODUCCION - Polling directo a HiveMQ
# ============================================
if not es_simulacion and st.session_state.mqtt_conectado and st.session_state.config is not None:
    st.markdown("---")
    st.markdown('<div class="section-title">MODO PRODUCCION ACTIVO</div>', unsafe_allow_html=True)
    st.success(f"Escuchando: **{st.session_state.config['topicos']['sensores']}**")

    try:
        import paho.mqtt.client as mqtt_poll

        datos_recibidos = []

        def on_message_poll(client, userdata, msg):
            try:
                payload = msg.payload.decode()
                datos = json.loads(payload)
                if 'Air temperature [K]' in datos:
                    datos_recibidos.append(datos)
                    client.disconnect()
            except Exception:
                pass

        client_poll = mqtt_poll.Client(protocol=mqtt_poll.MQTTv5)
        client_poll.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)
        client_poll.username_pw_set(
            st.session_state.config['username'],
            st.session_state.config['password']
        )
        client_poll.on_message = on_message_poll
        client_poll.connect(st.session_state.config['broker'], st.session_state.config['port'], 60)
        client_poll.loop_start()
        time.sleep(0.5)
        client_poll.subscribe(st.session_state.config['topicos']['sensores'], qos=1)
        time.sleep(1.5)
        client_poll.loop_stop()
        client_poll.disconnect()

        if datos_recibidos:
            procesar_lectura(datos_recibidos[0], None, st.session_state.config)
            st.info(f"Mensajes recibidos: {len(datos_recibidos)} | Procesados: {st.session_state.lecturas_procesadas}")
            st.rerun()
        else:
            st.warning(f"No se recibieron mensajes. Reintentando... | Procesados: {st.session_state.lecturas_procesadas}")
    except Exception as e:
        st.error(f"Error: {e}")

    time.sleep(0.3)
    st.rerun()

# ============================================
# LEYENDA EXPLICATIVA
# ============================================
st.markdown("""
<div style="background:rgba(10,21,37,0.8);border:1px solid rgba(30,58,95,0.6);
            border-radius:10px;padding:15px 25px;margin:15px 0;
            font-family:'Exo 2',sans-serif;font-size:12px;">
    <div style="color:#4a90d9;font-size:11px;letter-spacing:2px;text-transform:uppercase;
                margin-bottom:12px;font-weight:600;">📖 GUÍA RÁPIDA DE ESTADOS</div>
    <div style="display:flex;gap:30px;flex-wrap:wrap;justify-content:space-around;">
        <div style="text-align:center;">
            <div style="font-size:24px;">🟢</div>
            <div style="color:#00e676;font-weight:700;margin:4px 0;">NORMAL</div>
            <div style="color:#607d8b;font-size:11px;">Ambos modelos predicen<br>operación sin riesgo</div>
        </div>
        <div style="text-align:center;">
            <div style="font-size:24px;">🟡</div>
            <div style="color:#ffd740;font-weight:700;margin:4px 0;">AVISO</div>
            <div style="color:#607d8b;font-size:11px;">1 modelo detecta riesgo.<br>Monitorear de cerca</div>
        </div>
        <div style="text-align:center;">
            <div style="font-size:24px;">🔴</div>
            <div style="color:#ff5252;font-weight:700;margin:4px 0;">ALERTA</div>
            <div style="color:#607d8b;font-size:11px;">Ambos modelos detectan falla.<br>Detener máquina YA</div>
        </div>
        <div style="text-align:center;">
            <div style="font-size:24px;">🤖</div>
            <div style="color:#00d4ff;font-weight:700;margin:4px 0;">CONSENSO</div>
            <div style="color:#607d8b;font-size:11px;">XGBoost + Random Forest<br>votan en conjunto</div>
        </div>
        <div style="text-align:center;">
            <div style="font-size:24px;">🔥</div>
            <div style="color:#ffc107;font-weight:700;margin:4px 0;">FIREBASE</div>
            <div style="color:#607d8b;font-size:11px;">Avisos y alertas guardados<br>en Firestore (Producción)</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================
# FOOTER
# ============================================
firebase_status = "🔥 Firebase Firestore ACTIVO" if firebase_disponible else "🔥 Firebase NO disponible"
st.markdown(
    f'<div class="footer">'
    f'⚙ SISTEMA DE MANTENIMIENTO PREDICTIVO — TORNO HORIZONTAL &nbsp;|&nbsp; '
    f'XGBoost (umbral={umbral_xgb:.2f}) + Random Forest (umbral={umbral_rf:.2f}) &nbsp;|&nbsp; '
    f'HiveMQ Cloud TLS &nbsp;|&nbsp; Consenso de Doble Verificación &nbsp;|&nbsp; {firebase_status}'
    f'</div>',
    unsafe_allow_html=True
)