import streamlit as st
import time
import datetime
import pandas as pd
from supabase import create_client, Client

st.set_page_config(page_title="DTx Oncología | Udelar", page_icon="🧬", layout="wide")

# --- 1. CONEXIÓN A LA BÓVEDA EN LA NUBE ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase: Client = init_connection()
except Exception as e:
    st.error(f"Error de conexión. Revisa tus llaves en secrets.toml. Detalles: {e}")
    st.stop()

# --- 2. MOTOR ALGORÍTMICO MATUTINO ---
def calcular_semaforo(eficiencia, latencia, fatiga, estres, dolor_max):
    if fatiga >= 8 or dolor_max >= 7: return "🔴 ROJO"
    elif eficiencia < 85.0 or latencia > 45 or fatiga >= 5 or estres >= 6: return "🟡 AMARILLO"
    else: return "🟢 VERDE"

st.sidebar.title("Plataforma DTx 🧬")
rol = st.sidebar.radio("Rol de Usuario:", ["📱 Paciente (App Móvil)", "🔬 Fisiólogo (Tablet)"])
st.sidebar.markdown("---")
st.sidebar.caption("🟢 Conectado a Servidor Seguro en la Nube")

hoy_str = str(datetime.date.today())

# =====================================================================
# 📱 UNIVERSO 1: PACIENTE
# =====================================================================
if rol == "📱 Paciente (App Móvil)":
    col1, col_celular, col3 = st.columns([1, 2, 1])
    
    with col_celular:
        st.title("☀️ Triage Matutino")
        
        # Obtenemos los pacientes reales desde la Nube
        try:
            res_pacientes = supabase.table("pacientes").select("*").execute()
            lista_pacientes = [p["id_paciente"] for p in res_pacientes.data]
        except Exception:
            lista_pacientes = []

        if not lista_pacientes:
            st.warning("No hay pacientes en la base de datos.")
            st.stop()

        paciente_id = st.selectbox("Identificación:", lista_pacientes)
        st.divider()
        
        st.subheader("💤 1. Arquitectura del Sueño")
        c1, c2 = st.columns(2)
        with c1: hora_acostar = st.time_input("🛌 Hora de acostarse", datetime.time(22, 30))
        with c2: hora_despertar = st.time_input("🌅 Hora de despertarse", datetime.time(6, 30))
            
        c3, c4 = st.columns(2)
        with c3: latencia = st.number_input("⏱️ Minutos hasta dormirte:", 0, 180, 15, 5)
        with c4: despertares = st.number_input("🔄 Minutos despierto:", 0, 240, 0, 5)

        dt_acostar = datetime.datetime.combine(datetime.date.today(), hora_acostar)
        dt_despertar = datetime.datetime.combine(datetime.date.today(), hora_despertar)
        if dt_despertar <= dt_acostar: dt_despertar += datetime.timedelta(days=1)
            
        t_cama = (dt_despertar - dt_acostar).total_seconds() / 60
        t_dormido = max(0, t_cama - latencia - despertares) 
        eficiencia = (t_dormido / t_cama) * 100 if t_cama > 0 else 0

        st.info(f"📊 Has dormido **{t_dormido/60:.1f} hs netas**. Eficiencia: **{eficiencia:.1f}%**")

        st.divider()
        st.subheader("🔋 2. Fatiga y Estrés")
        fatiga = st.select_slider("Fatiga física (0=Energía | 10=Agotamiento)", list(range(11)), 2)
        estres = st.select_slider("Estrés/Ansiedad (0=Paz | 10=Angustia)", list(range(11)), 2)
        
        st.divider()
        st.subheader("🦴 3. Dolor Corporal")
        col_img, col_zonas = st.columns([1, 1.5])
        with col_img:
            svg_silueta = """<svg viewBox="0 0 100 200" xmlns="http://www.w3.org/2000/svg" style="max-height: 250px; display: block; margin: auto;"><circle cx="50" cy="25" r="14" fill="#e2e8f0" stroke="#94a3b8" stroke-width="2"/><path d="M 32 45 Q 50 40 68 45 L 62 100 L 38 100 Z" fill="#e2e8f0" stroke="#94a3b8" stroke-width="2"/><path d="M 32 45 Q 15 55 10 95" fill="none" stroke="#e2e8f0" stroke-width="10" stroke-linecap="round"/><path d="M 68 45 Q 85 55 90 95" fill="none" stroke="#e2e8f0" stroke-width="10" stroke-linecap="round"/><path d="M 42 100 L 35 175" fill="none" stroke="#e2e8f0" stroke-width="12" stroke-linecap="round"/><path d="M 58 100 L 65 175" fill="none" stroke="#e2e8f0" stroke-width="12" stroke-linecap="round"/><circle cx="32" cy="45" r="3.5" fill="#ef4444" /> <circle cx="68" cy="45" r="3.5" fill="#ef4444" /> <circle cx="50" cy="95" r="3.5" fill="#ef4444" /> <circle cx="38" cy="140" r="3.5" fill="#ef4444" /> <circle cx="62" cy="140" r="3.5" fill="#ef4444" /> </svg>"""
            st.markdown(svg_silueta, unsafe_allow_html=True)
        with col_zonas:
            zonas_afectadas = st.multiselect("📍 Zonas afectadas:", ["Hombro Izq", "Hombro Der", "Lumbar", "Rodillas", "Neuropatía"])
            dolor_max = 0
            if zonas_afectadas:
                for zona in zonas_afectadas:
                    d = st.slider(f"Intensidad en {zona} (1-10):", 1, 10, 5)
                    dolor_max = max(dolor_max, d)
        
        # INYECCIÓN DIRECTA A LA NUBE
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Enviar Reporte 🚀", use_container_width=True, type="primary"):
            color = calcular_semaforo(eficiencia, latencia, fatiga, estres, dolor_max)
            
            # Paquete JSON para la Nube
            datos_triage = {
                "id_paciente": paciente_id, 
                "fecha": hoy_str, 
                "estado_triage": "Completado",
                "semaforo": color, 
                "eficiencia_sueno": eficiencia, 
                "latencia_min": latencia,
                "despertares_min": despertares, 
                "fatiga_bfi": fatiga, 
                "estres_nccn": estres,
                "dolor_maximo": dolor_max, 
                "zonas_dolor": ", ".join(zonas_afectadas) if zonas_afectadas else "Ninguna"
            }
            
            with st.spinner("Cifrando y transmitiendo a la bóveda..."):
                try:
                    # 1. Comprobamos si el paciente ya reportó hoy
                    existe = supabase.table("registros_diarios").select("id").eq("id_paciente", paciente_id).eq("fecha", hoy_str).execute()
                    
                    # 2. Actualizamos o Insertamos para no duplicar datos
                    if len(existe.data) > 0:
                        id_registro = existe.data[0]["id"]
                        supabase.table("registros_diarios").update(datos_triage).eq("id", id_registro).execute()
                    else:
                        supabase.table("registros_diarios").insert(datos_triage).execute()
                        
                    st.success("✅ ¡Reporte guardado exitosamente! Te esperamos a las 13:00 hrs.")
                except Exception as e:
                    st.error(f"Error de conexión: {e}")

