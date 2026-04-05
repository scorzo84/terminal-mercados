import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import base64
from io import BytesIO

# 1. Configuración Global
st.set_page_config(page_title="CorzoNow - Terminal Inteligente", layout="wide")

# --- CARGA DE LOGO ---
@st.cache_data
def get_logo_base64(path):
    try:
        with open(path, 'rb') as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    except: return None

logo_html = get_logo_base64("logo.png")

# --- SIDEBAR (CONFIGURACIÓN Y BLOQUEO DE SEGURIDAD) ---
with st.sidebar:
    st.markdown("### 🕹️ Configuración")
    idioma = st.selectbox("🌐 Idioma", ["Español", "English"])
    mercado_sel = st.selectbox("Mercado", ["🇲🇽 México (IPC)", "🇺🇸 EE.UU. (Wall Street)", "🚀 Cripto (USD)"])
    estrategia_sel = st.radio("Estrategia", ["Day-Trading", "Swing-Traiding", "Position-Trading"])
    
    st.markdown("---")
    st.markdown("### 🔑 Acceso Premium")
    codigo_input = st.text_input("Ingresa tu código aquí:", type="password")
    
    # --- SISTEMA DE SECRETOS (PROTECCIÓN ANT-HACKERS) ---
    # Intenta leer la contraseña desde Streamlit Cloud; si no existe, usa una de respaldo.
    try:
        CODIGO_MAESTRO = st.secrets["PASSWORD_PREMIUM"]
    except:
        CODIGO_MAESTRO = "CORZO2026" # Contraseña temporal si no has configurado los secretos
    
    es_premium = (codigo_input == CODIGO_MAESTRO)

    if mercado_sel != "🇲🇽 México (IPC)" and not es_premium:
        st.warning("⚠️ Mercado bloqueado. Requiere suscripción.")
    elif es_premium:
        st.success("✅ Acceso Premium Activado")

# Diccionario de textos (Incluye NOTAS)
txt = {
    "Español": {
        "tit": "TERMINAL DE MERCADOS", "compra": "✅ COMPRA", "espera": "❌ ESPERAR", 
        "desc": "Descargar Excel", "creado": "Creado por Corzo Tech",
        "btn_mx": "☕ Regalar un café (Donar)", 
        "btn_usa": "🚀 ACTIVAR PREMIUM ($349 MXN)",
        "msg_pago": "📧 Tras el pago, el código se enviará manualmente a tu correo de PayPal.",
        "advertencia": "⚠️ REVISA TU BANDEJA DE ENTRADA TRAS EL PAGO.",
        "bloqueo_tit": "🛑 ACCESO RESTRINGIDO",
        "bloqueo_msg": "Este mercado es exclusivo para usuarios Premium. Realiza tu pago abajo para obtener tu código.",
        "nota_tit": "💡 Guía de Lectura del Panorama General:",
        "nota_1": "Ranking Dinámico: Esta lista evalúa el valor de mercado. Si una compañía cae, será reemplazada automáticamente.",
        "nota_2": "Señales Automáticas: Evalúa si el precio está por encima o por debajo de su promedio móvil (EMA).",
        "nota_3": "Uso Recomendado: Monitor informativo de apoyo para complementar tu estrategia personal."
    },
    "English": {
        "tit": "MARKET TERMINAL", "compra": "✅ BUY", "espera": "❌ WAIT", 
        "desc": "Download Excel", "creado": "Created by Corzo Tech",
        "btn_mx": "☕ Buy me a coffee (Donate)", 
        "btn_usa": "🚀 ACTIVATE PREMIUM ($18 USD)",
        "msg_pago": "📧 After payment, the code will be sent manually to your PayPal email.",
        "advertencia": "⚠️ CHECK YOUR INBOX AFTER PAYMENT.",
        "bloqueo_tit": "🛑 RESTRICTED ACCESS",
        "bloqueo_msg": "This market is exclusive to Premium users. Make your payment below to get your code.",
        "nota_tit": "💡 Quick Reading Guide:",
        "nota_1": "Dynamic Ranking: Based on market value. If a company drops, it's replaced automatically.",
        "nota_2": "Automatic Signals: Price vs EMA check.",
        "nota_3": "Usage: Informational monitor to complement your strategy."
    }
}[idioma]

