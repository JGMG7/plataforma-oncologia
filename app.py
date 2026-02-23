import streamlit as st
import time
import datetime
import pandas as pd
from supabase import create_client, Client

st.set_page_config(page_title="DTx Oncología | Udelar", page_icon="🧬", layout="wide")

# --- 1. CONEXIÓN A LA NUBE ---
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

try:
    supabase: Client = init_connection()
except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.stop()

# --- 2. GESTIÓN DE SESIONES ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_id = None
    st.session_state.cohorte = None

def calcular_semaforo(eficiencia, latencia, fatiga, estres, dolor_max):
    if fatiga >= 8 or dolor_max >= 7: return "🔴 ROJO"
    elif eficiencia < 85.0 or latencia > 45 or fatiga >= 5 or estres >= 6: return "🟡 AMARILLO"
    else: return "🟢 VERDE"

hoy_str = str(datetime.date.today())

# =====================================================================
# 🔐 PANTALLA DE LOGIN
# =====================================================================
if not st.session_state.logged_in:
    col_izq, col_login, col_der = st.columns([1, 2, 1])
    with col_login:
        st.markdown("<h2 style='text-align: center;'>🧬 DTx Oncología</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Plataforma de Ensayo Clínico - Acceso Restringido</p>", unsafe_allow_html=True)
        st.divider()
        
        tab_paciente, tab_investigador = st.tabs(["📱 Ingreso Pacientes", "🔬 Panel Investigador"])
        
        with tab_paciente:
            with st.form("login_paciente"):
                user_input = st.text_input("ID de Paciente (ej. SUBJ_042)").strip().upper()
                pin_input = st.text_input("PIN Secreto de 4 dígitos", type="password", max_chars=4)
                submitted = st.form_submit_button("Ingresar a mi Triage 🚀", use_container_width=True, type="primary")
                
                if submitted:
                    if user_input and pin_input:
                        with st.spinner("Verificando..."):
                            try:
                                res = supabase.table("pacientes").select("*").eq("id_paciente", user_input).execute()
                                if len(res.data) > 0:
                                    datos_bd = res.data[0]
                                    if str(datos_bd.get("pin")) == pin_input:
                                        st.session_state.logged_in = True
                                        st.session_state.role = "Paciente"
                                        st.session_state.user_id = datos_bd["id_paciente"]
                                        st.session_state.cohorte = datos_bd["cohorte"]
                                        st.rerun()
                                    else:
                                        st.error("❌ PIN incorrecto.")
                                else:
                                    st.error("❌ ID no encontrado.")
                            except Exception as e:
                                st.error(f"Error de red: {e}")
                    else:
                        st.warning("⚠️ Complete ambos campos.")

        with tab_investigador:
            with st.form("login_investigador"):
                pass_input = st.text_input("Contraseña Maestra", type="password")
                submitted_inv = st.form_submit_button("Desbloquear Radar Clínico 🔐", use_container_width=True, type="primary")
                
                if submitted_inv:
                    if pass_input == st.secrets.get("INVESTIGADOR_PASSWORD", "15.14.3.15.5.6.1."):
                        st.session_state.logged_in = True
                        st.session_state.role = "Investigador"
                        st.session_state.user_id = "Investigador Principal"
                        st.rerun()
                    else:
                        st.error("❌ Contraseña denegada.")
    st.stop() 

# =====================================================================
# 🚪 BARRA LATERAL
# =====================================================================
st.sidebar.title("Plataforma DTx 🧬")
if st.session_state.role == "Investigador": st.sidebar.success("✅ Conectado: Fisiólogo Clínico")
else:
    st.sidebar.info(f"👤 Sujeto: {st.session_state.user_id}")
    st.sidebar.caption(f"Cohorte: {st.session_state.cohorte}")

st.sidebar.divider()
if st.sidebar.button("Cerrar Sesión 🔒", use_container_width=True, type="primary"):
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_id = None
    st.rerun()

