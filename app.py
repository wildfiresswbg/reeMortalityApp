import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Tree Mortality Assessment", layout="wide")

st.title("🌲 Tree Mortality Assessment Tool")

# 1. Качване на файл
uploaded_file = st.file_uploader("Качи CSV или Excel файл", type=["csv", "xlsx"])

# 2. Настройки за прагове
st.sidebar.header("⚙️ Настройки на прагове")
cdi_thr = st.sidebar.slider("CDI праг", 0.0, 1.0, 0.50, 0.01)
bdi_thr = st.sidebar.slider("BDI праг", 0.0, 1.0, 0.75, 0.01)
rdi_thr = st.sidebar.slider("RDI праг", 0.0, 1.0, 0.75, 0.01)
risk_high = st.sidebar.slider("Risk Index – висок", 0.0, 1.0, 0.60, 0.01)
risk_med = st.sidebar.slider("Risk Index – среден", 0.0, 1.0, 0.40, 0.01)
moist_thr = st.sidebar.number_input("MoistCrit (%)", 0, 100, 25)

if uploaded_file:
    # 3. Зареждане
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.subheader("📋 Входни данни")
    st.dataframe(df.head())

    # 4. Изчисления
    if {"WM_T1 (%)","WM_T2 (%)","WM_T3 (%)"}.issubset(df.columns):
        df["WM_Min (%)"] = df[["WM_T1 (%)","WM_T2 (%)","WM_T3 (%)"]].min(axis=1)
    else:
        df["WM_Min (%)"] = None

    df["WM_CritFlag"] = df["WM_Min (%)"].apply(
        lambda x: 1 if pd.notna(x) and x != 0 and x <= moist_thr else 0
    )

    if {"CDI","BDI","RDI"}.issubset(df.columns):
        df["Critical_Zones_Count"] = (
            (df["CDI"] >= cdi_thr).astype(int) +
            (df["BDI"] >= bdi_thr).astype(int) +
            (df["RDI"] >= rdi_thr).astype(int)
        )
    else:
        df["Critical_Zones_Count"] = 0

    df["Critical_Total"] = df["Critical_Zones_Count"] + df["WM_CritFlag"]

    # 5. Логика за Mortality_Probability
    def mortality(row):
        if row.get("Burnt (%)",0) == 100:
            return "⬛ Сигурна смърт до 6 месеца"
        if row.get("Cambium_Dead_Count",0) >= 3:
            return "⬛ Сигурна смърт до 6 месеца"
        if row.get("Critical_Total",0) >= 3:
            return "⬛ Сигурна смърт до 6 месеца"
        if row.get("Critical_Total",0) == 2:
            return "🟥 Висока вероятност до 6 месеца"
        if row.get("Critical_Total",0) == 1:
            return "🟥 Висока вероятност до 12 месеца"
        if row.get("Risk_Index",0) >= risk_high:
            return "🟥 Висока вероятност за смърт"
        if row.get("Risk_Index",0) >= risk_med:
            return "🟨 Средна вероятност"
        return "🟩 Ниска вероятност"

    df["Mortality_Probability"] = df.apply(mortality, axis=1)

    # 6. Показване
    st.subheader("📊 Оценка на дърветата")
    st.dataframe(df)

    # 7. Обобщена статистика
    st.subheader("📈 Обобщена статистика")
    stats = df["Mortality_Probability"].value_counts()
    st.bar_chart(stats)
    st.write(stats)

    # 8. Експорт
    st.subheader("💾 Експорт на резултатите")

    # CSV
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Изтегли като CSV", data=csv,
                       file_name="Tree_Mortality_Results.csv",
                       mime="text/csv")

    # Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Results")
    st.download_button("⬇️ Изтегли като Excel", data=output.getvalue(),
                       file_name="Tree_Mortality_Results.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