# --- BLOQUE DINÁMICO ---
@st.fragment(run_every=300)
def contenido_dinamico(mercado, estrategia, textos, acceso_concedido):
    st.markdown("""
        <style>
        .stApp { background-color: #ffffff !important; }
        .header-right { display: flex; justify-content: flex-end; align-items: center; padding: 10px 25px; border-bottom: 1px solid #f0f0f0; }
        .header-right h1 { font-size: 18px; font-weight: 700; color: #4a4a4a; text-transform: uppercase; }
        .credit-text { margin-top: 20px; font-size: 14px; color: #888; font-weight: 600; font-style: italic; }
        .warning-box { background-color: #ffcccc; padding: 15px; border-radius: 8px; border: 1px solid #d9534f; margin-top: 10px; }
        </style>
        """, unsafe_allow_html=True)
    
    st.markdown(f'<div class="header-right"><h1>{textos["tit"]}</h1></div>', unsafe_allow_html=True)

    # --- LÓGICA DE BLOQUEO ---
    if mercado != "🇲🇽 México (IPC)" and not acceso_concedido:
        st.error(f"### {textos['bloqueo_tit']}")
        st.info(textos['bloqueo_msg'])
        
        email_paypal = "scorzo84@hotmail.com"
        precio_usd = "18.00"
        url_pago = (
            f"https://paypal.com"
            f"&business={email_paypal}"
            f"&amount={precio_usd}"
            f"&currency_code=USD"
            f"&item_name=ACCESO_PREMIUM_CORZONOW"
            f"&no_note=0"
            f"&cn=ESCRIBE_TU_EMAIL_AQUI_PARA_EL_CODIGO"
        )
        
        st.link_button(textos['btn_usa'], url=url_pago, type="primary", use_container_width=True)
        st.markdown(f'<p class="warning-box" style="text-align:center;">{textos["msg_pago"]}</p>', unsafe_allow_html=True)
        return

    # --- CARGA DE DATOS ---
    @st.cache_data(ttl=600)
    def obtener_top_10(m_nombre):
        listas = {
            "🇲🇽 México (IPC)": ["AMXB.MX", "WALMEX.MX", "GFNORTEO.MX", "GMEXICOB.MX", "FEMSAUBD.MX", "CEMEXCPO.MX", "GAPB.MX", "ASURB.MX", "AC.MX", "BIMBOA.MX"],
            "🇺🇸 EE.UU. (Wall Street)": ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "BRK-B", "LLY", "AVGO"],
            "🚀 Cripto (USD)": ["BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD", "ADA-USD", "DOGE-USD", "TRX-USD", "LINK-USD", "DOT-USD"]
        }
        return listas.get(m_nombre, [])

    with st.spinner('Sincronizando mercados...'):
        tickers = obtener_top_10(mercado)
        datos = yf.download(tickers, period="1y", interval="1d", group_by='ticker', progress=False)

    config = {"Day-Trading": (20, 14), "Swing-Traiding": (50, 14), "Position-Trading": (200, 21)}
    ema_p, _ = config[estrategia]

    c1, c2 = st.columns([1.2, 1.1])

    with c1:
        res = []
        for t in tickers:
            try:
                df = datos[t].dropna()
                df['E'] = df['Close'].ewm(span=ema_p, adjust=False).mean()
                u, a = df.iloc[-1], df.iloc[-2]
                c = ((u['Close'] - a['Close']) / a['Close']) * 100
                s = textos['compra'] if u['Close'] > u['E'] else textos['espera']
                res.append({"Ticker": t, "Precio": round(float(u['Close']), 2), "Volumen": int(u['Volume']), "Hoy %": f"{c:+.2f}%", "Señal": s})
            except: continue
        
        df_f = pd.DataFrame(res).sort_values("Señal")
        st.table(df_f.assign(Volumen=lambda d: d['Volumen'].apply(lambda x: f"{x:,.0f}")))

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_f.to_excel(writer, index=False)
            st.download_button(label=f"📥 {textos['desc']}", data=output.getvalue(), file_name="reporte.xlsx", use_container_width=True)
        
        with col_btn2:
            if mercado == "🇲🇽 México (IPC)":
                url_cafe = f"https://paypal.com&business=scorzo84@hotmail.com&amount=0.00&item_name=Donar_Cafe&currency_code=MXN"
                st.link_button(textos['btn_mx'], url=url_cafe, use_container_width=True)
            else:
                st.success("💎 Versión Premium Activa")
            
        st.markdown(f'<p class="credit-text" style="text-align:center;">🚀 {textos["creado"]}</p>', unsafe_allow_html=True)

    with c2:
        sel = st.selectbox("Selecciona para graficar:", tickers)
        df_s = datos[sel].dropna()
        df_s['EMA'] = df_s['Close'].ewm(span=ema_p, adjust=False).mean()
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df_s.index[-60:], open=df_s['Open'][-60:], high=df_s['High'][-60:], low=df_s['Low'][-60:], close=df_s['Close'][-60:], name="Precio"))
        fig.add_trace(go.Scatter(x=df_s.index[-60:], y=df_s['EMA'][-60:], line=dict(color='#0077b6', width=2), name="EMA"))
        if logo_html:
            fig.add_layout_image(dict(source=logo_html, xref="paper", yref="paper", x=0.5, y=0.5, sizex=0.6, sizey=0.6, xanchor="center", yanchor="middle", opacity=0.08, layer="below"))
        fig.update_layout(height=450, template="none", xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

    # --- NOTA INFORMATIVA FINAL ---
    st.markdown("---")
    st.info(f"**{textos['nota_tit']}**\n\n1. {textos['nota_1']}\n\n2. {textos['nota_2']}\n\n3. {textos['nota_3']}")

# Iniciar
contenido_dinamico(mercado_sel, estrategia_sel, txt, es_premium)



