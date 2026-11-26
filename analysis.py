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


# =====================================================================
# ДЕНЬ 3. Проверка качества данных и аналитика продаж
# =====================================================================
print("\n" + "=" * 60)
print("ДЕНЬ 3. Проверка качества данных")
print("=" * 60)

# ---------- Задание 1: пропуски ----------
missing = df.isna().sum()
total_missing = int(missing.sum())
print("\nЗадание 1. Пропуски по столбцам:")
print(missing)

# ---------- Задание 2: дубликаты без учёта id ----------
columns = ["product", "category", "price", "quantity", "sale_date"]
dup_mask = df.duplicated(subset=columns, keep=False)
dup_count = int(df.duplicated(subset=columns).sum())
print(f"\nЗадание 2. Полных дубликатов строк (с id): {int(df.duplicated().sum())}")
print(f"Повторяющихся продаж без учёта id: {dup_count}")
if dup_count:
    print(df[dup_mask])
    print("Внимание: автоматически не удаляем, две одинаковые продажи могут быть настоящими.")

# Дополнительные проверки на логические ошибки
bad_price = int((df["price"] <= 0).sum())
bad_qty = int((df["quantity"] <= 0).sum())
parsed_dates = pd.to_datetime(df["sale_date"], errors="coerce")
bad_dates = int(parsed_dates.isna().sum())
print(f"Цен <= 0: {bad_price}; количеств <= 0: {bad_qty}; неверных дат: {bad_dates}")

# ---------- Задание 3: среднее и медиана ----------
mean_price = df["price"].mean()
median_price = df["price"].median()
print(f"\nЗадание 3. Средняя цена: {mean_price:,.0f} тенге".replace(",", " "))
print(f"Медианная цена: {median_price:,.0f} тенге".replace(",", " "))

# ---------- Задание 4: влияние выброса ----------
# Эксперимент проводится на копии базы в памяти: реальный shop.db не меняется,
# поэтому тестовую запись удалять не нужно.
OUTLIER_PRICE = 15_000_000

src = sqlite3.connect("shop.db")
test_conn = sqlite3.connect(":memory:")
src.backup(test_conn)
src.close()

test_conn.execute(
    "INSERT INTO sales (product, category, price, quantity, sale_date) "
    "VALUES (?, ?, ?, ?, ?)",
    ("ТЕСТ (выброс)", "Техника", OUTLIER_PRICE, 1, "2026-11-13"),
)
df_test = pd.read_sql_query("SELECT * FROM sales", test_conn)
test_conn.close()
df_test["revenue"] = df_test["price"] * df_test["quantity"]

mean_after = df_test["price"].mean()
median_after = df_test["price"].median()
revenue_after = df_test["revenue"].sum()
mean_change = (mean_after / mean_price - 1) * 100
median_change = (median_after / median_price - 1) * 100
revenue_change = (revenue_after / total_revenue - 1) * 100

print("\nЗадание 4. Влияние выброса (тестовая цена "
      f"{OUTLIER_PRICE:,} тенге):".replace(",", " "))
print(f"Средняя цена: {mean_price:,.0f} -> {mean_after:,.0f} ({mean_change:+.0f}%)".replace(",", " "))
print(f"Медиана:      {median_price:,.0f} -> {median_after:,.0f} ({median_change:+.1f}%)".replace(",", " "))
print(f"Общая выручка: {total_revenue:,.0f} -> {revenue_after:,.0f} ({revenue_change:+.0f}%)".replace(",", " "))

# Поиск выбросов по правилу межквартильного размаха (IQR) в реальных данных
q1, q3 = df["price"].quantile(0.25), df["price"].quantile(0.75)
iqr = q3 - q1
upper_fence = q3 + 1.5 * iqr
real_outliers = df[df["price"] > upper_fence]
print(f"\nГраница выбросов по IQR: {upper_fence:,.0f} тенге".replace(",", " "))
print("Цены выше границы в реальных данных:", ", ".join(real_outliers["product"]) or "нет")

# ---------- Задание 5-8: анализ по датам ----------
df["sale_date"] = pd.to_datetime(df["sale_date"])
daily = df.groupby("sale_date")["revenue"].sum()
daily_qty = df.groupby("sale_date")["quantity"].sum()

best_day, best_value = daily.idxmax(), daily.max()
worst_day, worst_value = daily.idxmin(), daily.min()

print("\nЗадание 5. Выручка по датам:")
print(daily)
print(f"\nЗадание 6. Максимальная выручка: {best_day.date()} ({best_value:,.0f} тенге)".replace(",", " "))
print(f"Задание 7. Минимальная выручка: {worst_day.date()} ({worst_value:,.0f} тенге)".replace(",", " "))

plt.figure(figsize=(10, 5))
plt.plot(daily.index.strftime("%d.%m"), daily.values, marker="o", color="#E15759")
plt.title("Динамика продаж: выручка по дням")
plt.xlabel("Дата (ноябрь 2026)")
plt.ylabel("Выручка, тенге")
plt.grid(alpha=0.3)
save_chart("revenue_by_date.png")

plt.figure(figsize=(10, 5))
plt.plot(daily_qty.index.strftime("%d.%m"), daily_qty.values, marker="o", color="#76B7B2")
plt.title("Количество проданных единиц по дням")
plt.xlabel("Дата (ноябрь 2026)")
plt.ylabel("Количество, шт.")
plt.grid(alpha=0.3)
save_chart("quantity_by_date.png")

