import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Tree Mortality Assessment", layout="wide")

st.title("🌲 Tree Mortality Assessment Tool")

# 📌 Качване на Excel файл
uploaded_file = st.file_uploader("Качи Excel файл (с Settings + FieldData)", type=["xlsx"])

if uploaded_file:
    try:
        # Четене на двата листа
        settings = pd.read_excel(uploaded_file, sheet_name="Settings", header=None)
        df = pd.read_excel(uploaded_file, sheet_name="FieldData")

        # Функция за извличане на параметри от Settings
        def get_setting(name):
            row = settings[settings[0] == name]
            if not row.empty:
                return float(row.iloc[0, 1])
            return None

        # Вътрешни тегла
        live_w = get_setting("Live w")
        scorched_w = get_setting("Scorched w")
        burnt_w = get_setting("Burnt w")

        bark_none_w = get_setting("None w")
        bark_surface_w = get_setting("Surface w")
        bark_moderate_w = get_setting("Moderate w")
        bark_deep_w = get_setting("Deep w")

        root_none_w = get_setting("None w")
        root_surface_w = get_setting("Surface w")
        root_moderate_w = get_setting("Moderate w")
        root_deep_w = get_setting("Deep w")

        # Общи тегла
        crown_weight = get_setting("Crown weight")
        bark_weight = get_setting("Bark weight")
        root_weight = get_setting("Roots weight")

        # MoistCrit
        moistcrit = get_setting("MoistCrit (%)")

        # 📌 Изчисления
        df["CDI"] = (df["Live (%)"] * live_w +
                     df["Scorched (%)"] * scorched_w +
                     df["Burnt (%)"] * burnt_w) / 100

        df["BDI"] = (df["Bark_None (%)"] * bark_none_w +
                     df["Bark_Surface (%)"] * bark_surface_w +
                     df["Bark_Moderate (%)"] * bark_moderate_w +
                     df["Bark_Deep (%)"] * bark_deep_w) / 100

        df["RDI"] = (df["Roots_None (%)"] * root_none_w +
                     df["Roots_Surface (%)"] * root_surface_w +
                     df["Roots_Moderate (%)"] * root_moderate_w +
                     df["Roots_Deep (%)"] * root_deep_w) / 100

        # WM_Min и WM_CritFlag
        df["WM_Min (%)"] = df[["WM_T1 (%)", "WM_T2 (%)", "WM_T3 (%)"]].min(axis=1)
        df["WM_CritFlag"] = df["WM_Min (%)"].apply(
            lambda x: 1 if pd.notna(x) and x != 0 and x <= moistcrit else 0
        )

        # Risk_Index
        df["Risk_Index"] = df.apply(
            lambda row: min(
                row["CDI"] * crown_weight,
                row["BDI"] * bark_weight,
                row["RDI"] * root_weight
            ),
            axis=1
        )

        # Mortality Probability
        def mortality(row):
            if row.get("Burnt (%)", 0) == 100:
                return "⬛ Сигурна смърт до 6 месеца"
            if row.get("Cambium_Dead_Count", 0) >= 3:
                return "⬛ Сигурна смърт до 6 месеца"
            if row.get("Critical_Total", 0) >= 3:
                return "⬛ Сигурна смърт до 6 месеца"
            if row.get("Critical_Total", 0) == 2:
                return "🟥 Висока вероятност до 6 месеца"
            if row.get("Critical_Total", 0) == 1:
                return "🟥 Висока вероятност до 12 месеца"
            if row["Risk_Index"] >= 0.60:
                return "🟥 Висока вероятност за смърт"
            if row["Risk_Index"] >= 0.40:
                return "🟨 Средна вероятност"
            return "🟩 Ниска вероятност"

        df["Mortality_Probability"] = df.apply(mortality, axis=1)

        # 📊 Показване
        st.subheader("📊 Оценка на дърветата")
        st.dataframe(df)

        # 📈 Обобщена статистика
        st.subheader("📈 Обобщена статистика")
        stats = df["Mortality_Probability"].value_counts()
        st.bar_chart(stats)
        st.write(stats)

        # 💾 Експорт
        st.subheader("💾 Експорт на резултатите")
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Изтегли като CSV", data=csv,
                           file_name="Tree_Mortality_Results.csv",
                           mime="text/csv")

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Results")
        st.download_button("⬇️ Изтегли като Excel", data=output.getvalue(),
                           file_name="Tree_Mortality_Results.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    except Exception as e:
        st.error(f"⚠️ Възникна грешка при обработката на файла: {e}")

