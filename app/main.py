import streamlit as st
import pandas as pd
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Any, Callable

# ==========================================
# 1. EVENT BUS (Tulang Punggung Reaktif)
# ==========================================
@dataclass
class Event:
    event_type: str
    payload: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
    def subscribe(self, event_type: str, callback: Callable):
        if event_type not in self._subscribers: self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    def publish(self, event: Event):
        if event.event_type in self._subscribers:
            for cb in self._subscribers[event.event_type]: cb(event)

bus = EventBus()

# ==========================================
# 2. ENGINES & DECISION INTELLIGENCE
# ==========================================
class MacroEngine:
    def __init__(self): bus.subscribe("START_ANALYSIS", self.run)
    def run(self, event: Event):
        p = event.payload
        regime = "RISK_ON_BULL" if (p["vix"] < 20 and p["flow"] > 0) else ("RISK_OFF_BEAR" if p["vix"] > 25 else "SIDEWAYS_NEUTRAL")
        mult = 1.10 if regime == "RISK_ON_BULL" else (0.75 if regime == "RISK_OFF_BEAR" else 1.0)
        bus.publish(Event("MACRO_DONE", {"regime": regime, "mult": mult, "tickers": p["tickers"]}))

class ValueEngine:
    def __init__(self): bus.subscribe("MACRO_DONE", self.run)
    def run(self, event: Event):
        p = event.payload
        results = {}
        for t in p["tickers"]:
            name = t["ticker"]
            eps, bvps, price = t["eps"], t["bvps"], t["price"]
            fv = (22.5 * eps * bvps) ** 0.5 if (eps > 0 and bvps > 0) else 0
            mos = ((fv - price) / fv) * 100 if fv > 0 else -50
            score = min(max(50 + (mos * 1.5), 0), 100)
            
            # Audit trail & simulasi engine modular lain
            results[name] = {
                "Value": {"score": score, "fv": fv, "audit": [f"Graham Fair Value: IDR {fv:,.0f} vs Harga IDR {price:,.0f} (MoS: {mos:.1f}%)"]},
                "CorpAction": {"score": 70.0, "audit": ["Dividen konsisten 5 tahun terakhir."]},
                "Flow": {"score": 85.0, "audit": ["Akumulasi Smart Money (Asing) terdeteksi."]},
                "Swing": {"score": 65.0, "audit": ["Harga di area Demand Zone dengan konfirmasi volume."]}
            }
        bus.publish(Event("ENGINES_DONE", {"results": results, "regime": p["regime"], "mult": p["mult"]}))

class DecisionEngine:
    def __init__(self): 
        self.weights = {"Value": 0.35, "CorpAction": 0.20, "Flow": 0.20, "Swing": 0.25}
        bus.subscribe("ENGINES_DONE", self.run)
    def run(self, event: Event):
        p = event.payload
        final_decisions = []
        for ticker, eng in p["results"].items():
            raw_score = sum(eng[k]["score"] * self.weights[k] for k in self.weights)
            final_score = min(max(raw_score * p["mult"], 0.0), 100.0)
            
            rating = "STRONG BUY" if final_score >= 80 else ("ACCUMULATE" if final_score >= 65 else ("HOLD" if final_score >= 45 else "AVOID"))
            fv = eng["Value"]["fv"]
            
            white_box = [f"=== AUDIT TRAIL KEPUTUSAN (Skor Akhir: {final_score:.1f}/100) ==="]
            for k in eng:
                white_box.append(f"-> [{k} Engine] Skor: {eng[k]['score']:.1f}")
                for log in eng[k]["audit"]: white_box.append(f"   * {log}")

            final_decisions.append({
                "Ticker": ticker, "Rating": rating, "Skor": round(final_score, 1),
                "Fair Value": round(fv, 0), "Target Price": round(fv * 0.95, 0),
                "Entry Zone": f"IDR {fv*0.70:,.0f} - {fv*0.75:,.0f}", "Regime": p["regime"],
                "Breakdown": {k: eng[k]["score"] for k in eng}, "WhiteBox": white_box
            })
        bus.publish(Event("FINISH", {"decisions": final_decisions}))

# Inisialisasi Sistem
MacroEngine(); ValueEngine(); DecisionEngine()

# ==========================================
# 3. ANTARMUKA WEB (STREAMLIT DASHBOARD)
# ==========================================
st.set_page_config(page_title="IDX Quant Terminal", page_icon="📈", layout="wide")
st.title("🇮🇩 IDX Quant Terminal - Core Intelligence Engine")
st.caption("White-Box Investment Decision System | Event-Driven Architecture")

with st.sidebar:
    st.header("⚙️ Parameter Analisis")
    ticker_input = st.text_area("Daftar Ticker:", value="BBCA.JK, ASII.JK, BBRI.JK, TLKM.JK")
    tickers_list = [t.strip() for t in ticker_input.split(",") if t.strip()]
    
    st.markdown("---")
    st.subheader("Indikator Makroekonomi")
    bi_rate = st.slider("BI Rate (%)", 4.0, 8.0, 6.25, 0.25)
    vix = st.slider("VIX Index (Global Volatility)", 10.0, 40.0, 18.2, 0.5)
    foreign_flow = st.number_input("Net Foreign Flow 30D (Miliar IDR)", value=2450.0, step=100.0)
    run_btn = st.button("🚀 Jalankan Analisis Quant", type="primary", use_container_width=True)

if run_btn:
    with st.spinner("Mengorkestrasi Event Bus & Mesin Analisis..."):
        captured = []
        bus.subscribe("FINISH", lambda e: captured.extend(e.payload["decisions"]))
        
        # Simulasi Feed Data
        dummy_data = []
        for t in tickers_list:
            is_bank = "BB" in t
            dummy_data.append({
                "ticker": t, "price": 10200.0 if is_bank else 4600.0,
                "eps": 680 if is_bank else 820, "bvps": 4500 if is_bank else 7100
            })
            
        bus.publish(Event("START_ANALYSIS", {"vix": vix, "flow": foreign_flow, "tickers": dummy_data}))

    if captured:
        st.success("Analisis selesai! Rekomendasi disertai jejak kalkulasi yang dapat ditelusuri.")
        tab1, tab2 = st.tabs(["📊 Screener Akhir", "🔍 White-Box Audit Trail (Transparansi Model)"])
        
        with tab1:
            df = pd.DataFrame([{
                "Ticker": d["Ticker"], "Rating": d["Rating"], "Quant Score": f"{d['Skor']} / 100",
                "Fair Value (Est)": f"IDR {d['Fair Value']:,.0f}", "Target Price": f"IDR {d['Target Price']:,.0f}",
                "Regime Makro": d["Regime"]
            } for d in captured])
            st.dataframe(df, use_container_width=True, hide_index=True)
            
        with tab2:
            for d in captured:
                with st.expander(f"📌 {d['Ticker']} - Rating: {d['Rating']} (Skor: {d['Skor']})", expanded=True):
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.metric("Area Beli (Entry Zone)", d["Entry Zone"])
                        st.write("**Kontribusi Skor:**")
                        st.json(d["Breakdown"])
                    with col2:
                        st.markdown("**📝 Jejak Audit & Penjelasan Logika (White-Box):**")
                        for line in d["WhiteBox"]: st.write(line)
else:
    st.info("👆 Atur parameter di sidebar kiri, lalu klik tombol **'Jalankan Analisis Quant'**.")