# Сравнение среднего и медианы до и после выброса
plt.figure(figsize=(7, 5))
labels = ["Без выброса", "С выбросом"]
x = range(2)
plt.bar([i - 0.2 for i in x], [mean_price, mean_after], width=0.4, label="Среднее", color="#F28E2B")
plt.bar([i + 0.2 for i in x], [median_price, median_after], width=0.4, label="Медиана", color="#4E79A7")
plt.xticks(list(x), labels)
plt.title("Влияние выброса на среднюю и медианную цену")
plt.ylabel("Цена, тенге")
plt.legend()
save_chart("outlier_effect.png")

# ---------- Задание 9: выводы и отчёт ----------
def fmt(value):
    """Число с пробелами между разрядами: 1234567 -> '1 234 567'."""
    return f"{value:,.0f}".replace(",", " ")


trend_first = daily.iloc[: len(daily) // 2].mean()
trend_last = daily.iloc[len(daily) // 2:].mean()
trend_word = "выросла" if trend_last > trend_first else "снизилась"

findings = [
    f"Пропусков в данных {'нет' if total_missing == 0 else total_missing}, "
    f"повторяющихся продаж без учёта id: {dup_count}, "
    f"логических ошибок (цена или количество <= 0, неверная дата): {bad_price + bad_qty + bad_dates}.",
    f"Средняя цена ({fmt(mean_price)} тенге) выше медианы ({fmt(median_price)} тенге): "
    "в данных есть дорогие товары, которые тянут среднее вверх.",
    f"Одна запись с ценой {fmt(OUTLIER_PRICE)} тенге увеличила среднюю цену на {mean_change:.0f}%, "
    f"а медиану лишь на {median_change:.1f}%: медиана устойчива к выбросам.",
    f"Тот же выброс увеличил общую выручку на {revenue_change:.0f}%, "
    "то есть одна ошибка полностью исказила бы главный показатель отчёта.",
    f"Максимальная выручка за день: {best_day.date()} ({fmt(best_value)} тенге), "
    f"минимальная: {worst_day.date()} ({fmt(worst_value)} тенге).",
    f"Средняя дневная выручка во второй половине периода {trend_word} "
    f"({fmt(trend_first)} -> {fmt(trend_last)} тенге), но дни с дорогой техникой "
    "резко меняют график, поэтому по такому короткому периоду тренд ненадёжен.",
]

print("\nЗадание 9. Аналитические выводы:")
for i, text in enumerate(findings, 1):
    print(f"{i}. {text}")

report = f"""# День 3. Исследование данных и поиск аномалий

Отчёт создаётся автоматически программой `analysis.py` и пересчитывается при изменении данных в `shop.db`.

## 1. Качество данных
| Проверка | Результат |
|----------|-----------|
| Пропуски (всего по всем столбцам) | {total_missing} |
| Повторяющиеся продажи без учёта id | {dup_count} |
| Цена или количество <= 0 | {bad_price + bad_qty} |
| Неверные даты | {bad_dates} |

Повторяющиеся продажи автоматически не удаляются: две одинаковые продажи могут быть настоящими, это нужно проверять вручную.

## 2. Среднее и медиана цены
- Средняя цена: **{fmt(mean_price)} тенге**
- Медианная цена: **{fmt(median_price)} тенге**

## 3. Анализ выброса
Эксперимент выполнялся на копии базы в памяти (файл `shop.db` не изменялся): добавлена тестовая запись с ценой {fmt(OUTLIER_PRICE)} тенге.

| Показатель | До | После | Изменение |
|------------|----|-------|-----------|
| Средняя цена | {fmt(mean_price)} | {fmt(mean_after)} | {mean_change:+.0f}% |
| Медиана цены | {fmt(median_price)} | {fmt(median_after)} | {median_change:+.1f}% |
| Общая выручка | {fmt(total_revenue)} | {fmt(revenue_after)} | {revenue_change:+.0f}% |

![Влияние выброса](charts/outlier_effect.png)

### Почему необычные значения искажают результаты
Среднее арифметическое учитывает каждое значение, поэтому одно очень большое число сдвигает его далеко от типичных цен, и по среднему становится невозможно судить, сколько стоит обычный товар. Суммы (выручка) искажаются так же: одна ошибочная запись меняет главный показатель отчёта и все построенные на нём графики и решения. Медиана определяется положением значения в упорядоченном ряду, а не его величиной, поэтому почти не реагирует на выбросы. Поэтому перед анализом необходимо проверять данные и выяснять, ошибка это или реальное редкое событие: ошибку исправляют, реальное значение оставляют, но анализируют отдельно.

## 4. Динамика продаж
- День с максимальной выручкой: **{best_day.date()}** ({fmt(best_value)} тенге)
- День с минимальной выручкой: **{worst_day.date()}** ({fmt(worst_value)} тенге)

![Динамика продаж](charts/revenue_by_date.png)

![Количество по дням](charts/quantity_by_date.png)

## 5. Выводы
"""
for i, text in enumerate(findings, 1):
    report += f"{i}. {text}\n"

with open("day3_report.md", "w", encoding="utf-8") as f:
    f.write(report)

print("\nОтчёт сохранён: day3_report.md")