# =====================================================================
# 📱 UNIVERSO 1: PACIENTE
# =====================================================================
if st.session_state.role == "Paciente":
    col1, col_celular, col3 = st.columns([1, 2, 1])
    with col_celular:
        st.title("☀️ Triage Matutino")
        st.markdown(f"**Identidad Protegida:** Sujeto `{st.session_state.user_id}`")
        st.divider()
        
        st.subheader("💤 1. Arquitectura del Sueño")
        c1, c2 = st.columns(2)
        with c1: hora_acostar = st.time_input("🛌 Hora acostarse", datetime.time(22, 30))
        with c2: hora_despertar = st.time_input("🌅 Hora despertarse", datetime.time(6, 30))
            
        c3, c4 = st.columns(2)
        with c3: latencia = st.number_input("⏱️ Minutos hasta dormir:", 0, 180, 15, 5)
        with c4: despertares = st.number_input("🔄 Minutos despierto:", 0, 240, 0, 5)

        dt_acostar = datetime.datetime.combine(datetime.date.today(), hora_acostar)
        dt_despertar = datetime.datetime.combine(datetime.date.today(), hora_despertar)
        if dt_despertar <= dt_acostar: dt_despertar += datetime.timedelta(days=1)
            
        t_cama = (dt_despertar - dt_acostar).total_seconds() / 60
        t_dormido = max(0, t_cama - latencia - despertares) 
        eficiencia = (t_dormido / t_cama) * 100 if t_cama > 0 else 0

        st.info(f"📊 Dormiste **{t_dormido/60:.1f} hs netas**. Eficiencia: **{eficiencia:.1f}%**")

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
                    d = st.slider(f"Intensidad en {zona}:", 1, 10, 5)
                    dolor_max = max(dolor_max, d)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Enviar Reporte a la Clínica 🚀", use_container_width=True, type="primary"):
            color = calcular_semaforo(eficiencia, latencia, fatiga, estres, dolor_max)
            
            datos_triage = {
                "id_paciente": st.session_state.user_id, 
                "fecha": hoy_str, "estado_triage": "Completado", "semaforo": color, 
                "eficiencia_sueno": eficiencia, "latencia_min": latencia, "despertares_min": despertares, 
                "fatiga_bfi": fatiga, "estres_nccn": estres, "dolor_maximo": dolor_max, 
                "zonas_dolor": ", ".join(zonas_afectadas) if zonas_afectadas else "Ninguna"
            }
            with st.spinner("Transmitiendo..."):
                try:
                    existe = supabase.table("registros_diarios").select("id").eq("id_paciente", st.session_state.user_id).eq("fecha", hoy_str).execute()
                    if len(existe.data) > 0:
                        supabase.table("registros_diarios").update(datos_triage).eq("id", existe.data[0]["id"]).execute()
                    else:
                        supabase.table("registros_diarios").insert(datos_triage).execute()
                    st.success("✅ ¡Reporte guardado! Te esperamos a las 13:00 hrs.")
                except Exception as e:
                    st.error(f"Error de conexión: {e}")

