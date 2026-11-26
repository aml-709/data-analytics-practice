import os
import sqlite3

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

# Если задать SHOW_CHARTS=1, графики дополнительно откроются на экране
if os.environ.get("SHOW_CHARTS") != "1":
    matplotlib.use("Agg")

CHARTS_DIR = "charts"
os.makedirs(CHARTS_DIR, exist_ok=True)

# ---------- 1. Получение данных из SQLite ----------
conn = sqlite3.connect("shop.db")
df = pd.read_sql_query("SELECT * FROM sales", conn)
conn.close()

print("Первые строки таблицы:")
print(df.head())

# ---------- 2. Расчёт показателей ----------
df["revenue"] = df["price"] * df["quantity"]

total_revenue = df["revenue"].sum()
total_quantity = df["quantity"].sum()

# Выручка и количество по товарам (если товар продавался несколько раз, суммируем)
by_product = df.groupby("product")["revenue"].sum().sort_values(ascending=False)
qty_by_product = df.groupby("product")["quantity"].sum().sort_values(ascending=False)
by_category = df.groupby("category")["revenue"].sum().sort_values(ascending=False)

top3 = by_product.head(3)

print(f"\nЗадание 1. Общая выручка: {total_revenue:,} тенге".replace(",", " "))
print(f"Задание 2. Всего продано единиц: {total_quantity}")
print("Задание 3. Топ-3 товара по выручке:")
for name, value in top3.items():
    print(f"  {name}: {value:,} тенге".replace(",", " "))


def save_chart(filename):
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, filename), dpi=150)
    if os.environ.get("SHOW_CHARTS") == "1":
        plt.show()
    plt.close()


# ---------- 3. Задание 4: выручка по товарам ----------
plt.figure(figsize=(11, 6))
by_product.plot(kind="bar", color="#4C78A8")
plt.title("Выручка по товарам")
plt.xlabel("Товар")
plt.ylabel("Выручка, тенге")
plt.xticks(rotation=45, ha="right")
save_chart("revenue_by_product.png")

# ---------- 4. Задание 5: доли категорий ----------
plt.figure(figsize=(7, 7))
by_category.plot(kind="pie", autopct="%1.1f%%", startangle=90)
plt.title("Доля категорий в общей выручке")
plt.ylabel("")
save_chart("revenue_by_category.png")

# ---------- 5. Задание 6: количество проданных товаров ----------
plt.figure(figsize=(11, 6))
qty_by_product.plot(kind="bar", color="#59A14F")
plt.title("Количество проданных единиц по товарам")
plt.xlabel("Товар")
plt.ylabel("Количество, шт.")
plt.xticks(rotation=45, ha="right")
save_chart("quantity_by_product.png")

print(f"\nЗадание 7. Графики сохранены в папку {CHARTS_DIR}/")

# ---------- 6. Задание 8: выводы (считаются автоматически) ----------
best_category = by_category.index[0]
best_share = by_category.iloc[0] / total_revenue * 100
top3_share = top3.sum() / total_revenue * 100
top_qty_name = qty_by_product.index[0]
top_qty_value = qty_by_product.iloc[0]

print("\nЗадание 8. Выводы:")
print(f"1. Больше всего выручки приносит категория «{best_category}» "
      f"({best_share:.1f}% от общей выручки).")
print(f"2. Три самых прибыльных товара ({', '.join(top3.index)}) "
      f"дают {top3_share:.1f}% всей выручки.")
print(f"3. Больше всего единиц продано по товару «{top_qty_name}» "
      f"({top_qty_value} шт.), хотя по выручке он может быть не в лидерах: "
      f"количество и выручка не всегда совпадают.")
