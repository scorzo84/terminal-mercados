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

# --- SIDEBAR (ESTÁTICA) ---
with st.sidebar:
    st.markdown("### 🕹️ Configuración")
    idioma = st.selectbox("🌐 Idioma", ["Español", "English"])
    mercado_sel = st.selectbox("Mercado", ["🇲🇽 México (IPC)", "🇺🇸 EE.UU. (Wall Street)", "🚀 Cripto (USD)"])
    estrategia_sel = st.radio("Estrategia", ["Day-Trading", "Swing-Traiding", "Position-Trading"])

# Diccionario de textos ajustado para el comportamiento HÍBRIDO y PAGO
txt = {
    "Español": {
        "tit": "TERMINAL DE MERCADOS", "compra": "✅ COMPRA", "espera": "❌ ESPERAR", 
        "desc": "Descargar Excel", "creado": "Creado por Corzo Tech",
        "btn_mx": "☕ Regalar un café (Donar)", 
        "btn_usa": "💳 Acceso Premium",
        "msg_pago": "📧 Tras el pago, recibirás tu código por correo.",
        "advertencia": "⚠️ Revisa tu bandeja de entrada (y SPAM) tras el pago.",
        "nota_tit": "💡 Guía de Lectura:",
        "nota_1": "Ranking Dinámico: Evaluación por valor de mercado.",
        "nota_2": "Señales: Precio vs promedio móvil (EMA).",
        "nota_3": "Uso: Monitor informativo complementario."
    },
    "English": {
        "tit": "MARKET TERMINAL", "compra": "✅ BUY", "espera": "❌ WAIT", 
        "desc": "Download Excel", "creado": "Created by Corzo Tech",
        "btn_mx": "☕ Buy me a coffee (Donate)", 
        "btn_usa": "💳 Premium Access",
        "msg_pago": "📧 After payment, you'll receive your code via email.",
        "advertencia": "⚠️ Check your inbox (and SPAM) after payment.",
        "nota_tit": "💡 Quick Guide:",
        "nota_1": "Dynamic Ranking: Market value based.",
        "nota_2": "Signals: Price vs EMA.",
        "nota_3": "Usage: Informational support monitor."
    }
}[idioma]

# --- BLOQUE DINÁMICO ---
@st.fragment(run_every=300)
def contenido_dinamico(mercado, estrategia, textos):
    st.markdown("""
        <style>
        .stApp { background-color: #ffffff !important; }
        .header-right { display: flex; justify-content: flex-end; align-items: center; padding: 10px 25px; border-bottom: 1px solid #f0f0f0; }
        .header-right h1 { font-size: 18px; font-weight: 700; color: #4a4a4a; text-transform: uppercase; }
        .credit-text { margin-top: 20px; font-size: 14px; color: #888; font-weight: 600; font-style: italic; }
        .warning-text { color: #d9534f; font-size: 12px; font-weight: bold; margin-top: 5px; }
        </style>
        """, unsafe_allow_html=True)
    
    st.markdown(f'<div class="header-right"><h1>{textos["tit"]}</h1></div>', unsafe_allow_html=True)

    @st.cache_data(ttl=600)
    def obtener_top_10(m_nombre):
        listas = {
            "🇲🇽 México (IPC)": ["AMXB.MX", "WALMEX.MX", "GFNORTEO.MX", "GMEXICOB.MX", "FEMSAUBD.MX", "CEMEXCPO.MX", "GAPB.MX", "ASURB.MX", "AC.MX", "BIMBOA.MX"],
            "🇺🇸 EE.UU. (Wall Street)": ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "BRK-B", "LLY", "AVGO"],
            "🚀 Cripto (USD)": ["BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD", "ADA-USD", "DOGE-USD", "TRX-USD", "LINK-USD", "DOT-USD"]
        }
        return listas.get(m_nombre, [])

    with st.spinner('Actualizando datos...'):
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

        # --- BOTONES DE ACCIÓN ---
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_f.to_excel(writer, index=False, sheet_name='Analisis')
            if st.download_button(label=f"📥 {textos['desc']}", data=output.getvalue(), file_name="corzonow_analisis.xlsx", use_container_width=True):
                st.toast("✅ Reporte Excel generado", icon="📊")
        
        with col_btn2:
            email_paypal = "scorzo84@hotmail.com"
            precio_usd = "18.00" # Aprox $349 MXN
            
            if mercado == "🇲🇽 México (IPC)":
                label_boton = textos['btn_mx']
                url_final = f"https://paypal.me"
                msg_footer = "☕ Invita un café para apoyar el proyecto."
            else:
                label_boton = f"{textos['btn_usa']} ($349 MXN / $18 USD)"
                # Link con nota al vendedor y nombre de item específico
                url_final = (
                    f"https://paypal.com"
                    f"&business={email_paypal}"
                    f"&amount={precio_usd}"
                    f"&currency_code=USD"
                    f"&item_name=CORZONOW_PREMIUM_ACCESS_CODE"
                    f"&no_note=0"
                    f"&cn=Escribe_tu_email_para_enviarte_el_codigo"
                )
                msg_footer = textos['msg_pago']

            st.link_button(label_boton, url=url_final, use_container_width=True, type="primary")
            st.caption(f"_{msg_footer}_")
            if mercado != "🇲🇽 México (IPC)":
                st.markdown(f'<p class="warning-text">{textos["advertencia"]}</p>', unsafe_allow_html=True)
            
        st.markdown(f'<p class="credit-text" style="text-align:center;">🚀 {textos["creado"]}</p>', unsafe_allow_html=True)

    with c2:
        sel = st.selectbox("Selecciona para graficar:", tickers)
        df_s = datos[sel].dropna()
        df_s['EMA'] = df_s['Close'].ewm(span=ema_p, adjust=False).mean()
        
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df_s.index[-60:], open=df_s['Open'][-60:], high=df_s['High'][-60:], low=df_s['Low'][-60:], close=df_s['Close'][-60:], name="Precio"))
        fig.add_trace(go.Scatter(x=df_s.index[-60:], y=df_s['EMA'][-60:], line=dict(color='#0077b6', width=2), name=f"EMA {ema_p}"))
        
        if logo_html:
            fig.add_layout_image(dict(source=logo_html, xref="paper", yref="paper", x=0.5, y=0.5, sizex=0.6, sizey=0.6, xanchor="center", yanchor="middle", opacity=0.08, layer="below"))
        
        fig.update_layout(height=450, template="none", xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

    st.info(f"**{textos['nota_tit']}**\n\n1. {textos['nota_1']}\n\n2. {textos['nota_2']}\n\n3. {textos['nota_3']}")

# Ejecutar terminal
contenido_dinamico(mercado_sel, estrategia_sel, txt)
