import streamlit as st
import time
import datetime
import pandas as pd
from supabase import create_client, Client
import streamlit.components.v1 as components
import qrcode
from io import BytesIO

st.set_page_config(page_title="DTx Oncología | ISIEF-CURE-UDELAR", page_icon="🧬", layout="wide")

# =====================================================================
# ⚙️ INYECCIÓN PWA (CAMUFLAJE Y MODO APP NATIVA)
# =====================================================================
# 1. Ocultar menús web y evitar el rebote al hacer scroll
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    body { overscroll-behavior-y: contain; }
    </style>
""", unsafe_allow_html=True)

# 2. Forzar Standalone Mode (Pantalla Completa en iOS y Android)
components.html(
    """
    <script>
        var head = window.parent.document.querySelector("head");
        if (!head.querySelector('meta[name="apple-mobile-web-app-capable"]')) {
            var m1 = window.parent.document.createElement('meta'); m1.name = "apple-mobile-web-app-capable"; m1.content = "yes"; head.appendChild(m1);
            var m2 = window.parent.document.createElement('meta'); m2.name = "apple-mobile-web-app-status-bar-style"; m2.content = "black-translucent"; head.appendChild(m2);
            var m3 = window.parent.document.createElement('meta'); m3.name = "mobile-web-app-capable"; m3.content = "yes"; head.appendChild(m3);
        }
    </script>
    """, height=0, width=0
)

# --- CONEXIÓN A LA NUBE Y SESIÓN ---
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

try: supabase: Client = init_connection()
except Exception as e: st.error(f"Error de red: {e}"); st.stop()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None; st.session_state.user_id = None
    st.session_state.cohorte = None; st.session_state.grupo = None

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
                user_input = st.text_input("ID de Paciente (ej. SUBJ_042 o CTRL_001)").strip().upper()
                pin_input = st.text_input("PIN Secreto", type="password", max_chars=4)
                if st.form_submit_button("Ingresar a mi App 🚀", use_container_width=True, type="primary"):
                    with st.spinner("Verificando..."):
                        res = supabase.table("pacientes").select("*").eq("id_paciente", user_input).execute()
                        if len(res.data) > 0 and str(res.data[0].get("pin")) == pin_input:
                            st.session_state.logged_in = True; st.session_state.role = "Paciente"
                            st.session_state.user_id = res.data[0]["id_paciente"]
                            st.session_state.cohorte = res.data[0]["cohorte"]
                            st.session_state.grupo = res.data[0].get("grupo") or "EXPERIMENTAL"
                            st.rerun()
                        else: st.error("❌ Credenciales incorrectas.")

        with tab_investigador:
            with st.form("login_investigador"):
                pass_input = st.text_input("Contraseña Maestra", type="password")
                if st.form_submit_button("Desbloquear Radar Clínico 🔐", use_container_width=True, type="primary"):
                    if pass_input == st.secrets.get("INVESTIGADOR_PASSWORD", "15.14.15.3.5.6.1."):
                        st.session_state.logged_in = True; st.session_state.role = "Investigador"
                        st.session_state.user_id = "PI"; st.rerun()
                    else: st.error("❌ Contraseña denegada.")
    st.stop() 

# =====================================================================
# 🚪 BARRA LATERAL
# =====================================================================
st.sidebar.title("Plataforma DTx 🧬")
if st.session_state.role == "Investigador": st.sidebar.success("✅ Fisiólogo Clínico")
else: st.sidebar.info(f"👤 Sujeto: {st.session_state.user_id}"); st.sidebar.caption(f"Cohorte: {st.session_state.cohorte}")

st.sidebar.divider()
if st.sidebar.button("Cerrar Sesión 🔒", use_container_width=True, type="primary"):
    st.session_state.logged_in = False; st.session_state.role = None; st.session_state.user_id = None
    st.session_state.cohorte = None; st.session_state.grupo = None; st.rerun()

# =====================================================================
# 📱 UNIVERSO 1: PACIENTE
# =====================================================================
if st.session_state.role == "Paciente":
    col1, col_celular, col3 = st.columns([1, 2, 1])
    with col_celular:
        if st.session_state.grupo == "CONTROL":
            st.title("📓 Diario de Síntomas"); st.markdown("Tu reporte diario es vital para la investigación clínica.")
        else:
            st.title("☀️ Triage Matutino"); st.markdown("Tu reporte ajustará la dosis de tu sesión de entrenamiento de hoy.")
            
        st.divider()
        st.subheader("💤 1. Arquitectura del Sueño")
        c1, c2 = st.columns(2)
        with c1: hora_acostar = st.time_input("🛌 Hora acostarse", datetime.time(22, 30))
        with c2: hora_despertar = st.time_input("🌅 Hora despertarse", datetime.time(6, 30))
        c3, c4 = st.columns(2)
        with c3: latencia = st.number_input("⏱️ Min. hasta dormir:", 0, 180, 15, 5)
        with c4: despertares = st.number_input("🔄 Min. despierto:", 0, 240, 0, 5)

        dt_acostar = datetime.datetime.combine(datetime.date.today(), hora_acostar)
        dt_despertar = datetime.datetime.combine(datetime.date.today(), hora_despertar)
        if dt_despertar <= dt_acostar: dt_despertar += datetime.timedelta(days=1)
        t_cama = (dt_despertar - dt_acostar).total_seconds() / 60
        t_dormido = max(0, t_cama - latencia - despertares) 
        eficiencia = (t_dormido / t_cama) * 100 if t_cama > 0 else 0
        st.info(f"📊 Tiempo de sueño: **{t_dormido/60:.1f} hs netas**.")

        st.divider()
        st.subheader("🔋 2. Fatiga y Estrés")
        fatiga = st.select_slider("Fatiga física (0=Energía | 10=Agotamiento)", list(range(11)), 2)
        estres = st.select_slider("Estrés/Ansiedad (0=Paz | 10=Angustia)", list(range(11)), 2)
        
        st.divider()
        st.subheader("🦴 3. Dolor Corporal")
        col_img, col_zonas = st.columns([1, 1.5])
        with col_img:
            st.markdown("""<svg viewBox="0 0 100 200" xmlns="http://www.w3.org/2000/svg" style="max-height: 250px; display: block; margin: auto;"><circle cx="50" cy="25" r="14" fill="#e2e8f0" stroke="#94a3b8" stroke-width="2"/><path d="M 32 45 Q 50 40 68 45 L 62 100 L 38 100 Z" fill="#e2e8f0" stroke="#94a3b8" stroke-width="2"/><path d="M 32 45 Q 15 55 10 95" fill="none" stroke="#e2e8f0" stroke-width="10" stroke-linecap="round"/><path d="M 68 45 Q 85 55 90 95" fill="none" stroke="#e2e8f0" stroke-width="10" stroke-linecap="round"/><path d="M 42 100 L 35 175" fill="none" stroke="#e2e8f0" stroke-width="12" stroke-linecap="round"/><path d="M 58 100 L 65 175" fill="none" stroke="#e2e8f0" stroke-width="12" stroke-linecap="round"/><circle cx="32" cy="45" r="3.5" fill="#ef4444" /> <circle cx="68" cy="45" r="3.5" fill="#ef4444" /> <circle cx="50" cy="95" r="3.5" fill="#ef4444" /> <circle cx="38" cy="140" r="3.5" fill="#ef4444" /> <circle cx="62" cy="140" r="3.5" fill="#ef4444" /> </svg>""", unsafe_allow_html=True)
        with col_zonas:
            zonas_afectadas = st.multiselect("📍 Zonas afectadas:", ["Hombro Izq", "Hombro Der", "Lumbar", "Rodillas", "Neuropatía"])
            dolor_max = max([st.slider(f"Intensidad en {z}:", 1, 10, 5) for z in zonas_afectadas]) if zonas_afectadas else 0
        
        st.markdown("<br>", unsafe_allow_html=True)
        btn_txt = "Enviar Registro Diario 🚀" if st.session_state.grupo == "CONTROL" else "Enviar Reporte a Clínica 🚀"
        
        if st.button(btn_txt, use_container_width=True, type="primary"):
            datos_triage = {
                "id_paciente": st.session_state.user_id, "fecha": hoy_str, "estado_triage": "Completado", 
                "semaforo": calcular_semaforo(eficiencia, latencia, fatiga, estres, dolor_max), 
                "eficiencia_sueno": eficiencia, "latencia_min": latencia, "despertares_min": despertares, 
                "fatiga_bfi": fatiga, "estres_nccn": estres, "dolor_maximo": dolor_max, 
                "zonas_dolor": ", ".join(zonas_afectadas) if zonas_afectadas else "Ninguna"
            }
            with st.spinner("Transmitiendo..."):
                try:
                    existe = supabase.table("registros_diarios").select("id").eq("id_paciente", st.session_state.user_id).eq("fecha", hoy_str).execute()
                    if len(existe.data) > 0: supabase.table("registros_diarios").update(datos_triage).eq("id", existe.data[0]["id"]).execute()
                    else: supabase.table("registros_diarios").insert(datos_triage).execute()
                    
                    if st.session_state.grupo == "CONTROL": st.success("✅ ¡Registro guardado! Muchas gracias.")
                    else: st.success("✅ ¡Reporte guardado! Te esperamos para tu sesión.")
                except Exception as e: st.error(f"Error de conexión: {e}")

# =====================================================================
# 🔬 UNIVERSO 2: INVESTIGADOR
# =====================================================================
elif st.session_state.role == "Investigador":
    st.title("📡 Radar Clínico y Monitoreo RCT")
    
    # ⚠️ REEMPLAZA ESTE TEXTO CON EL LINK EXACTO DE TU APP EN STREAMLIT CLOUD:
    url_app = "https://plataforma-oncologia.streamlit.app" 
    
    try:
        res_pacientes = supabase.table("pacientes").select("*").execute()
        res_registros = supabase.table("registros_diarios").select("*").eq("fecha", hoy_str).execute()
        
        df_pacientes = pd.DataFrame(res_pacientes.data)
        if df_pacientes.empty: st.stop()
            
        if len(res_registros.data) > 0: df_radar = pd.merge(df_pacientes, pd.DataFrame(res_registros.data), on="id_paciente", how="left")
        else: df_radar = df_pacientes.copy(); df_radar[["estado_triage", "semaforo", "eficiencia_sueno", "fatiga_bfi", "dolor_maximo", "zonas_dolor", "estado_sesion"]] = None
                
        if 'grupo' not in df_radar.columns: df_radar['grupo'] = 'EXPERIMENTAL'
            
        df_mostrar = df_radar.rename(columns={"id_paciente": "ID", "grupo": "Brazo RCT", "cohorte": "Cohorte", "estado_triage": "Estado AM", "semaforo": "Semáforo", "eficiencia_sueno": "Eficiencia %", "fatiga_bfi": "Fatiga", "dolor_maximo": "Dolor"}).fillna({"Brazo RCT": "EXPERIMENTAL", "Estado AM": "Pendiente", "Semáforo": "⚪", "Eficiencia %": 0.0, "Fatiga": 0, "Dolor": 0})
        
        st.subheader("👥 Estado de las Cohortes (Hoy)")
        st.dataframe(df_mostrar[["ID", "Brazo RCT", "Cohorte", "Estado AM", "Semáforo", "Eficiencia %", "Fatiga", "Dolor"]].set_index("ID"), use_container_width=True)
        st.divider()
        
        if not df_radar.empty:
            paciente_sel = st.selectbox("📋 Seleccionar paciente para revisión:", df_radar["id_paciente"].tolist())
            datos_pac = df_radar[df_radar["id_paciente"] == paciente_sel].iloc[0]
            grupo_sel = str(datos_pac.get("grupo", "EXPERIMENTAL")).upper()
            
            # NUEVO: Agregamos la pestaña del QR
            tab_hoy, tab_historial, tab_qr = st.tabs(["📝 Cuaderno de Datos", "📈 Análisis Histórico", "📲 Enrolar Paciente (QR)"])
            
            with tab_qr:
                st.markdown("### 🖨️ Instalación de App en Celular del Paciente")
                st.write(f"Enlace oficial: `{url_app}`")
                
                # Generador de Código QR en tiempo real
                qr = qrcode.QRCode(version=1, box_size=8, border=2)
                qr.add_data(url_app)
                qr.make(fit=True)
                img_qr = qr.make_image(fill_color="black", back_color="white")
                
                buf = BytesIO()
                img_qr.save(buf, format="PNG")
                
                col_qr1, col_qr2 = st.columns([1, 2])
                with col_qr1:
                    st.image(buf, caption="Escanea con la cámara", use_container_width=True)
                with col_qr2:
                    st.info("**Paso 1:** Pídele al paciente que escanee este código con la cámara de su celular el Día 1 de familiarización.")
                    st.success("**Paso 2 (iPhone/Safari):** Tocar el botón compartir (cuadradito con flecha ⬆️ abajo) y seleccionar **'Agregar a Inicio'**.")
                    st.warning("**Paso 2 (Android/Chrome):** Tocar los 3 puntitos arriba a la derecha y seleccionar **'Instalar aplicación'** o **'Añadir a pantalla de inicio'**.")
                    st.markdown("💡 *Al hacerlo, la app se instalará en su teléfono con un ícono y se abrirá a pantalla completa (sin mostrar la barra de direcciones de internet).*")

            with tab_hoy:
                if datos_pac.get("estado_triage") in ["Pendiente", None]: st.warning("⚠️ El paciente aún no ha enviado su reporte.")
                else:
                    semaforo = str(datos_pac.get("semaforo", "⚪")); cohorte = str(datos_pac.get("cohorte", "MAMA"))
                    c_alerta1, c_alerta2 = st.columns(2)
                    if float(datos_pac.get("eficiencia_sueno", 100)) < 85.0: c_alerta1.warning(f"💤 Alerta Neural: Eficiencia {float(datos_pac.get('eficiencia_sueno', 0)):.1f}%.")
                    if float(datos_pac.get("dolor_maximo", 0)) > 0: c_alerta2.error(f"📍 Alerta Biomecánica: Dolor en {datos_pac.get('zonas_dolor', '')}.")
                    st.markdown("---")
                    
                    if grupo_sel == "CONTROL":
                        st.info("ℹ️ **GRUPO CONTROL: Monitoreo Activo**")
                        if st.button("Marcar Signos Vitales Revisados ✅", type="primary"):
                            supabase.table("registros_diarios").update({"estado_sesion": "Revisado (Control)", "ejercicio_1": "Ninguno", "kilos_ejercicio_1": 0.0, "ejercicio_2": "Ninguno", "kilos_ejercicio_2": 0.0, "rpe_sesion": 0}).eq("id_paciente", paciente_sel).eq("fecha", hoy_str).execute()
                            st.success("✅ Guardado en eCRF.")
                    else:
                        if "ROJO" in semaforo:
                            st.error("🚨 ZONA ROJA: Carga bloqueada.")
                            if st.button("Guardar Sesión Vagal 🫁"): supabase.table("registros_diarios").update({"estado_sesion": "Completado", "protocolo_vagal": True, "rpe_sesion": 0}).eq("id_paciente", paciente_sel).eq("fecha", hoy_str).execute(); st.success("Guardado.")
                        else:
                            if "AMARILLO" in semaforo: st.warning("⚠️ ZONA AMARILLA: -1 Serie, +2 RIR.")
                            else: st.success("✅ ZONA VERDE: Dosis 100%.")

                            c1, c2 = st.columns(2)
                            ej1 = "Prensa" if cohorte == "PROSTATA" else "Sentadilla Copa"; ej2 = "Press Máquina" if cohorte == "PROSTATA" else "Floor Press"
                            with c1: kilos1 = st.number_input(f"Kilos ({ej1}):", min_value=0.0, value=15.0, step=2.5)
                            with c2: kilos2 = st.number_input(f"Kilos ({ej2}):", min_value=0.0, value=10.0, step=2.5)
                            
                            if cohorte == "MAMA" and kilos2 > 25.0: st.error("🚨 Riesgo de Linfedema.")
                            else:
                                rpe = st.slider("RPE:", 0, 10, 6)
                                if st.button("Guardar Kilos en Nube 💾", type="primary"):
                                    supabase.table("registros_diarios").update({"estado_sesion": "Completado", "ejercicio_1": ej1, "kilos_ejercicio_1": float(kilos1), "ejercicio_2": ej2, "kilos_ejercicio_2": float(kilos2), "rpe_sesion": rpe}).eq("id_paciente", paciente_sel).eq("fecha", hoy_str).execute(); st.success("✅ Sincronizado.")

            with tab_historial:
                res_hist = supabase.table("registros_diarios").select("fecha, fatiga_bfi, dolor_maximo, eficiencia_sueno, kilos_ejercicio_1, rpe_sesion").eq("id_paciente", paciente_sel).order("fecha").execute()
                if len(res_hist.data) > 1:
                    df_hist = pd.DataFrame(res_hist.data); df_hist["fecha"] = pd.to_datetime(df_hist["fecha"]).dt.strftime('%d-%m'); df_hist.set_index("fecha", inplace=True); df_hist.fillna(0, inplace=True)
                    c_g1, c_g2 = st.columns(2)
                    with c_g1: st.line_chart(df_hist[["fatiga_bfi", "dolor_maximo"]], color=["#ff4b4b", "#ffa500"])
                    with c_g2: st.line_chart(df_hist[["eficiencia_sueno"]], color=["#1f77b4"])
                    if grupo_sel != "CONTROL": st.line_chart(df_hist[["kilos_ejercicio_1", "rpe_sesion"]], color=["#2ca02c", "#9467bd"])
                else: st.info("Datos insuficientes.")
                            
    except Exception as e: st.error(f"Error interno: {e}")