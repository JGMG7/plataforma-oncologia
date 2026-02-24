import streamlit as st
import datetime
import pytz
import pandas as pd
from supabase import create_client, Client
import streamlit.components.v1 as components
import qrcode
from io import BytesIO

st.set_page_config(page_title="DTx ISEF-CURE-UDELAR", page_icon="🧬", layout="wide")

# =====================================================================
# ⚙️ INYECCIÓN PWA Y ZONA HORARIA
# =====================================================================
st.markdown("""<style>#MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;} body { overscroll-behavior-y: contain; }</style>""", unsafe_allow_html=True)
components.html("""<script>var head = window.parent.document.querySelector("head"); if (!head.querySelector('meta[name="apple-mobile-web-app-capable"]')) {var m1 = window.parent.document.createElement('meta'); m1.name = "apple-mobile-web-app-capable"; m1.content = "yes"; head.appendChild(m1); var m2 = window.parent.document.createElement('meta'); m2.name = "apple-mobile-web-app-status-bar-style"; m2.content = "black-translucent"; head.appendChild(m2);}</script>""", height=0, width=0)

# Reloj Oficial Udelar (Uruguay)
zona_horaria = pytz.timezone('America/Montevideo')
fecha_hoy_uy = datetime.datetime.now(zona_horaria).date()
hoy_str = str(fecha_hoy_uy)
dia_semana = fecha_hoy_uy.weekday() # 0=Lunes, 1=Martes, 2=Miércoles, 3=Jueves, 4=Viernes, 5=Sábado, 6=Domingo
nombres_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# --- CONEXIÓN A LA NUBE ---
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

try: supabase: Client = init_connection()
except Exception as e: st.error(f"Error de red: {e}"); st.stop()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None; st.session_state.user_id = None
    st.session_state.cohorte = None; st.session_state.grupo = None

# =====================================================================
# 📚 MOTOR CIENTÍFICO (RUTINAS Y REGLAS)
# =====================================================================
def calcular_semaforo(eficiencia, latencia, fatiga, estres, dolor_max):
    if fatiga >= 8 or dolor_max >= 7: return "🔴 ROJO"
    elif eficiencia < 85.0 or latencia > 45 or fatiga >= 5 or estres >= 6: return "🟡 AMARILLO"
    else: return "🟢 VERDE"

def obtener_rutina(cohorte, dia_semana):
    if cohorte == "MAMA":
        if dia_semana == 0: return ["Sentadilla Copa (Goblet)", "Remo c/ Mancuerna", "Puente de Glúteos", "Plancha Frontal"]
        elif dia_semana == 2: return ["Prensa Piernas 45°", "Floor Press (Seguro)", "Peso Muerto Rumano", "Pallof Press"]
        elif dia_semana == 4: return ["Estocadas (Lunges)", "Jalón al Pecho (Polea)", "Extensión Cuádriceps", "Bird-Dog"]
    else: # PROSTATA
        if dia_semana == 0: return ["Prensa Piernas 45°", "Press Pecho (Máquina)", "Remo Sentado", "Elevación Talones"]
        elif dia_semana == 2: return ["Peso Muerto Hexagonal / RDL", "Press Militar Sentado", "Jalón al Pecho", "Caminata de Granjero"]
        elif dia_semana == 4: return ["Sentadilla Búlgara", "Flexiones / Inclinado", "Remo en TRX / 1 Brazo", "Suelo Pélvico (Kegel)"]
    return ["Descanso", "Descanso", "Descanso", "Descanso"]

def obtener_intensidad(dia_semana):
    if dia_semana == 0: return "65% (LUNES - Carga Base)"
    elif dia_semana == 2: return "75% (MIÉRCOLES - Día Pesado)"
    elif dia_semana == 4: return "55% (VIERNES - Día Regenerativo)"
    return "Monitoreo Pasivo"

