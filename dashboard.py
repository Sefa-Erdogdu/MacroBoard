import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import yfinance as yf

# API Adresi
API_BASE_URL = "http://127.0.0.1:8000/api/v1"

# Sayfa Yapılandırması
st.set_page_config(
    page_title="MacroBoard Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

SEKMELER = ["📊 Makro Terminal", "💼 Portföyüm", "🔍 Canlı Varlık Arama & İnceleme", "📄 Ekstre İçe Aktar"]

# 1. BEKLEYEN YÖNLENDİRME VARSA WİDGET EKRANA ÇİZİLMEDEN ÖNCE GÜNCELLE (HATA ÇÖZÜMÜ)
if "pending_nav" in st.session_state:
    st.session_state["main_nav_radio"] = st.session_state.pop("pending_nav")

if "main_nav_radio" not in st.session_state:
    st.session_state["main_nav_radio"] = SEKMELER[0]
if "active_ticker" not in st.session_state:
    st.session_state["active_ticker"] = "NVDA"
if "timeframe" not in st.session_state:
    st.session_state["timeframe"] = "1mo"

# ---------------------------------------------------------
# SPINNER'SIZ ÖNBELLEK
# ---------------------------------------------------------
@st.cache_data(ttl=30, show_spinner=False)
def fetch_macro_quotes():
    tickers = {
        "BİST 100": "XU100.IS",
        "S&P 500": "^GSPC",
        "USD / TRY": "TRY=X",
        "EUR / TRY": "EURTRY=X",
        "Ons Altın": "GC=F",
        "Brent Petrol": "BZ=F",
        "US 10Y Tahvil": "^TNX",
        "Bitcoin": "BTC-USD"
    }
    data = {}
    for name, sym in tickers.items():
        try:
            t = yf.Ticker(sym)
            p = t.fast_info.get("lastPrice", 0.0)
            prev = t.fast_info.get("previousClose", p)
            chg = ((p - prev) / prev * 100) if prev > 0 else 0.0
            data[name] = {"symbol": sym, "price": p, "change": chg}
        except Exception:
            pass
    return data

@st.cache_data(ttl=60, show_spinner=False)
def fetch_ticker_history(symbol: str, period: str):
    try:
        return yf.Ticker(symbol).history(period=period)
    except Exception:
        return pd.DataFrame()

# ---------------------------------------------------------
# ÖZEL TERMINAL CSS STİLLERİ
# ---------------------------------------------------------
st.markdown("""
<style>
    .stApp { background-color: #0c0f14; }
    
    /* Navigasyon Barı Stili */
    div[data-testid="stRadio"] > div {
        flex-direction: row;
        gap: 12px;
        margin-bottom: 20px;
    }
    div[data-testid="stRadio"] label {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        padding: 10px 22px !important;
        border-radius: 8px !important;
        color: #8b949e !important;
        font-weight: 600 !important;
        cursor: pointer;
    }
    div[data-testid="stRadio"] label:hover {
        border-color: #58a6ff !important;
        color: #f0f6fc !important;
    }

    /* Metrik Kartı */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #161b22, #0d1117);
        border: 1px solid #30363d;
        padding: 14px;
        border-radius: 10px;
    }
    div[data-testid="stMetric"]:hover {
        border-color: #58a6ff;
    }
</style>
""", unsafe_allow_html=True)

st.title("📈 MacroBoard Terminal")

# NAVİGASYON WIDGETI
st.radio(
    "Navigasyon Barı",
    SEKMELER,
    key="main_nav_radio",
    label_visibility="collapsed"
)

# =========================================================
# 1. SEKME: MAKRO TERMINAL
# =========================================================
if st.session_state["main_nav_radio"] == SEKMELER[0]:
    st.subheader("🌍 Küresel Piyasa & Makro Gösterge Paneli")
    st.caption("Göstergelerin altındaki butonlara bastığınızda anında grafik sayfasına yönlendirilirsiniz.")

    macro_data = fetch_macro_quotes()
    cols = st.columns(4)
    col_idx = 0

    for name, item in macro_data.items():
        sym = item["symbol"]
        price = item["price"]
        chg = item["change"]
        
        with cols[col_idx % 4]:
            st.metric(label=name, value=f"{price:,.2f}", delta=f"{chg:+.2f}%")
            if st.button("📊 Grafiği İncele", key=f"btn_m_{sym}", width="stretch"):
                st.session_state["active_ticker"] = sym
                st.session_state["pending_nav"] = SEKMELER[2]  # Güvenli Yönlendirme
                st.rerun()
        col_idx += 1

    st.divider()
    st.info("💡 **İpucu:** Herhangi bir makro verinin grafik detayına gitmek için '📊 Grafiği İncele' butonuna tıklayabilirsiniz.")

# =========================================================
# 2. SEKME: PORTFÖYÜM
# =========================================================
elif st.session_state["main_nav_radio"] == SEKMELER[1]:
    st.subheader("💼 Canlı Portföy Özeti")

    try:
        port_res = requests.get(f"{API_BASE_URL}/portfolio/summary")
        if port_res.status_code == 200:
            data = port_res.json()
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Toplam Değer", f"{data['total_portfolio_value_try']:,.2f} ₺")
            m2.metric("Toplam Maliyet", f"{data['total_portfolio_cost_try']:,.2f} ₺")
            m3.metric(
                "Net Kâr / Zarar", 
                f"{data['total_profit_loss_try']:,.2f} ₺", 
                delta=f"{data['total_profit_loss_percent']}%"
            )
            m4.metric("Dolar / TL Kuru", f"{data['usd_try_rate']:.2f} ₺")

            st.write("")
            items = data.get("items", [])
            if items:
                df = pd.DataFrame(items)
                col_chart, col_table = st.columns([1, 2])

                with col_chart:
                    st.markdown("### Varlık Ağırlıkları")
                    fig = px.pie(
                        df, 
                        names='symbol', 
                        values='value_try',
                        hole=0.6,
                        color_discrete_sequence=["#2b5c8f", "#d97724", "#258257", "#b83b3b", "#7b52ab", "#00a896"]
                    )
                    fig.update_traces(
                        textposition='outside', 
                        textinfo='percent+label',
                        marker=dict(line=dict(color='#0c0f14', width=2))
                    )
                    fig.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        showlegend=False,
                        margin=dict(l=20, r=20, t=20, b=20)
                    )
                    st.plotly_chart(fig, width="stretch")

                with col_table:
                    st.markdown("### Varlık Detayları")
                    display_df = df[[
                        "symbol", "asset_type", "amount", "avg_cost", 
                        "currency", "current_price", "value_try", "profit_loss_try", "profit_loss_percent"
                    ]].copy()
                    display_df.columns = [
                        "Sembol", "Tip", "Miktar", "Ort. Maliyet", 
                        "Para Birimi", "Anlık Fiyat", "Değer (₺)", "Kâr/Zarar (₺)", "Kâr/Zarar (%)"
                    ]
                    st.dataframe(display_df, width="stretch", hide_index=True)

                    st.write("**Grafiğini İncelemek İçin Tıklayın:**")
                    port_btns = st.columns(len(items))
                    for idx, item in enumerate(items):
                        sym_code = item["symbol"]
                        if port_btns[idx].button(f"🔍 {sym_code}", key=f"btn_p_{sym_code}_{item['id']}", width="stretch"):
                            st.session_state["active_ticker"] = sym_code
                            st.session_state["pending_nav"] = SEKMELER[2]  # Güvenli Yönlendirme
                            st.rerun()

                st.divider()

                # SAYFA İÇİ SİLME ALANI
                st.markdown("### 🗑️ Varlık Yönetimi & Silme")
                col_del_select, col_del_btn = st.columns([3, 1])
                
                with col_del_select:
                    item_options = {f"{item['symbol']} — Adet: {item['amount']} (ID: {item['id']})": item['id'] for item in items}
                    selected_del_option = st.selectbox("Silmek İstediğiniz Varlığı Seçin", list(item_options.keys()))
                
                with col_del_btn:
                    st.write("")
                    st.write("")
                    if st.button("Varlığı Portföyden Sil", type="primary", width="stretch"):
                        delete_id = item_options[selected_del_option]
                        del_res = requests.delete(f"{API_BASE_URL}/portfolio/delete/{delete_id}")
                        if del_res.status_code == 200:
                            st.success("Varlık silindi!")
                            st.rerun()
                        else:
                            st.error("Silme başarısız.")
            else:
                st.info("Portföyünüzde varlık bulunmuyor. 'Canlı Varlık Arama' sekmesinden ekleyebilirsiniz.")
    except Exception as e:
        st.error(f"Portföy verileri yüklenirken hata oluştu: {e}")

