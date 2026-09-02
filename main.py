import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
from datetime import datetime

DB = "supermarket.db"

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def setup():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS products(
            id INTEGER PRIMARY KEY, code TEXT UNIQUE, name TEXT,
            category TEXT, price REAL, stock INTEGER, tax REAL);
        CREATE TABLE IF NOT EXISTS bills(
            id INTEGER PRIMARY KEY, bill_no TEXT UNIQUE, total REAL,
            paid REAL, change REAL, created TEXT);
        CREATE TABLE IF NOT EXISTS items(
            id INTEGER PRIMARY KEY, bill_id INTEGER, code TEXT,
            name TEXT, qty INTEGER, price REAL, tax REAL);
        """)
        if con.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
            con.executemany(
                "INSERT INTO products(code,name,category,price,stock,tax) VALUES(?,?,?,?,?,?)",
                [
                    ("1001","Rice 5kg","Groceries",420,50,5),
                    ("1002","Sugar 1kg","Groceries",55,100,5),
                    ("1003","Milk 1L","Dairy",62,80,0),
                    ("1004","Bread","Bakery",45,60,0),
                    ("1005","Cooking Oil 1L","Groceries",155,40,5),
                    ("1006","Shampoo","Personal Care",120,30,12),
                    ("1007","Biscuits","Snacks",30,120,5),
                ])

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simple Supermarket Billing")
        self.geometry("850x560")
        self.cart = []
        self.build_home()

    def clear(self):
        for w in self.winfo_children(): w.destroy()

    def build_home(self):
        self.clear()
        ttk.Label(self, text="SUPERMARKET BILLING SYSTEM",
                  font=("Arial", 22, "bold")).pack(pady=30)
        box = ttk.Frame(self)
        box.pack(pady=10)
        for text, command in [
            ("New Bill", self.billing),
            ("Products", self.products),
            ("Bill History", self.history)
        ]:
            ttk.Button(box, text=text, command=command, width=20).pack(pady=8)

        with db() as con:
            products = con.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            stock = con.execute("SELECT COALESCE(SUM(stock),0) FROM products").fetchone()[0]
            bills = con.execute("SELECT COUNT(*) FROM bills").fetchone()[0]
        ttk.Label(self, text=f"Products: {products}    Stock: {stock}    Bills: {bills}",
                  font=("Arial", 12)).pack(pady=30)

    def billing(self):
        win = tk.Toplevel(self)
        win.title("New Bill")
        win.geometry("800x600")

        top = ttk.Frame(win, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text="Product Code").pack(side="left")
        code = ttk.Entry(top, width=15); code.pack(side="left", padx=5)
        ttk.Label(top, text="Qty").pack(side="left")
        qty = ttk.Spinbox(top, from_=1, to=999, width=6); qty.set(1)
        qty.pack(side="left", padx=5)

        tree = ttk.Treeview(win, columns=("code","name","qty","price","total"),
                            show="headings", height=15)
        for c, h, width in [
            ("code","Code",100),("name","Product",250),("qty","Qty",70),
            ("price","Price",100),("total","Total",120)]:
            tree.heading(c, text=h); tree.column(c, width=width)
        tree.pack(fill="both", expand=True, padx=10)

        total_var = tk.StringVar(value="Total: ₹0.00")
        paid_var = tk.StringVar(value="0")

        def refresh():
            for x in tree.get_children(): tree.delete(x)
            total = 0
            for item in self.cart:
                line = item["price"] * item["qty"]
                total += line
                tree.insert("", "end", values=(
                    item["code"], item["name"], item["qty"],
                    f"₹{item['price']:.2f}", f"₹{line:.2f}"))
            tax = sum(i["price"] * i["qty"] * i["tax"] / 100 for i in self.cart)
            total += tax
            total_var.set(f"Total: ₹{total:.2f}")

        def add():
            pcode = code.get().strip()
            try:
                number = int(qty.get())
                if number <= 0: raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Enter a valid quantity."); return

            with db() as con:
                p = con.execute("SELECT * FROM products WHERE code=?", (pcode,)).fetchone()
            if not p:
                messagebox.showerror("Error", "Product not found."); return

            old = next((x for x in self.cart if x["id"] == p["id"]), None)
            current = old["qty"] if old else 0
            if current + number > p["stock"]:
                messagebox.showerror("Error", f"Only {p['stock']} available."); return
            if old:
                old["qty"] += number
            else:
                self.cart.append(dict(p, qty=number))
            code.delete(0, "end"); qty.set(1)
            refresh()

        def remove():
            selected = tree.selection()
            if selected:
                self.cart.pop(tree.index(selected[0]))
                refresh()

        def save():
            if not self.cart:
                messagebox.showwarning("Empty", "Add a product first."); return
            try: paid = float(paid_var.get())
            except ValueError:
                messagebox.showerror("Error", "Enter valid cash."); return

            subtotal = sum(i["price"] * i["qty"] for i in self.cart)
            tax = sum(i["price"] * i["qty"] * i["tax"] / 100 for i in self.cart)
            total = round(subtotal + tax, 2)
            if paid < total:
                messagebox.showerror("Error", f"Need ₹{total:.2f}."); return

            no = datetime.now().strftime("%Y%m%d%H%M%S")
            with db() as con:
                cur = con.execute(
                    "INSERT INTO bills(bill_no,total,paid,change,created) VALUES(?,?,?,?,?)",
                    (no,total,paid,paid-total,datetime.now().strftime("%d-%m-%Y %H:%M")))
                bill_id = cur.lastrowid
                for i in self.cart:
                    con.execute(
                        "INSERT INTO items(bill_id,code,name,qty,price,tax) VALUES(?,?,?,?,?,?)",
                        (bill_id,i["code"],i["name"],i["qty"],i["price"],i["tax"]))
                    con.execute("UPDATE products SET stock=stock-? WHERE id=?",
                                (i["qty"],i["id"]))

            receipt = f"""SUPERMARKET RECEIPT