# =====================================================================
# 🔬 UNIVERSO 2: EL DASHBOARD DEL INVESTIGADOR
# =====================================================================
elif rol == "🔬 Fisiólogo (Tablet)":
    st.title("📡 Radar Clínico L-M-V")
    
    try:
        # 1. DESCARGA DE DATOS EN VIVO
        res_pacientes = supabase.table("pacientes").select("*").execute()
        res_registros = supabase.table("registros_diarios").select("*").eq("fecha", hoy_str).execute()
        
        # Cruzamos los pacientes con los reportes de HOY usando Pandas
        df_pacientes = pd.DataFrame(res_pacientes.data)
        if df_pacientes.empty:
            st.warning("No hay pacientes registrados.")
            st.stop()
            
        if len(res_registros.data) > 0:
            df_registros = pd.DataFrame(res_registros.data)
            df_radar = pd.merge(df_pacientes, df_registros, on="id_paciente", how="left")
        else:
            df_radar = df_pacientes.copy()
            for col in ["estado_triage", "semaforo", "eficiencia_sueno", "fatiga_bfi", "dolor_maximo", "zonas_dolor", "estado_sesion"]:
                df_radar[col] = None
                
        # Llenamos vacíos
        df_radar["estado_triage"] = df_radar["estado_triage"].fillna("Pendiente")
        df_radar["semaforo"] = df_radar["semaforo"].fillna("⚪")
        df_radar["eficiencia_sueno"] = df_radar["eficiencia_sueno"].fillna(0.0)
        df_radar["fatiga_bfi"] = df_radar["fatiga_bfi"].fillna(0)
        df_radar["dolor_maximo"] = df_radar["dolor_maximo"].fillna(0)
        df_radar["estado_sesion"] = df_radar["estado_sesion"].fillna("Pendiente")
        
        # Tabla Visual
        df_mostrar = df_radar.rename(columns={
            "id_paciente": "ID Paciente", "cohorte": "Cohorte", "estado_triage": "Estado AM",
            "semaforo": "Semáforo", "eficiencia_sueno": "Eficiencia %", "fatiga_bfi": "Fatiga BFI",
            "dolor_maximo": "Dolor Máx"
        })
        
        st.dataframe(df_mostrar[["ID Paciente", "Cohorte", "Estado AM", "Semáforo", "Eficiencia %", "Fatiga BFI", "Dolor Máx"]].set_index("ID Paciente"), use_container_width=True)
        st.divider()
        
        # 2. DATA ENTRY DEL LABORATORIO (Actualiza la Nube)
        st.subheader("📋 Intervención Intra-Sesión (Exporta a Nube)")
        
        if not df_radar.empty:
            paciente_sel = st.selectbox("Seleccionar paciente en camilla:", df_radar["id_paciente"].tolist())
            datos_pac = df_radar[df_radar["id_paciente"] == paciente_sel].iloc[0]
            
            estado_am = datos_pac["estado_triage"]
            semaforo = str(datos_pac["semaforo"])
            cohorte = str(datos_pac["cohorte"])
            
            if estado_am == "Pendiente":
                st.warning("⚠️ Este paciente aún no ha completado el Triage AM en su celular.")
            else:
                # Alertas Cruzadas
                c_alerta1, c_alerta2 = st.columns(2)
                if float(datos_pac["eficiencia_sueno"]) < 85.0:
                    c_alerta1.warning(f"💤 **Alerta Neural:** Eficiencia del sueño en {float(datos_pac['eficiencia_sueno']):.1f}%.")
                if float(datos_pac["dolor_maximo"]) > 0:
                    c_alerta2.error(f"📍 **Alerta Biomecánica:** Foco de dolor en {datos_pac['zonas_dolor']}.")

                st.markdown("---")

                # Prescripción Dinámica
                if "ROJO" in semaforo:
                    st.error("🚨 ZONA ROJA: TOXICIDAD AGUDA. Carga mecánica bloqueada.")
                    if st.button("Guardar Sesión Vagal en la Nube 🫁"):
                        supabase.table("registros_diarios").update({
                            "estado_sesion": "Completado", "protocolo_vagal": True, "rpe_sesion": 0
                        }).eq("id_paciente", paciente_sel).eq("fecha", hoy_str).execute()
                        st.success("✅ Guardado exitoso en Supabase.")
                else:
                    if "AMARILLO" in semaforo: st.warning("⚠️ ZONA AMARILLA: DOWN-REGULATION (-1 Serie, +2 RIR).")
                    else: st.success("✅ ZONA VERDE: HOMEOSTASIS (Dosis al 100%).")

                    st.markdown("#### Registro de Cargas Reales")
                    c1, c2 = st.columns(2)
                    
                    if cohorte == "PROSTATA":
                        ej1 = "Prensa de Piernas 45°"; ej2 = "Press Pecho (Máquina)"; val_k1 = 60.0; val_k2 = 35.0
                    else: 
                        ej1 = "Sentadilla Copa (Goblet)"; ej2 = "Floor Press c/ Mancuernas"; val_k1 = 15.0; val_k2 = 10.0

                    with c1: kilos1 = st.number_input(f"Kilos ({ej1}):", min_value=0.0, value=val_k1, step=2.5)
                    with c2: kilos2 = st.number_input(f"Kilos ({ej2}):", min_value=0.0, value=val_k2, step=2.5)

                    if cohorte == "MAMA" and kilos2 > 25.0:
                        st.error("🚨 **VIOLACIÓN DE REGLA CLÍNICA:** La carga en tren superior excede la progresión segura (Riesgo de Linfedema).")
                    else:
                        rpe = st.slider("Escala de Borg CR10 (Carga Interna):", 0, 10, 6)
                        
                        if st.button("Guardar Datos en eCRF 💾", type="primary"):
                            datos_sesion = {
                                "estado_sesion": "Completado",
                                "ejercicio_1": ej1, "kilos_ejercicio_1": float(kilos1),
                                "ejercicio_2": ej2, "kilos_ejercicio_2": float(kilos2),
                                "rpe_sesion": int(rpe)
                            }
                            supabase.table("registros_diarios").update(datos_sesion).eq("id_paciente", paciente_sel).eq("fecha", hoy_str).execute()
                            st.success("✅ ¡Datos exportados a la Nube! (Listos para Tidy Data)")
                            
    except Exception as e:
        st.error(f"Error interno del Radar: {e}")