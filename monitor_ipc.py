import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import base64
from io import BytesIO
from datetime import datetime

# 1. Configuración Global y Diseño Responsivo
st.set_page_config(
    page_title="CorzoNow - Terminal Inteligente", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- CSS PROFESIONAL Y ADAPTATIVO ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    .stTable { width: 100%; font-size: 14px; }

    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0;
        border-bottom: 2px solid #f0f2f6;
        margin-bottom: 20px;
    }
    .header-title {
        font-size: 22px;
        font-weight: 800;
        color: #1E3A8A;
        text-transform: uppercase;
    }
    .update-tag {
        font-size: 12px;
        color: #64748b;
        background-color: #f1f5f9;
        padding: 4px 10px;
        border-radius: 20px;
    }

    .premium-lock {
        background-color: #fef2f2;
        border: 1px solid #dc2626;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 20px 0;
    }
    
    .footer-credits {
        text-align: center;
        color: #94a3b8;
        font-size: 12px;
        margin-top: 30px;
        font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE LOGO ---
@st.cache_data
def get_logo_base64(path):
    try:
        with open(path, 'rb') as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    except: return None

logo_html = get_logo_base64("logo.png")

# --- SIDEBAR (CONFIGURACIÓN Y SEGURIDAD) ---
with st.sidebar:
    st.markdown("## 🕹️ Panel de Control")
    idioma = st.selectbox("🌐 Idioma", ["Español", "English"])
    mercado_sel = st.selectbox("📊 Seleccionar Mercado", ["🇲🇽 México (IPC)", "🇺🇸 EE.UU. (Wall Street)", "🚀 Cripto (USD)"])
    estrategia_sel = st.radio("📈 Estrategia", ["Day-Trading", "Swing-Traiding", "Position-Trading"])
    
    st.markdown("---")
    st.markdown("### 🔑 Acceso Premium")
    codigo_input = st.text_input("Ingresa tu código de acceso:", type="password")
    
    try:
        CODIGO_MAESTRO = st.secrets["PASSWORD_PREMIUM"]
    except:
        CODIGO_MAESTRO = "CORZO2026" 
    
    es_premium = (codigo_input == CODIGO_MAESTRO)

    if mercado_sel != "🇲🇽 México (IPC)" and not es_premium:
        st.error("🔒 Mercado Protegido")
    elif es_premium:
        st.success("🔓 Modo Premium Activo")

# --- TEXTOS ---
txt = {
    "Español": {
        "tit": "Terminal Inteligente", "compra": "✅ COMPRA", "espera": "❌ ESPERA", 
        "desc": "Descargar Excel", "creado": "Desarrollado por Corzo Tech",
        "btn_mx": "☕ Apoyar con un café (Donar)", 
        "btn_usa": "🚀 ACTIVAR ACCESO PREMIUM ($349 MXN)",
        "msg_pago": "📧 Envía tu comprobante a scorzo84@hotmail.com para recibir tu clave.",
        "bloqueo_tit": "CONTENIDO EXCLUSIVO",
        "bloqueo_msg": "Mercado Premium. Desbloquea las señales de compra realizando tu suscripción.",
        "act": "Última actualización:",
        "nota_tit": "💡 Guía de Análisis:",
        "nota_1": "Ranking: Basado en capitalización de mercado.",
        "nota_2": "Señales: Cruce de precio vs EMA configurada.",
        "nota_3": "Importante: Monitor informativo de apoyo."
    },
    "English": {
        "tit": "Intelligent Terminal", "compra": "✅ BUY", "espera": "❌ WAIT", 
        "desc": "Download Report", "creado": "Created by Corzo Tech",
        "btn_mx": "☕ Buy me a coffee (Donate)", 
        "btn_usa": "🚀 ACTIVATE PREMIUM ACCESS ($18 USD)",
        "msg_pago": "📧 Send payment proof to scorzo84@hotmail.com to get your key.",
        "bloqueo_tit": "EXCLUSIVE CONTENT",
        "bloqueo_msg": "Premium Market. Subscribe to unlock signals and charts.",
        "act": "Last update:",
        "nota_tit": "💡 Quick Guide:",
        "nota_1": "Ranking: Dynamic market cap evaluation.",
        "nota_2": "Signals: Price vs EMA crossover.",
        "nota_3": "Important: Information-only support tool."
    }
}[idioma]

# --- BLOQUE DINÁMICO CON REFRESCO DE 60 SEGUNDOS ---
@st.fragment(run_every=60)
def render_app(mercado, estrategia, textos, acceso_ok):
    ahora = datetime.now().strftime("%H:%M:%S")
    
    # Encabezado con Timer Visual
    st.markdown(f'''
        <div class="header-container">
            <div class="header-title">CorzoNow: {textos["tit"]}</div>
            <div class="update-tag">🔄 {textos["act"]} {ahora}</div>
        </div>
    ''', unsafe_allow_html=True)

    if mercado != "🇲🇽 México (IPC)" and not acceso_ok:
        st.markdown(f'<div class="premium-lock"><h2>{textos["bloqueo_tit"]}</h2><p>{textos["bloqueo_msg"]}</p></div>', unsafe_allow_html=True)
        email_paypal = "scorzo84@hotmail.com"
        url_pago = f"https://paypal.com{email_paypal}&amount=18.00&currency_code=USD&item_name=PREMIUM_ACCESS"
        st.link_button(textos['btn_usa'], url=url_pago, type="primary", use_container_width=True)
        st.info(textos['msg_pago'])
        return

    listas = {
        "🇲🇽 México (IPC)": ["AMXB.MX", "WALMEX.MX", "GFNORTEO.MX", "GMEXICOB.MX", "FEMSAUBD.MX", "CEMEXCPO.MX", "GAPB.MX", "ASURB.MX", "AC.MX", "BIMBOA.MX"],
        "🇺🇸 EE.UU. (Wall Street)": ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "BRK-B", "LLY", "AVGO"],
        "🚀 Cripto (USD)": ["BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD", "ADA-USD", "DOGE-USD", "TRX-USD", "LINK-USD", "DOT-USD"]
    }
    tickers = listas.get(mercado, [])

    # Descarga rápida (sin caché pesada para refresco real)
    datos = yf.download(tickers, period="5d", interval="1m" if mercado == "🚀 Cripto (USD)" else "1d", group_by='ticker', progress=False)

    config_est = {"Day-Trading": (20, 14), "Swing-Traiding": (50, 14), "Position-Trading": (200, 21)}
    ema_p, _ = config_est[estrategia]

    col1, col2 = st.columns([1.3, 1], gap="medium")

    with col1:
        res = []
        for t in tickers:
            try:
                df = datos[t].dropna()
                df['EMA'] = df['Close'].ewm(span=ema_p, adjust=False).mean()
                u, a = df.iloc[-1], df.iloc[-2]
                cambio = ((u['Close'] - a['Close']) / a['Close']) * 100
                señal = textos['compra'] if u['Close'] > u['EMA'] else textos['espera']
                res.append({"Ticker": t, "Precio": f"{u['Close']:,.2f}", "Hoy %": f"{cambio:+.2f}%", "Señal": señal})
            except: continue
        
        df_final = pd.DataFrame(res)
        st.table(df_final)

        # Acciones
        btn_a, btn_b = st.columns(2)
        with btn_a:
            output = BytesIO()
            df_final.to_excel(output, index=False, engine='xlsxwriter')
            st.download_button(label=textos['desc'], data=output.getvalue(), file_name="CorzoNow_Update.xlsx", use_container_width=True)
        with btn_b:
            if mercado == "🇲🇽 México (IPC)":
                st.link_button(textos['btn_mx'], url=f"https://paypal.me", use_container_width=True)
            else:
                st.success("💎 Premium Desbloqueado")

    with col2:
        seleccion = st.selectbox("Detalle de Activo:", tickers)
        df_sel = datos[seleccion].dropna()
        df_sel['EMA'] = df_sel['Close'].ewm(span=ema_p, adjust=False).mean()
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df_sel.index[-60:], open=df_sel['Open'][-60:], high=df_sel['High'][-60:], low=df_sel['Low'][-60:], close=df_sel['Close'][-60:], name="Precio"))
        fig.add_trace(go.Scatter(x=df_sel.index[-60:], y=df_sel['EMA'][-60:], line=dict(color='#2563eb', width=2), name="EMA"))
        if logo_html:
            fig.add_layout_image(dict(source=logo_html, xref="paper", yref="paper", x=0.5, y=0.5, sizex=0.5, sizey=0.5, xanchor="center", yanchor="middle", opacity=0.1, layer="below"))
        fig.update_layout(height=400, template="none", xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.info(f"**{textos['nota_tit']}**\n\n1. {textos['nota_1']}\n\n2. {textos['nota_2']}\n\n3. {textos['nota_3']}")
    st.markdown(f'<p class="footer-credits">{textos["creado"]} | © 2026</p>', unsafe_allow_html=True)

# Ejecutar
render_app(mercado_sel, estrategia_sel, txt, es_premium)



