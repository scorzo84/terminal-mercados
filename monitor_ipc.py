import pandas_ta as ta

def obtener_analisis_profesional(df, estrategia):
    """
    Analiza CUALQUIER activo (Acciones o Cripto) con triple filtro.
    Evita señales falsas de fin de tendencia.
    """
    if len(df) < 50: 
        return "⏳ DATOS INSUF."

    # 1. AJUSTE DE PARÁMETROS POR ESTRATEGIA
    # No usamos lo mismo para Day-Trading que para Long Term
    configs = {
        "Day-Trading": {"ema_f": 9, "ema_s": 21, "rsi_max": 68, "rsi_min": 45},
        "Swing-Traiding": {"ema_f": 20, "ema_s": 50, "rsi_max": 62, "rsi_min": 40},
        "Position-Trading": {"ema_f": 50, "ema_s": 200, "rsi_max": 58, "rsi_min": 35}
    }
    c = configs[estrategia]

    # 2. CÁLCULO DE INDICADORES (Usando pandas_ta)
    df['EMA_FAST'] = ta.ema(df['Close'], length=c['ema_f'])
    df['EMA_SLOW'] = ta.ema(df['Close'], length=c['ema_s'])
    df['RSI'] = ta.rsi(df['Close'], length=14)
    
    # MACD para medir la fuerza del movimiento
    macd = ta.macd(df['Close'])
    df['MACD_LINE'] = macd.iloc[:, 0]
    df['MACD_SIG'] = macd.iloc[:, 2]

    # 3. FILTROS ANTIFALSOS (La "Triple Llave")
    ultimo = df.iloc[-1]
    
    # Filtro A: Tendencia (Precio sobre medias y media rápida sobre lenta)
    es_tendencia_alcista = ultimo['Close'] > ultimo['EMA_FAST'] > ultimo['EMA_SLOW']
    
    # Filtro B: Momentum (MACD cruzado al alza)
    tiene_fuerza = ultimo['MACD_LINE'] > ultimo['MACD_SIG']
    
    # Filtro C: Agotamiento (RSI)
    # Evita comprar si el RSI es muy alto (ya subió mucho) 
    # o muy bajo (está cayendo sin control)
    esta_en_punto_dulce = c['rsi_min'] < ultimo['RSI'] < c['rsi_max']

    # 4. RESULTADO FINAL
    if es_tendencia_alcista and tiene_fuerza and esta_en_punto_dulce:
        return "✅ COMPRA"
    elif es_tendencia_alcista or tiene_fuerza:
        # Si solo cumple una, hay duda, mejor ser cauteloso
        return "🟡 NEUTRAL"
    else:
        # Si el precio está abajo de la media o el MACD es bajista
        return "❌ ESPERA"

# --- APLICACIÓN EN TU BUCLE DE TICKERS ---
# Sustituye la parte donde generas 'res' por esto:
res = []
for t in tickers:
    try:
        # Ajustamos el intervalo de descarga según la estrategia
        intv = "15m" if estrategia_sel == "Day-Trading" else "1d" if estrategia_sel == "Swing-Traiding" else "1wk"
        periodo = "1mo" if estrategia_sel == "Day-Trading" else "1y"
        
        df_t = yf.download(t, period=periodo, interval=intv, progress=False)
        df_t = df_t.dropna()
        
        señal = obtener_analisis_profesional(df_t, estrategia_sel)
        
        u = df_t.iloc[-1]
        cambio = ((u['Close'] - df_t['Close'].iloc[-2]) / df_t['Close'].iloc[-2]) * 100
        
        res.append({
            "Ticker": t, 
            "Precio": f"{u['Close']:,.2f}", 
            "RSI": f"{u['RSI']:.1f}", # Para que veas por qué no compra
            "Hoy %": f"{cambio:+.2f}%", 
            "Señal": señal
        })
    except: continue