# =========================================================
# 3. SEKME: SINIRSIZ SERBEST ARAMA ENGINE
# =========================================================
elif st.session_state["main_nav_radio"] == SEKMELER[2]:
    st.subheader("🔎 Sınırsız Canlı Varlık Arama Engine")
    st.caption("İstediğiniz TÜM küresel hisseleri (PLAG, TTWO, AAPL, NVDA), BİST hisselerini (THYAO.IS), Kripto veya TEFAS fonlarını doğrudan yazabilirsiniz.")

    col_search_input, col_search_btn = st.columns([4, 1])
    
    with col_search_input:
        user_input = st.text_input(
            "Sembol / Varlık Adı Yazın (Örn: PLAG, TTWO, THYAO.IS, AAPL, BTC-USD, AFA)",
            value=st.session_state["active_ticker"],
            key="search_input_field"
        ).strip().upper()
    
    with col_search_btn:
        st.write("")
        st.write("")
        search_clicked = st.button("Piyasada Ara", type="primary", width="stretch")

    if user_input and user_input != st.session_state["active_ticker"]:
        st.session_state["active_ticker"] = user_input
        st.rerun()

    active_symbol = st.session_state["active_ticker"]

    if active_symbol:
        asset_type = "STOCK"
        live_price = 0.0
        currency = "USD"
        info_name = active_symbol

        # TEFAS Fon Kontrolü
        if len(active_symbol) == 3 and not active_symbol.endswith(".IS"):
            try:
                tf_res = requests.get(f"{API_BASE_URL}/fund/{active_symbol}")
                if tf_res.status_code == 200 and "error" not in tf_res.json():
                    fund_data = tf_res.json()
                    asset_type = "FUND"
                    live_price = fund_data.get("price", 0.0)
                    currency = "TRY"
                    info_name = fund_data.get("title", active_symbol)
            except Exception:
                pass

        # Standart Piyasa Kontrolü (yfinance)
        if asset_type == "STOCK":
            try:
                if active_symbol in ["ALTIN.S1.IS", "ALTIN.S1"]:
                    gold_ounce = yf.Ticker("GC=F").fast_info.get("lastPrice", 0.0)
                    usd_try = yf.Ticker("TRY=X").fast_info.get("lastPrice", 1.0)
                    if gold_ounce > 0:
                        gram_try = (gold_ounce * usd_try) / 31.1035
                        live_price = round(gram_try / 100, 2)
                        currency = "TRY"
                else:
                    t = yf.Ticker(active_symbol)
                    live_price = round(t.fast_info.get("lastPrice", 0.0), 2)
                    currency = "TRY" if active_symbol.endswith(".IS") else t.fast_info.get("currency", "USD")
                    
                    try:
                        long_name = t.info.get("longName")
                        if long_name:
                            info_name = f"{active_symbol} — {long_name}"
                    except Exception:
                        pass

            except Exception:
                live_price = 0.0

        if live_price > 0:
            st.success(f"**{info_name}**")
            k1, k2, k3 = st.columns(3)
            k1.metric("Anlık Piyasa Fiyatı", f"{live_price:,.2f} {currency}")
            k2.metric("Varlık Tipi", asset_type)
            k3.metric("Para Birimi", currency)

            # GRAFİK PERİYOT SEÇİMİ (1A, 3A, 6A, 1Y, 3Y, 5Y)
            if asset_type == "STOCK":
                st.markdown("### 📉 Tarihsel Fiyat Performansı")
                tf_map = {"1 Ay": "1mo", "3 Ay": "3mo", "6 Ay": "6mo", "1 Yıl": "1y", "3 Yıl": "3y", "5 Yıl": "5y"}
                
                tf_cols = st.columns(len(tf_map))
                for idx, (label, period_val) in enumerate(tf_map.items()):
                    if tf_cols[idx].button(label, key=f"tf_{period_val}", width="stretch"):
                        st.session_state["timeframe"] = period_val
                        st.rerun()

                selected_period = st.session_state["timeframe"]
                hist = fetch_ticker_history(active_symbol, selected_period)

                if not hist.empty:
                    fig_area = px.area(
                        hist, x=hist.index, y="Close", 
                        color_discrete_sequence=["#58a6ff"],
                        title=f"{active_symbol} — Periyot: {selected_period.upper()}"
                    )
                    fig_area.update_layout(
                        template="plotly_dark", 
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        xaxis_title="", yaxis_title=f"Fiyat ({currency})"
                    )
                    st.plotly_chart(fig_area, width="stretch")

            st.divider()

            # PORTFÖYE EKLEME FORMU
            st.markdown(f"### ➕ {active_symbol} Varlığını Portföye Ekle")
            with st.form("add_asset_direct_form"):
                ca, cb = st.columns(2)
                with ca:
                    add_amount = st.number_input("Adet / Miktar", min_value=0.0001, step=1.0, value=10.0)
                with cb:
                    add_cost = st.number_input(f"Ortalama Alış Maliyeti ({currency})", min_value=0.0001, step=0.1, value=float(live_price))
                
                btn_add = st.form_submit_button("Portföyüme Ekle", width="stretch")

                if btn_add:
                    payload = {
                        "symbol": active_symbol,
                        "asset_type": asset_type,
                        "amount": add_amount,
                        "avg_cost": add_cost
                    }
                    try:
                        res = requests.post(f"{API_BASE_URL}/portfolio/add", json=payload)
                        if res.status_code == 200:
                            st.success(f"{active_symbol} portföye eklendi!")
                            st.session_state["pending_nav"] = SEKMELER[1]  # Portföye Güvenli Dönüş
                            st.rerun()
                        else:
                            st.error("Ekleme başarısız.")
                    except Exception as e:
                        st.error(f"Bağlantı Hatası: {e}")
        else:
            st.error(f"'{active_symbol}' sembolü küresel piyasalarda bulunamadı. Lütfen geçerli bir kod girin (Örn: PLAG, TTWO, THYAO.IS, AAPL, BTC-USD).")

