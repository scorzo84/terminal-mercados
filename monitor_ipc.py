import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
import base64
from io import BytesIO

# 1. Configuración Global
st.set_page_config(page_title="CorzoNow - Terminal Inteligente", layout="wide")

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .reportview-container .main .block-container { padding-top: 1rem; }
    .stTable { font-size: 14px; }
    .footer { text-align: center; color: #94a3b8; font-size: 12px; margin-top: 30px; }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA TÉCNICA ROBUSTA (ANTIFALSOS) ---
def analizar_activo(df, estrategia):
    if df is None or len(df) < 50: return "⏳ DATA INSUF."
    
    # Configuración por Estrategia
    configs = {
        "Day-Trading": {"ema_f": 9, "ema_s": 21, "rsi_max": 68, "rsi_min": 45},
        "Swing-Traiding": {"ema_f": 20, "ema_s": 50, "rsi_max": 62, "rsi_min": 40},
        "Position-Trading": {"ema_f": 50, "ema_s": 200, "rsi_max": 58, "rsi_min": 35}
    }
    c = configs[estrategia]

    # Cálculo de Indicadores
    df['EMA_F'] = ta.ema(df['Close'], length=c['ema_f'])
    df['EMA_S'] = ta.ema(df['Close'], length=c['ema_s'])
    df['RSI'] = ta.rsi(df['Close'], length=14)
    macd = ta.macd(df['Close'])
    df['MACD'] = macd.iloc[:, 0]
    df['MACD_S'] = macd.iloc[:, 2]

    u = df.iloc[-1]
    
    # TRIPLE FILTRO
    cond_tendencia = u['Close'] > u['EMA_F'] > u['EMA_S']
    cond_momento = u['MACD'] > u['MACD_S']
    cond_rsi = c['rsi_min'] < u['RSI'] < c['rsi_max']

    if cond_tendencia and cond_momento and cond_rsi:
        return "✅ COMPRA"
    elif cond_tendencia or cond_momento:
        return "🟡 NEUTRAL"
    else:
        return "❌ ESPERA"

# --- SIDEBAR Y CONFIGURACIÓN ---
with st.sidebar:
    st.header("🕹️ Panel de Control")
    mercado_sel = st.selectbox("🌐 Mercado", ["🇲🇽 México (IPC)", "🇺🇸 EE.UU. (Wall Street)", "🚀 Cripto (USD)"])
    estrategia_sel = st.selectbox("📈 Estrategia", ["Day-Trading", "Swing-Traiding", "Position-Trading"])
    
    st.markdown("---")
    codigo_input = st.text_input("🔑 Código Premium", type="password")
    
    # Seguridad
    try: CODIGO_MAESTRO = st.secrets["PASSWORD_PREMIUM"]
    except: CODIGO_MAESTRO = "CORZO2026"
    es_premium = (codigo_input == CODIGO_MAESTRO)

# --- DEFINICIÓN DE TICKERS (Solución al NameError) ---
listas_mercados = {
    "🇲🇽 México (IPC)": ["AMXB.MX", "WALMEX.MX", "GFNORTEO.MX", "GMEXICOB.MX", "FEMSAUBD.MX", "CEMEXCPO.MX", "GAPB.MX", "ASURB.MX", "AC.MX", "BIMBOA.MX"],
    "🇺🇸 EE.UU. (Wall Street)": ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "AVGO", "COST", "NFLX"],
    "🚀 Cripto (USD)": ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD", "DOGE-USD", "TRX-USD", "AVAX-USD", "DOT-USD"]
}

# Selección de tickers según el mercado elegido
tickers = listas_mercados.get(mercado_sel, [])

# --- RENDERIZADO PRINCIPAL ---
st.title(f"Terminal Inteligente: {mercado_sel}")

# Muro de pago para mercados internacionales
if mercado_sel != "🇲🇽 México (IPC)" and not es_premium:
    st.error("🔒 Contenido exclusivo para miembros Premium.")
    st.info("Envía tu comprobante a scorzo84@hotmail.com para desbloquear.")
else:
    with st.spinner("Analizando mercados en tiempo real..."):
        # Ajuste de temporalidad según estrategia
        intervalo = "15m" if estrategia_sel == "Day-Trading" else "1d" if estrategia_sel == "Swing-Traiding" else "1wk"
        periodo_dl = "1mo" if estrategia_sel == "Day-Trading" else "2y"

        # Descarga de datos
        datos = yf.download(tickers, period=periodo_dl, interval=intervalo, group_by='ticker', progress=False)

        res = []
        for t in tickers:
            try:
                df_t = datos[t].dropna()
                if df_t.empty: continue
                
                señal = analizar_activo(df_t, estrategia_sel)
                u = df_t.iloc[-1]
                rsi_val = df_t['RSI'].iloc[-1]
                cambio = ((u['Close'] - df_t['Close'].iloc[-2]) / df_t['Close'].iloc[-2]) * 100
                
                res.append({
                    "Ticker": t,
                    "Precio": f"{u['Close']:,.2f}",
                    "RSI": f"{rsi_val:.1f}",
                    "Hoy %": f"{cambio:+.2f}%",
                    "Señal": señal
                })
            except: continue

        # Mostrar tabla de resultados
        df_final = pd.DataFrame(res)
        
        def color_señal(val):
            if '✅' in val: color = '#22c55e'
            elif '❌' in val: color = '#ef4444'
            else: color = '#f59e0b'
            return f'color: {color}; font-weight: bold'

        st.table(df_final.style.applymap(color_señal, subset=['Señal']))

        # Gráfico dinámico del primer ticker o selección
        st.markdown("---")
        t_ver = st.selectbox("Ver gráfico detallado:", tickers)
        df_plot = datos[t_ver].dropna()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['Close'], name="Precio"))
        fig.update_layout(template="plotly_white", height=400, title=f"Tendencia de {t_ver}")
        st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="footer">Desarrollado por Corzo Tech © 2026</div>', unsafe_allow_html=True)


