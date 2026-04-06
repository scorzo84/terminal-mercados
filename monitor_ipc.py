import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
import base64
from io import BytesIO

# 1. Configuración Global de la App
st.set_page_config(
    page_title="CorzoNow - Terminal Inteligente", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS PROFESIONALES ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stTable { font-size: 14px; width: 100%; }
    .footer-credits { text-align: center; color: #94a3b8; font-size: 12px; margin-top: 30px; font-style: italic; }
    .st-emotion-cache-1kyxreq { justify-content: center; }
    </style>
    """, unsafe_allow_html=True)

# --- MOTOR DE ANÁLISIS TÉCNICO (CONTEXTUAL) ---
def analizar_activo(df, estrategia):
    """Aplica triple filtro: EMA (Tendencia), RSI (Agotamiento) y MACD (Fuerza)"""
    if df is None or len(df) < 35: return "⏳ DATA INSUF."
    
    # Parámetros ajustados por temporalidad
    configs = {
        "Day-Trading": {"ema_f": 9, "ema_s": 21, "rsi_max": 68, "rsi_min": 45},
        "Swing-Traiding": {"ema_f": 20, "ema_s": 50, "rsi_max": 62, "rsi_min": 40},
        "Position-Trading": {"ema_f": 50, "ema_s": 200, "rsi_max": 58, "rsi_min": 35}
    }
    c = configs.get(estrategia, configs["Swing-Traiding"])

    # Cálculos Técnicos
    df['EMA_F'] = ta.ema(df['Close'], length=c['ema_f'])
    df['EMA_S'] = ta.ema(df['Close'], length=c['ema_s'])
    df['RSI'] = ta.rsi(df['Close'], length=14)
    macd = ta.macd(df['Close'])
    
    # Verificación de que MACD se calculó correctamente
    if macd is not None and not macd.empty:
        df['MACD'] = macd.iloc[:, 0]
        df['MACD_S'] = macd.iloc[:, 2]
    else:
        return "⚠️ ERROR IND."

    u = df.iloc[-1]
    
    # LÓGICA DE TRIPLE CONFIRMACIÓN
    cond_tendencia = u['Close'] > u['EMA_F'] > u['EMA_S']
    cond_momento = u['MACD'] > u['MACD_S']
    cond_rsi = c['rsi_min'] < u['RSI'] < c['rsi_max']

    if cond_tendencia and cond_momento and cond_rsi:
        return "✅ COMPRA"
    elif cond_tendencia or cond_momento:
        return "🟡 NEUTRAL"
    else:
        return "❌ ESPERA"

# --- SIDEBAR: CONTROL Y SEGURIDAD ---
with st.sidebar:
    st.markdown("## 🕹️ Panel de Control")
    mercado_sel = st.selectbox("🌐 Seleccionar Mercado", ["🇲🇽 México (IPC)", "🇺🇸 EE.UU. (Wall Street)", "🚀 Cripto (USD)"])
    estrategia_sel = st.selectbox("📈 Estrategia", ["Day-Trading", "Swing-Traiding", "Position-Trading"])
    
    st.markdown("---")
    st.markdown("### 🔑 Acceso Premium")
    codigo_input = st.text_input("Código de acceso:", type="password")
    
    try: CODIGO_MAESTRO = st.secrets["PASSWORD_PREMIUM"]
    except: CODIGO_MAESTRO = "CORZO2026"
    
    es_premium = (codigo_input == CODIGO_MAESTRO)

# --- BASE DE DATOS DE ACTIVOS ---
listas_mercados = {
    "🇲🇽 México (IPC)": ["AMXB.MX", "WALMEX.MX", "GFNORTEO.MX", "GMEXICOB.MX", "FEMSAUBD.MX", "CEMEXCPO.MX", "GAPB.MX", "ASURB.MX", "AC.MX", "BIMBOA.MX"],
    "🇺🇸 EE.UU. (Wall Street)": ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "AVGO", "COST", "NFLX"],
    "🚀 Cripto (USD)": ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD", "DOGE-USD", "TRX-USD", "AVAX-USD", "DOT-USD"]
}

tickers = listas_mercados.get(mercado_sel, [])

# --- RENDERIZADO PRINCIPAL ---
st.title(f"CorzoNow: {mercado_sel}")

if mercado_sel != "🇲🇽 México (IPC)" and not es_premium:
    st.error("🔒 Mercado Protegido. Se requiere cuenta Premium.")
    st.link_button("🚀 ACTIVAR ACCESO PREMIUM ($349 MXN)", "https://paypal.me", type="primary")
    st.info("📧 Envía tu comprobante a scorzo84@hotmail.com")
else:
    with st.spinner("Analizando mercados en tiempo real..."):
        # Configuración de descarga según estrategia
        intervalo = "15m" if estrategia_sel == "Day-Trading" else "1d" if estrategia_sel == "Swing-Traiding" else "1wk"
        periodo_dl = "1mo" if estrategia_sel == "Day-Trading" else "2y"

        # Descarga de datos masiva
        try:
            datos = yf.download(tickers, period=periodo_dl, interval=intervalo, group_by='ticker', progress=False)
        except Exception as e:
            st.error(f"Error de conexión con el mercado: {e}")
            st.stop()

        res = []
        for t in tickers:
            try:
                # Manejo de estructura de datos de yfinance (MultiIndex vs Single)
                df_t = datos[t].dropna() if len(tickers) > 1 else datos.dropna()
                
                if df_t.empty or len(df_t) < 5: continue
                
                señal = analizar_activo(df_t, estrategia_sel)
                u = df_t.iloc[-1]
                a = df_t.iloc[-2]
                rsi_val = df_t['RSI'].iloc[-1] if 'RSI' in df_t.columns else 0
                cambio = ((u['Close'] - a['Close']) / a['Close']) * 100
                
                res.append({
                    "Ticker": t,
                    "Precio": f"{u['Close']:,.2f}",
                    "RSI": f"{rsi_val:.1f}",
                    "Hoy %": f"{cambio:+.2f}%",
                    "Señal": señal
                })
            except: continue

        # --- TABLA DE RESULTADOS CON CORRECCIÓN DE ERROR ---
        df_final = pd.DataFrame(res)
        
        if not df_final.empty:
            def aplicar_estilo(val):
                color = '#22c55e' if '✅' in val else '#ef4444' if '❌' in val else '#f59e0b'
                return f'color: {color}; font-weight: bold'

            try:
                # Corrección para versiones nuevas de Pandas (map en lugar de applymap)
                st.table(df_final.style.map(aplicar_estilo, subset=['Señal']))
            except AttributeError:
                st.table(df_final.style.applymap(aplicar_estilo, subset=['Señal']))
        else:
            st.warning("No hay datos disponibles para mostrar en este momento.")

        # --- SECCIÓN GRÁFICA ---
        st.markdown("---")
        col_g1, col_g2 = st.columns([1, 2])
        
        with col_g1:
            t_ver = st.selectbox("Seleccionar activo para gráfico:", tickers)
            if st.button("Descargar Reporte Excel"):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_final.to_excel(writer, index=False)
                st.download_button("Click para Guardar", output.getvalue(), "Reporte_CorzoNow.xlsx")

        with col_g2:
            try:
                df_plot = datos[t_ver].dropna() if len(tickers) > 1 else datos.dropna()
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['Close'], name="Precio", line=dict(color='#1E3A8A')))
                fig.update_layout(template="plotly_white", height=350, margin=dict(l=0,r=0,t=30,b=0), title=f"Histórico: {t_ver}")
                st.plotly_chart(fig, use_container_width=True)
            except: st.info("Selecciona un activo para visualizar.")

st.markdown('<div class="footer-credits">Desarrollado por Corzo Tech © 2026</div>', unsafe_allow_html=True)