------------------------------
Bill No: {no}
Date: {datetime.now():%d-%m-%Y %H:%M}
------------------------------
"""
            for i in self.cart:
                receipt += f"{i['name']} x{i['qty']} = ₹{i['price']*i['qty']:.2f}\n"
            receipt += f"""------------------------------
Subtotal: ₹{subtotal:.2f}
Tax:      ₹{tax:.2f}
TOTAL:    ₹{total:.2f}
Paid:     ₹{paid:.2f}
Change:   ₹{paid-total:.2f}
------------------------------
Thank you!
"""
            with open(f"receipt_{no}.txt", "w", encoding="utf-8") as f:
                f.write(receipt)

            messagebox.showinfo("Saved", f"Bill saved.\nReceipt: receipt_{no}.txt")
            self.cart = []
            win.destroy()
            self.build_home()

        ttk.Button(top, text="Add", command=add).pack(side="left", padx=5)
        ttk.Button(top, text="Remove", command=remove).pack(side="left", padx=5)
        ttk.Button(top, text="Clear", command=lambda: (self.cart.clear(), refresh())).pack(side="left")
        code.bind("<Return>", lambda e: add())

        bottom = ttk.Frame(win, padding=10); bottom.pack(fill="x")
        ttk.Label(bottom, textvariable=total_var,
                  font=("Arial", 14, "bold")).pack(side="left")
        ttk.Label(bottom, text="Cash Paid").pack(side="left", padx=(30,5))
        ttk.Entry(bottom, textvariable=paid_var, width=12).pack(side="left")
        ttk.Button(bottom, text="SAVE BILL", command=save).pack(side="right")

    def products(self):
        win = tk.Toplevel(self); win.title("Products"); win.geometry("850x600")
        form = ttk.Frame(win, padding=10); form.pack(fill="x")
        labels = ["Code","Name","Category","Price","Stock","Tax"]
        entries = {}
        for n, label in enumerate(labels):
            ttk.Label(form, text=label).grid(row=0,column=n)
            e=ttk.Entry(form,width=14); e.grid(row=1,column=n,padx=3)
            entries[label]=e

        tree=ttk.Treeview(win,columns=labels,show="headings")
        for label in labels:
            tree.heading(label,text=label); tree.column(label,width=125)
        tree.pack(fill="both",expand=True,padx=10,pady=5)

        def refresh():
            for x in tree.get_children(): tree.delete(x)
            with db() as con:
                rows=con.execute("SELECT code,name,category,price,stock,tax FROM products ORDER BY name").fetchall()
            for p in rows: tree.insert("", "end", values=tuple(p))

        def clear():
            for e in entries.values(): e.delete(0,"end")

        def add():
            try:
                values=(entries["Code"].get().strip(),entries["Name"].get().strip(),
                        entries["Category"].get().strip(),float(entries["Price"].get()),
                        int(entries["Stock"].get()),float(entries["Tax"].get()))
                if not values[0] or not values[1]: raise ValueError
                with db() as con:
                    con.execute("INSERT INTO products(code,name,category,price,stock,tax) VALUES(?,?,?,?,?,?)", values)
                clear(); refresh()
            except Exception:
                messagebox.showerror("Error","Enter valid product details.")

        def delete():
            selected=tree.selection()
            if not selected: return
            code_value=tree.item(selected[0],"values")[0]
            with db() as con: con.execute("DELETE FROM products WHERE code=?", (code_value,))
            refresh()

        ttk.Button(form,text="Add Product",command=add).grid(row=2,column=0,pady=8)
        ttk.Button(form,text="Delete Selected",command=delete).grid(row=2,column=1,pady=8)
        ttk.Button(form,text="Clear",command=clear).grid(row=2,column=2,pady=8)
        refresh()

    def history(self):
        win=tk.Toplevel(self); win.title("Bill History"); win.geometry("750x450")
        tree=ttk.Treeview(win,columns=("bill","total","paid","change","date"),show="headings")
        for c,h in zip(tree["columns"],["Bill No","Total","Paid","Change","Date"]):
            tree.heading(c,text=h); tree.column(c,width=140)
        tree.pack(fill="both",expand=True,padx=10,pady=10)
        with db() as con:
            rows=con.execute("SELECT bill_no,total,paid,change,created FROM bills ORDER BY id DESC").fetchall()
        for r in rows: tree.insert("", "end", values=tuple(r))

if __name__ == "__main__":
    setup()
    App().mainloop()
