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

# Diccionario de textos
txt = {
    "Español": {
        "tit": "TERMINAL DE MERCADOS", "compra": "✅ COMPRA", "espera": "❌ ESPERAR", 
        "desc": "Descargar Excel", "creado": "Creado por Corzo Tech",
        "apoyo": "☕ Donar por PayPal",
        "nota_tit": "💡 Guía de Lectura del Panorama General:",
        "nota_1": "Ranking Dinámico: Esta lista evalúa el valor de mercado. Si una compañía cae, será reemplazada automáticamente.",
        "nota_2": "Señales Automáticas: Evalúa si el precio está por encima o por debajo de su promedio móvil (EMA).",
        "nota_3": "Uso Recomendado: Monitor informativo de apoyo para complementar tu estrategia personal."
    },
    "English": {
        "tit": "MARKET TERMINAL", "compra": "✅ BUY", "espera": "❌ WAIT", 
        "desc": "Download Excel", "creado": "Created by Corzo Tech",
        "apoyo": "☕ Donate via PayPal",
        "nota_tit": "💡 Quick Reading Guide:",
        "nota_1": "Dynamic Ranking: This list evaluates market value. If a company drops, it will be replaced automatically.",
        "nota_2": "Automatic Signals: Evaluates if the price is above or below its moving average (EMA).",
        "nota_3": "Usage: Informational monitor to complement your personal strategy."
    }
}[idioma]

st.markdown(f'<div class="header-right"><h1>{txt["tit"]}</h1></div>', unsafe_allow_html=True)

# --- BLOQUE DINÁMICO (AUTO-REFRESCO 5 MIN) ---
@st.fragment(run_every=300)
def contenido_dinamico(mercado, estrategia, textos):
    st.markdown("""
        <style>
        .stApp { background-color: #ffffff !important; }
        #MainMenu, .stDeployButton {visibility: hidden; display:none;}
        header { background-color: rgba(0,0,0,0) !important; border: none !important; }
        .block-container { padding-top: 1rem !important; }
        .header-right { display: flex; justify-content: flex-end; align-items: center; padding: 10px 25px; border-bottom: 1px solid #f0f0f0; }
        .header-right h1 { font-size: 18px; font-weight: 700; color: #4a4a4a; text-transform: uppercase; }
        .credit-text { margin-top: 20px; font-size: 14px; color: #888; font-weight: 600; font-style: italic; }
        </style>
        """, unsafe_allow_html=True)

    @st.cache_data(ttl=600)
    def obtener_top_10(m_nombre):
        listas = {
            "🇲🇽 México (IPC)": ["AMXB.MX", "WALMEX.MX", "GFNORTEO.MX", "GMEXICOB.MX", "FEMSAUBD.MX", "CEMEXCPO.MX", "GAPB.MX", "ASURB.MX", "AC.MX", "BIMBOA.MX"],
            "🇺🇸 EE.UU. (Wall Street)": ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "BRK-B", "LLY", "AVGO"],
            "🚀 Cripto (USD)": ["BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD", "ADA-USD", "DOGE-USD", "TRX-USD", "LINK-USD", "DOT-USD"]
        }
        try:
            info = []
            for t in listas[m_nombre]:
                ticker_obj = yf.Ticker(t)
                m_cap = ticker_obj.info.get('marketCap', 0)
                if m_cap > 0:
                    info.append({'ticker': t, 'marketCap': m_cap})
            
            if len(info) > 0:
                df_rank = pd.DataFrame(info).sort_values('marketCap', ascending=False)
                return df_rank['ticker'].tolist()
            return listas[m_nombre]
        except:
            return listas[m_nombre]

    @st.cache_data(ttl=300)
    def descargar(tickers):
        return yf.download(tickers, period="1y", interval="1d", group_by='ticker', progress=False)

    with st.spinner('Sincronizando CorzoNow...'):
        top_10 = obtener_top_10(mercado)
        datos = descargar(top_10)

    config = {"Day-Trading": (20, 14), "Swing-Traiding": (50, 14), "Position-Trading": (200, 21)}
    ema_p, rsi_p = config[estrategia]

    c1, c2 = st.columns([1.1, 1.2])

    with c1:
        res = []
        for t in top_10:
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
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_f.to_excel(writer, index=False, sheet_name='Analisis')
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            st.download_button(label=f"📥 {textos['desc']}", data=output.getvalue(), file_name=f"panorama_{mercado}.xlsx", use_container_width=True)
        with col_btn2:
            # Enlace de PayPal directo usando tu correo
            link_paypal = f"https://paypal.com"
            st.link_button(f"{textos['apoyo']}", url=link_paypal, use_container_width=True)
            
        st.markdown(f'<p class="credit-text" style="text-align:center;">🚀 {textos["creado"]}</p>', unsafe_allow_html=True)

    with c2:
        sel = st.selectbox("Selecciona para graficar:", top_10)
        df_s = datos[sel].dropna()
        df_s['EMA'] = df_s['Close'].ewm(span=ema_p, adjust=False).mean()
        
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df_s.index[-60:], open=df_s['Open'][-60:], high=df_s['High'][-60:], low=df_s['Low'][-60:], close=df_s['Close'][-60:], name="Precio"))
        fig.add_trace(go.Scatter(x=df_s.index[-60:], y=df_s['EMA'][-60:], line=dict(color='#0077b6', width=2), name=f"EMA {ema_p}"))
        fig.add_trace(go.Bar(x=df_s.index[-60:], y=df_s['Volume'][-60:], name="Volumen", marker_color='rgba(128, 128, 128, 0.2)', yaxis='y2'))
        
        if logo_html:
            fig.add_layout_image(dict(source=logo_html, xref="paper", yref="paper", x=0.5, y=0.5, sizex=0.6, sizey=0.6, xanchor="center", yanchor="middle", opacity=0.08, layer="below"))
        
        fig.update_layout(height=480, template="none", xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=10, b=0), yaxis2=dict(overlaying='y', side='right', showgrid=False))
        st.plotly_chart(fig, use_container_width=True)

    # --- NOTA INFORMATIVA FINAL ---
    st.markdown("---")
    st.info(f"**{textos['nota_tit']}**\n\n1. {textos['nota_1']}\n\n2. {textos['nota_2']}\n\n3. {textos['nota_3']}")

# Iniciar aplicación
contenido_dinamico(mercado_sel, estrategia_sel, txt)