# =====================================================================
# 🔐 PANTALLA DE LOGIN
# =====================================================================
if not st.session_state.logged_in:
    col_izq, col_login, col_der = st.columns([1, 2, 1])
    with col_login:
        st.markdown("<h2 style='text-align: center;'>🧬 DTx Udelar</h2>", unsafe_allow_html=True)
        tab_paciente, tab_investigador = st.tabs(["📱 Pacientes", "🔬 Equipo Clínico"])
        with tab_paciente:
            with st.form("login_pac"):
                user_input = st.text_input("ID de Paciente").strip().upper()
                pin_input = st.text_input("PIN Secreto", type="password")
                if st.form_submit_button("Ingresar 🚀", use_container_width=True, type="primary"):
                    res = supabase.table("pacientes").select("*").eq("id_paciente", user_input).execute()
                    if len(res.data) > 0 and str(res.data[0].get("pin")) == pin_input:
                        st.session_state.logged_in = True; st.session_state.role = "Paciente"
                        st.session_state.user_id = res.data[0]["id_paciente"]; st.session_state.cohorte = res.data[0]["cohorte"]
                        st.session_state.grupo = res.data[0].get("grupo") or "EXPERIMENTAL"; st.rerun()
                    else: st.error("❌ Error en credenciales.")
        with tab_investigador:
            with st.form("login_inv"):
                pass_input = st.text_input("Contraseña Maestra", type="password")
                if st.form_submit_button("Desbloquear Radar 🔐", use_container_width=True, type="primary"):
                    if pass_input == st.secrets.get("INVESTIGADOR_PASSWORD", "Udelar2026"):
                        st.session_state.logged_in = True; st.session_state.role = "Investigador"; st.session_state.user_id = "PI"; st.rerun()
                    else: st.error("❌ Contraseña denegada.")
    st.stop() 

st.sidebar.title("DTx ISEF-CURE-UDELAR 🧬")
if st.session_state.role == "Investigador": st.sidebar.success(f"✅ Panel Clínico\n📅 {nombres_dias[dia_semana]}, {hoy_str}")
else: st.sidebar.info(f"👤 {st.session_state.user_id}"); st.sidebar.caption(f"📅 Fecha: {hoy_str}")
st.sidebar.divider()
if st.sidebar.button("Cerrar Sesión 🔒", use_container_width=True, type="primary"): st.session_state.clear(); st.rerun()

# =====================================================================
# 📱 UNIVERSO 1: PACIENTE (MONITOREO CONTINUO L-D)
# =====================================================================
if st.session_state.role == "Paciente":
    col1, col_celular, col3 = st.columns([1, 2, 1])
    with col_celular:
        st.markdown(f"**📅 Hoy es {nombres_dias[dia_semana]}, {fecha_hoy_uy.strftime('%d/%m/%Y')}**")
        
        if st.session_state.grupo == "CONTROL":
            st.title("📓 Diario de Síntomas"); st.markdown("Tu reporte diario es vital para comprender la evolución del tratamiento.")
        else:
            st.title("☀️ Triage Matutino")
            if dia_semana in [0, 2, 4]: st.markdown("Tu reporte ajustará la dosis de tu **sesión de entrenamiento de hoy**.")
            else: st.markdown("Hoy es día de **recuperación**. Tu reporte nos ayuda a monitorear tu descanso.")
            
        st.divider()
        
        st.subheader("💤 1. Arquitectura del Sueño")
        c1, c2 = st.columns(2)
        with c1: hora_acostar = st.time_input("🛌 Hora acostarse", datetime.time(22, 30))
        with c2: hora_despertar = st.time_input("🌅 Hora despertarse", datetime.time(6, 30))
        c3, c4 = st.columns(2)
        with c3: latencia = st.number_input("⏱️ Min. hasta dormir:", 0, 180, 15, 5)
        with c4: despertares = st.number_input("🔄 Min. despierto:", 0, 240, 0, 5)

        dt_acostar = datetime.datetime.combine(fecha_hoy_uy, hora_acostar)
        dt_despertar = datetime.datetime.combine(fecha_hoy_uy, hora_despertar)
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
        zonas_afectadas = st.multiselect("📍 Zonas afectadas:", ["Hombro Izq", "Hombro Der", "Lumbar", "Rodillas", "Neuropatía"])
        dolor_max = 0
        if zonas_afectadas:
            dolor_max = max([st.slider(f"Intensidad en {z}:", 1, 10, 5) for z in zonas_afectadas])
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        btn_txt = "Enviar Registro Diario 🚀" if st.session_state.grupo == "CONTROL" else "Enviar Reporte 🚀"
        
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
                    
                    if st.session_state.grupo == "CONTROL": st.success("✅ ¡Registro guardado! Muchas gracias por tu compromiso.")
                    else:
                        if dia_semana in [0, 2, 4]: st.success("✅ ¡Reporte guardado! Te esperamos hoy para tu sesión de entrenamiento.")
                        else: st.success("✅ ¡Reporte guardado! Excelente trabajo monitoreando tu recuperación de hoy.")
                except Exception as e: st.error(f"Error de conexión: {e}")