# =====================================================================
# 🔬 UNIVERSO 2: INVESTIGADOR (CON VISUAL ANALYTICS)
# =====================================================================
elif st.session_state.role == "Investigador":
    st.title("📡 Radar Clínico y Analítica Longitudinal")
    
    try:
        res_pacientes = supabase.table("pacientes").select("*").execute()
        res_registros = supabase.table("registros_diarios").select("*").eq("fecha", hoy_str).execute()
        
        df_pacientes = pd.DataFrame(res_pacientes.data)
        if df_pacientes.empty: st.stop()
            
        if len(res_registros.data) > 0:
            df_radar = pd.merge(df_pacientes, pd.DataFrame(res_registros.data), on="id_paciente", how="left")
        else:
            df_radar = df_pacientes.copy()
            for col in ["estado_triage", "semaforo", "eficiencia_sueno", "fatiga_bfi", "dolor_maximo", "zonas_dolor", "estado_sesion"]:
                df_radar[col] = None
                
        # Mostrar Radar de Hoy
        df_mostrar = df_radar.rename(columns={
            "id_paciente": "ID Paciente", "cohorte": "Cohorte", "estado_triage": "Estado AM",
            "semaforo": "Semáforo", "eficiencia_sueno": "Eficiencia %", "fatiga_bfi": "Fatiga BFI", "dolor_maximo": "Dolor Máx"
        }).fillna({"Estado AM": "Pendiente", "Semáforo": "⚪", "Eficiencia %": 0.0, "Fatiga BFI": 0, "Dolor Máx": 0})
        
        st.subheader("👥 Cohorte Citada para Hoy")
        st.dataframe(df_mostrar[["ID Paciente", "Cohorte", "Estado AM", "Semáforo", "Eficiencia %", "Fatiga BFI", "Dolor Máx"]].set_index("ID Paciente"), use_container_width=True)
        st.divider()
        
        if not df_radar.empty:
            paciente_sel = st.selectbox("📋 Seleccionar paciente:", df_radar["id_paciente"].tolist())
            datos_pac = df_radar[df_radar["id_paciente"] == paciente_sel].iloc[0]
            
            # --- TABS PARA ORGANIZAR DATA ENTRY Y GRÁFICOS ---
            tab_hoy, tab_historial = st.tabs(["📝 Cuaderno de Sesión (Hoy)", "📈 Análisis Longitudinal (Histórico)"])
            
            with tab_hoy:
                if datos_pac.get("estado_triage") in ["Pendiente", None]:
                    st.warning("⚠️ El paciente no completó el Triage hoy.")
                else:
                    semaforo = str(datos_pac.get("semaforo", "⚪"))
                    cohorte = str(datos_pac.get("cohorte", "MAMA"))
                    
                    c_alerta1, c_alerta2 = st.columns(2)
                    if float(datos_pac.get("eficiencia_sueno", 100)) < 85.0:
                        c_alerta1.warning(f"💤 Alerta Neural: Eficiencia del sueño en {float(datos_pac.get('eficiencia_sueno', 0)):.1f}%.")
                    if float(datos_pac.get("dolor_maximo", 0)) > 0:
                        c_alerta2.error(f"📍 Alerta Biomecánica: Foco de dolor en {datos_pac.get('zonas_dolor', '')}.")

                    if "ROJO" in semaforo:
                        st.error("🚨 ZONA ROJA: TOXICIDAD AGUDA. Carga bloqueada.")
                        if st.button("Guardar Sesión Vagal 🫁"):
                            supabase.table("registros_diarios").update({"estado_sesion": "Completado", "protocolo_vagal": True, "rpe_sesion": 0}).eq("id_paciente", paciente_sel).eq("fecha", hoy_str).execute()
                            st.success("Guardado.")
                    else:
                        if "AMARILLO" in semaforo: st.warning("⚠️ ZONA AMARILLA: Down-Regulation (-1 Serie, +2 RIR).")
                        else: st.success("✅ ZONA VERDE: Homeostasis.")

                        c1, c2 = st.columns(2)
                        ej1 = "Prensa" if cohorte == "PROSTATA" else "Sentadilla Copa"
                        ej2 = "Press Máquina" if cohorte == "PROSTATA" else "Floor Press"
                        
                        val_k1 = 60.0 if cohorte == "PROSTATA" else 15.0
                        val_k2 = 35.0 if cohorte == "PROSTATA" else 10.0

                        with c1: kilos1 = st.number_input(f"Kilos ({ej1}):", min_value=0.0, value=val_k1, step=2.5)
                        with c2: kilos2 = st.number_input(f"Kilos ({ej2}):", min_value=0.0, value=val_k2, step=2.5)
                        
                        if cohorte == "MAMA" and kilos2 > 25.0:
                            st.error("🚨 **VIOLACIÓN DE REGLA CLÍNICA:** Riesgo de Linfedema. Reduzca la carga del tren superior.")
                        else:
                            rpe = st.slider("RPE (Carga Interna):", 0, 10, 6)
                            if st.button("Guardar Kilos en Nube 💾", type="primary"):
                                supabase.table("registros_diarios").update({
                                    "estado_sesion": "Completado", "ejercicio_1": ej1, "kilos_ejercicio_1": float(kilos1),
                                    "ejercicio_2": ej2, "kilos_ejercicio_2": float(kilos2), "rpe_sesion": rpe
                                }).eq("id_paciente", paciente_sel).eq("fecha", hoy_str).execute()
                                st.success("✅ Datos sincronizados.")

            with tab_historial:
                st.markdown(f"### 📈 Evolución Biomédica: `{paciente_sel}`")
                
                # Descargar todo el historial del paciente de Supabase
                res_hist = supabase.table("registros_diarios").select("fecha, fatiga_bfi, dolor_maximo, eficiencia_sueno, kilos_ejercicio_1, rpe_sesion").eq("id_paciente", paciente_sel).order("fecha").execute()
                
                if len(res_hist.data) > 1: # Mínimo 2 puntos para dibujar una línea
                    df_hist = pd.DataFrame(res_hist.data)
                    df_hist["fecha"] = pd.to_datetime(df_hist["fecha"]).dt.strftime('%d-%m') # Solo día y mes
                    df_hist.set_index("fecha", inplace=True)
                    
                    # Limpiamos nulos matemáticos para que la gráfica no se corte
                    df_hist.fillna(0, inplace=True)

                    col_g1, col_g2 = st.columns(2)
                    
                    with col_g1:
                        st.markdown("**1. Toxicidad Central (Fatiga vs Dolor)**")
                        st.caption("Síntomas reportados (0-10)")
                        st.line_chart(df_hist[["fatiga_bfi", "dolor_maximo"]], color=["#ff4b4b", "#ffa500"])
                        
                    with col_g2:
                        st.markdown("**2. Recuperación Autonómica (Eficiencia de Sueño %)**")
                        st.caption("Monitorización del Ritmo Circadiano")
                        st.line_chart(df_hist[["eficiencia_sueno"]], color=["#1f77b4"])
                        
                    st.markdown("**3. Carga Interna vs Carga Externa**")
                    st.caption("Kilos movilizados vs sRPE Percibido (0-10)")
                    st.line_chart(df_hist[["kilos_ejercicio_1", "rpe_sesion"]], color=["#2ca02c", "#9467bd"])
                else:
                    st.info("Aún no hay datos históricos suficientes. Las gráficas aparecerán en cuanto el paciente tenga 2 o más días registrados.")
                            
    except Exception as e:
        st.error(f"Error interno del Radar: {e}")