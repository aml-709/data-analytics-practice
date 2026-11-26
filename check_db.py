import sqlite3

conn = sqlite3.connect("shop.db")
cursor = conn.cursor()


def show(title, query, params=()):
    print(f"\n=== {title} ===")
    cursor.execute(query, params)
    for row in cursor.fetchall():
        print(row)


show("Все записи", "SELECT * FROM sales")

show("Задание 3: товары дороже 20 000 тенге",
     "SELECT * FROM sales WHERE price > 20000")

show("Задание 4: товары категории «Техника»",
     "SELECT * FROM sales WHERE category = ?", ("Техника",))

show("Задание 5: сортировка по цене (от дорогих к дешёвым)",
     "SELECT product, category, price FROM sales ORDER BY price DESC")

show("Задание 6: количество записей",
     "SELECT COUNT(*) FROM sales")

show("Количество записей по категориям",
     "SELECT category, COUNT(*) FROM sales GROUP BY category")

conn.close()