# =========================================================
# 4. SEKME: PDF EKSTRE İÇE AKTARMA
# =========================================================
elif st.session_state["main_nav_radio"] == SEKMELER[3]:
    st.subheader("📄 Aracı Kurum Ekstresinden İçe Aktar")
    st.caption("Şu an Midas hesap ekstresi (PDF) destekleniyor. Dosyayı yükleyin, önizlemeyi kontrol edin, onaylayın.")

    uploaded_pdf = st.file_uploader("PDF Dosyasını Seçin", type=["pdf"])

    if uploaded_pdf is not None:
        if st.button("Ekstreyi Analiz Et", type="primary"):
            files = {"file": (uploaded_pdf.name, uploaded_pdf.getvalue(), "application/pdf")}
            try:
                res = requests.post(f"{API_BASE_URL}/portfolio/import/preview", files=files)
                if res.status_code == 200:
                    st.session_state["import_preview"] = res.json()["items"]
                else:
                    st.error(f"Analiz başarısız: {res.json().get('detail', 'Bilinmeyen hata')}")
                    st.session_state.pop("import_preview", None)
            except Exception as e:
                st.error(f"Bağlantı Hatası: {e}")

    if "import_preview" in st.session_state and st.session_state["import_preview"]:
        st.divider()
        st.markdown("### 🔎 Bulunan Varlıklar — Onaylamadan Önce Kontrol Edin")

        # Mevcut portföydeki sembolleri çek (çakışma uyarısı için)
        existing_symbols = set()
        try:
            existing_res = requests.get(f"{API_BASE_URL}/portfolio/summary")
            if existing_res.status_code == 200:
                existing_symbols = {i["symbol"] for i in existing_res.json().get("items", [])}
        except Exception:
            pass

        preview_df = pd.DataFrame(st.session_state["import_preview"])
        preview_df.insert(0, "İçe Aktar", True)
        preview_df["Zaten Portföyde mi?"] = preview_df["symbol"].apply(
            lambda s: "⚠️ Evet — eklenirse ayrı satır olarak eklenir" if s in existing_symbols else "Yeni"
        )
        preview_df.columns = ["İçe Aktar", "Sembol", "Adet", "Ort. Maliyet", "Tip", "Durum"]

        edited_df = st.data_editor(
            preview_df,
            width="stretch",
            hide_index=True,
            disabled=["Sembol", "Adet", "Ort. Maliyet", "Tip", "Durum"]
        )

        if st.button("Seçilenleri Portföye Ekle", type="primary"):
            selected_rows = edited_df[edited_df["İçe Aktar"] == True]
            payload = [
                {
                    "symbol": row["Sembol"],
                    "asset_type": row["Tip"],
                    "amount": row["Adet"],
                    "avg_cost": row["Ort. Maliyet"]
                }
                for _, row in selected_rows.iterrows()
            ]
            try:
                res = requests.post(f"{API_BASE_URL}/portfolio/import/confirm", json=payload)
                if res.status_code == 200:
                    count = res.json().get("count", 0)
                    st.success(f"{count} varlık başarıyla portföye eklendi!")
                    st.session_state.pop("import_preview", None)
                    st.session_state["pending_nav"] = SEKMELER[1]
                    st.rerun()
                else:
                    st.error("Ekleme başarısız.")
            except Exception as e:
                st.error(f"Bağlantı Hatası: {e}")