# =====================================================================
# 🔬 UNIVERSO 2: INVESTIGADOR (RCT, SOP Y DOSIFICACIÓN L-M-V)
# =====================================================================
elif st.session_state.role == "Investigador":
    st.title("📡 Quirófano Clínico (Producción V2.0)")
    
    # ⚠️ RECUERDA PONER TU ENLACE REAL DE STREAMLIT AQUÍ
    url_app = "https://plataforma-oncologia-4zktoxiwtebukcvht57msb.streamlit.app/?embed=true" 

    try:
        res_pacientes = supabase.table("pacientes").select("*").execute()
        res_registros = supabase.table("registros_diarios").select("*").eq("fecha", hoy_str).execute()
        
        df_pacientes = pd.DataFrame(res_pacientes.data)
        if df_pacientes.empty: st.stop()
            
        if len(res_registros.data) > 0: df_radar = pd.merge(df_pacientes, pd.DataFrame(res_registros.data), on="id_paciente", how="left")
        else: df_radar = df_pacientes.copy(); df_radar[["estado_triage", "semaforo", "eficiencia_sueno", "fatiga_bfi", "dolor_maximo", "zonas_dolor", "estado_sesion"]] = None
                
        if 'grupo' not in df_radar.columns: df_radar['grupo'] = 'EXPERIMENTAL'
        if 'fecha_inicio' not in df_radar.columns: df_radar['fecha_inicio'] = None
            
        df_mostrar = df_radar.rename(columns={
            "id_paciente": "ID Paciente", "grupo": "Brazo", "cohorte": "Cohorte", "estado_triage": "Estado AM",
            "semaforo": "Semáforo", "eficiencia_sueno": "Eficiencia %", "fatiga_bfi": "Fatiga", "dolor_maximo": "Dolor"
        }).fillna({"Brazo": "EXPERIMENTAL", "Estado AM": "Pendiente", "Semáforo": "⚪", "Eficiencia %": 0.0, "Fatiga": 0, "Dolor": 0})
        
        st.subheader("👥 Estado de las Cohortes (Hoy)")
        st.dataframe(df_mostrar[["ID Paciente", "Brazo", "Cohorte", "Estado AM", "Semáforo", "Eficiencia %", "Fatiga", "Dolor"]].set_index("ID Paciente"), use_container_width=True)
        st.divider()
        
        if not df_radar.empty:
            paciente_sel = st.selectbox("📋 Seleccionar paciente para la sesión:", df_radar["id_paciente"].tolist())
            datos_pac = df_radar[df_radar["id_paciente"] == paciente_sel].iloc[0]
            grupo_sel = str(datos_pac.get("grupo", "EXPERIMENTAL")).upper()
            cohorte_sel = str(datos_pac.get("cohorte", "MAMA")).upper()
            
            tab_hoy, tab_admin, tab_qr = st.tabs(["📝 Cuaderno de Sesión", "⚙️ Configuración & Histórico", "📲 Enrolar Paciente (QR)"])
            
            # --- CÁLCULO DE SEMANA (ROLLING ADMISSION) ---
            f_inicio = datos_pac.get("fecha_inicio")
            if pd.isna(f_inicio) or f_inicio is None:
                semana_actual = "Paciente NO ENROLADO"
                dias_trans = -1
            else:
                dias_trans = (fecha_hoy_uy - pd.to_datetime(f_inicio).date()).days
                semana_actual = f"Semana {(dias_trans // 7) + 1}" if dias_trans >= 0 else "Inicia en el futuro"
            
            with tab_admin:
                st.markdown("### ⚙️ Panel de Enrolamiento (Rolling Admission)")
                if pd.isna(f_inicio) or f_inicio is None:
                    st.warning("⚠️ Este paciente aún no ha iniciado la Semana 1 del ensayo clínico.")
                    if st.button(f"🔴 Fijar HOY ({hoy_str}) como INICIO SEMANA 1", type="primary"):
                        supabase.table("pacientes").update({"fecha_inicio": hoy_str}).eq("id_paciente", paciente_sel).execute()
                        st.success("✅ Fecha de inicio registrada. Por favor, selecciona otro paciente y vuelve a este para recargar.")
                else:
                    st.info(f"✅ El paciente inició el estudio el **{f_inicio}**.")
                    st.success(f"🚀 **Actualmente cursando la {semana_actual} del ensayo.**")
                    
                st.divider()
                st.markdown(f"### 📈 Evolución Biomédica: `{paciente_sel}`")
                res_hist = supabase.table("registros_diarios").select("fecha, fatiga_bfi, dolor_maximo, eficiencia_sueno, kilos_ejercicio_1, rpe_sesion").eq("id_paciente", paciente_sel).order("fecha").execute()
                if len(res_hist.data) > 1:
                    df_hist = pd.DataFrame(res_hist.data); df_hist["fecha"] = pd.to_datetime(df_hist["fecha"]).dt.strftime('%d-%m'); df_hist.set_index("fecha", inplace=True); df_hist.fillna(0, inplace=True)
                    c_g1, c_g2 = st.columns(2)
                    with c_g1: st.line_chart(df_hist[["fatiga_bfi", "dolor_maximo"]], color=["#ff4b4b", "#ffa500"])
                    with c_g2: st.line_chart(df_hist[["eficiencia_sueno"]], color=["#1f77b4"])
                    if grupo_sel != "CONTROL": st.line_chart(df_hist[["kilos_ejercicio_1", "rpe_sesion"]], color=["#2ca02c", "#9467bd"])
                else: st.info("Aún no hay datos históricos suficientes.")

            with tab_qr:
                st.markdown("### 🖨️ Instalación de App en Celular del Paciente")
                qr = qrcode.QRCode(version=1, box_size=8, border=2); qr.add_data(url_app); qr.make(fit=True)
                img_qr = qr.make_image(fill_color="black", back_color="white"); buf = BytesIO(); img_qr.save(buf, format="PNG")
                col_qr1, col_qr2 = st.columns([1, 2])
                with col_qr1: st.image(buf, caption="Escanea con la cámara", use_container_width=True)
                with col_qr2: st.write("Pídele al paciente que escanee este código en su primera visita de familiarización para instalar la App.")

            with tab_hoy:
                if datos_pac.get("estado_triage") in ["Pendiente", None]:
                    st.warning("⚠️ El paciente aún no ha enviado su reporte diario.")
                else:
                    semaforo = str(datos_pac.get("semaforo", "⚪"))
                    st.markdown(f"**Sujeto:** `{paciente_sel}` | **Fase:** `{semana_actual}` | **Condición AM:** {semaforo}")
                    c_alerta1, c_alerta2 = st.columns(2)
                    if float(datos_pac.get("eficiencia_sueno", 100)) < 85.0: c_alerta1.warning(f"💤 Alerta Neural: Eficiencia del sueño en {float(datos_pac.get('eficiencia_sueno', 0)):.1f}%.")
                    if float(datos_pac.get("dolor_maximo", 0)) > 0: c_alerta2.error(f"📍 Alerta Biomecánica: Foco de dolor en {datos_pac.get('zonas_dolor', '')}.")
                    st.markdown("---")
                    
                    if grupo_sel == "CONTROL":
                        st.info("ℹ️ **GRUPO CONTROL: Monitoreo Activo (Usual Care)**")
                        if st.button("Marcar Signos Vitales Revisados ✅", type="primary"):
                            supabase.table("registros_diarios").update({
                                "estado_sesion": "Revisado (Control)", "ejercicio_1": "Ninguno", "kilos_ejercicio_1": 0.0, "ejercicio_2": "Ninguno", "kilos_ejercicio_2": 0.0, "ejercicio_3": "Ninguno", "kilos_ejercicio_3": 0.0, "ejercicio_4": "Ninguno", "kilos_ejercicio_4": 0.0, "rpe_sesion": 0
                            }).eq("id_paciente", paciente_sel).eq("fecha", hoy_str).execute()
                            st.success("✅ Registro de monitorización guardado en el eCRF.")
                            
                    else:
                        # VALIDACIÓN DE DÍAS (SOLO L-M-V PRESCRIPCIÓN)
                        if dia_semana not in [0, 2, 4]:
                            st.info("🛋️ **DÍA DE RECUPERACIÓN PASIVA.**")
                            st.markdown("Hoy no corresponde sesión de entrenamiento de fuerza. El sistema ha registrado el reporte matutino del paciente para el análisis de recuperación longitudinal.")
                        else:
                            intensidad_hoy = obtener_intensidad(dia_semana)
                            st.subheader(f"🎯 Periodización del Día: {intensidad_hoy}")
                            
                            # 👨‍🏫 DIRECTRICES PARA EL PROFESOR (SOPs)
                            with st.expander("📖 **VER DIRECTRICES DE LA SESIÓN (SOP)**", expanded=True):
                                st.markdown("""
                                **Directrices Generales (Obligatorias):**
                                * 🏃 **Entrada en calor:** 5-10 min aeróbico ligero + Movilidad articular dinámica de todo el cuerpo.
                                * ⏱️ **Pausas:** **2 minutos estrictos** entre series de fuerza.
                                * ❤️ **Monitoreo FC:** Tomar Frecuencia Cardíaca en cuello/muñeca durante 15 segundos y multiplicar x4.
                                * 🎛️ **Cadencia:** Controlada (**2-0-2-0**), 2s excéntrica bajando, sin pausa, 2s concéntrica empujando.
                                """)
                                
                                if "VERDE" in semaforo:
                                    st.success("**🟢 ZONA VERDE (Homeostasis):**\n* Dosis Completa. Realizar todas las Series por ejercicio.\n* **Exigencia:** RIR 2-3 (Dejar 2 a 3 repeticiones en recámara).")
                                elif "AMARILLO" in semaforo:
                                    st.warning("**🟡 ZONA AMARILLA (Down-Regulation):**\n* Reducir Volumen: **-1 Serie** por ejercicio.\n* Mayor margen de seguridad: **RIR 4** (Terminar muy lejos del fallo muscular).")
                                elif "ROJO" in semaforo:
                                    st.error("""
                                    **🔴 ZONA ROJA (Toxicidad Aguda):** CARGA BLOQUEADA.
                                    * **Paso 1:** Posicionar al paciente en decúbito supino cómodo o posición sedente segura.
                                    * **Paso 2 (Protocolo Vagal):** Iniciar respiración **4-7-8** (Inhala por la nariz en 4s, retiene 7s, exhala por la boca en 8s).
                                    * **Paso 3:** Mantener por 10 a 15 minutos en ambiente tranquilo.
                                    * **Paso 4:** Monitorear reducción de FC y consultar estado de bienestar general.
                                    """)
                            
                            if "ROJO" in semaforo:
                                if st.button("Guardar Ejecución Protocolo Vagal 🫁"):
                                    supabase.table("registros_diarios").update({
                                        "estado_sesion": "Vagal Completado", "protocolo_vagal": True, "rpe_sesion": 0,
                                        "ejercicio_1": "Protocolo Vagal", "kilos_ejercicio_1": 0, "ejercicio_2": "Ninguno", "kilos_ejercicio_2": 0, "ejercicio_3": "Ninguno", "kilos_ejercicio_3": 0, "ejercicio_4": "Ninguno", "kilos_ejercicio_4": 0
                                    }).eq("id_paciente", paciente_sel).eq("fecha", hoy_str).execute()
                                    st.success("Guardado.")
                            else:
                                if dias_trans < 0:
                                    st.warning("El paciente inicia el protocolo en el futuro. No se pueden registrar cargas hoy.")
                                else:
                                    st.markdown("#### 🏋️‍♂️ Registro de Cargas Reales (Kg)")
                                    rutina = obtener_rutina(cohorte_sel, dia_semana)
                                    
                                    c1, c2 = st.columns(2)
                                    with c1:
                                        k1 = st.number_input(f"1. {rutina[0]}:", min_value=0.0, step=2.5)
                                        k3 = st.number_input(f"3. {rutina[2]}:", min_value=0.0, step=2.5)
                                    with c2:
                                        k2 = st.number_input(f"2. {rutina[1]}:", min_value=0.0, step=2.5)
                                        k4 = st.number_input(f"4. {rutina[3]}:", min_value=0.0, step=2.5)
                                        
                                    if cohorte_sel == "MAMA" and ("Press" in rutina[1] or "Elevaciones" in rutina[1]) and k2 > 25.0:
                                        st.error("🚨 **ALERTA CLÍNICA:** La carga en tren superior podría presentar riesgo de Linfedema. Verifique.")
                                    
                                    rpe = st.slider("Escala de Borg CR10 (Carga Interna de la Sesión Completa):", 0, 10, 6)
                                    
                                    if st.button("Guardar Sesión L-M-V 💾", type="primary"):
                                        try:
                                            datos_sesion = {
                                                "estado_sesion": "Completado", "rpe_sesion": rpe,
                                                "ejercicio_1": rutina[0], "kilos_ejercicio_1": float(k1),
                                                "ejercicio_2": rutina[1], "kilos_ejercicio_2": float(k2),
                                                "ejercicio_3": rutina[2], "kilos_ejercicio_3": float(k3),
                                                "ejercicio_4": rutina[3], "kilos_ejercicio_4": float(k4)
                                            }
                                            supabase.table("registros_diarios").update(datos_sesion).eq("id_paciente", paciente_sel).eq("fecha", hoy_str).execute()
                                            st.success("✅ ¡Datos del microciclo sincronizados con éxito (Tidy Data listo para publicación)!")
                                        except Exception as e:
                                            st.error(f"Error al guardar: {e}. Asegúrate de haber agregado las columnas ejercicio_3 y ejercicio_4 en SQL.")
                            

    except Exception as e: st.error(f"Error de sistema: {e}")

