import os
import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st

DB_PATH = "shop.db"

# set_page_config должен быть первой командой Streamlit
st.set_page_config(
    page_title="Аналитика магазина",
    page_icon="📊",
    layout="wide",
)


def money(value):
    """Число с пробелами между разрядами и знаком тенге."""
    return f"{value:,.0f} ₸".replace(",", " ")


@st.cache_data(show_spinner=False)
def load_data(db_mtime):
    """Читает таблицу sales из SQLite.

    Параметр db_mtime — время изменения файла базы: если shop.db изменился,
    кэш сбрасывается и данные загружаются заново.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        data = pd.read_sql_query("SELECT * FROM sales", conn)
    finally:
        conn.close()
    data["revenue"] = data["price"] * data["quantity"]
    data["sale_date"] = pd.to_datetime(data["sale_date"])
    return data


# ---------- Заголовок ----------
st.title("📊 Аналитика интернет-магазина")
st.caption("Данные берутся из базы shop.db. Используйте фильтры слева, чтобы изменить выборку.")

# ---------- Загрузка данных ----------
if not os.path.exists(DB_PATH):
    st.error("Файл shop.db не найден. Запустите setup_db.py и откройте приложение из папки проекта.")
    st.stop()

try:
    df = load_data(os.path.getmtime(DB_PATH))
except Exception as error:
    st.error(f"Не удалось прочитать таблицу sales: {error}")
    st.stop()

if df.empty:
    st.warning("В таблице sales нет записей.")
    st.stop()

# ---------- Фильтры (боковая панель) ----------
st.sidebar.header("Фильтры")

all_categories = sorted(df["category"].unique())
selected_categories = st.sidebar.multiselect(
    "Категории",
    all_categories,
    default=all_categories,
)

# Список товаров зависит от выбранных категорий
products_in_categories = sorted(
    df[df["category"].isin(selected_categories)]["product"].unique()
)
selected_products = st.sidebar.multiselect(
    "Товары",
    products_in_categories,
    default=products_in_categories,
)

filtered = df[
    df["category"].isin(selected_categories)
    & df["product"].isin(selected_products)
]

# ---------- Пустой результат ----------
if filtered.empty:
    st.info("Нет данных для выбранных фильтров. Выберите хотя бы одну категорию и один товар.")
    st.stop()

# ---------- Показатели ----------
by_product = filtered.groupby("product", as_index=False)["revenue"].sum()
best_product = by_product.sort_values("revenue", ascending=False).iloc[0]["product"]

st.subheader("Основные показатели")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Общая выручка", money(filtered["revenue"].sum()))
col2.metric("Продано единиц", f'{int(filtered["quantity"].sum())}')
col3.metric("Записей о продажах", len(filtered))
col4.metric("Средняя цена", money(filtered["price"].mean()))
col5.metric("Лидер по выручке", best_product)

# ---------- Графики ----------
st.subheader("Графики")

left, right = st.columns(2)

with left:
    fig_products = px.bar(
        by_product.sort_values("revenue", ascending=False),
        x="product",
        y="revenue",
        title="Выручка по товарам",
        labels={"product": "Товар", "revenue": "Выручка, тенге"},
    )
    fig_products.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_products)

with right:
    by_category = filtered.groupby("category", as_index=False)["revenue"].sum()
    fig_categories = px.pie(
        by_category,
        names="category",
        values="revenue",
        title="Доля категорий в выручке",
    )
    st.plotly_chart(fig_categories)

daily = filtered.groupby("sale_date", as_index=False)["revenue"].sum()
fig_daily = px.line(
    daily,
    x="sale_date",
    y="revenue",
    markers=True,
    title="Динамика выручки по дням",
    labels={"sale_date": "Дата", "revenue": "Выручка, тенге"},
)
st.plotly_chart(fig_daily)

qty_by_product = (
    filtered.groupby("product", as_index=False)["quantity"]
    .sum()
    .sort_values("quantity", ascending=False)
)
fig_qty = px.bar(
    qty_by_product,
    x="product",
    y="quantity",
    title="Количество проданных единиц по товарам",
    labels={"product": "Товар", "quantity": "Количество, шт."},
)
fig_qty.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig_qty)

# ---------- Таблица ----------
st.subheader("Таблица продаж")
table = filtered.sort_values("sale_date").copy()
table["sale_date"] = table["sale_date"].dt.strftime("%Y-%m-%d")
st.dataframe(table, hide_index=True)

# ---------- Экспорт CSV ----------
csv = table.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    "Скачать CSV",
    csv,
    file_name="sales_report.csv",
    mime="text/csv",
)
