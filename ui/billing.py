import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from services import add_to_cart, remove_from_cart, calculate_totals
from database import RECEIPT_DIR


class BillingWindow(tk.Toplevel):
    def __init__(self,parent,db,on_saved=None):
        super().__init__(parent)
        self.db=db; self.on_saved=on_saved; self.cart=[]
        self.title("New Bill / POS")
        self.geometry("1050x650")
        self.transient(parent); self.grab_set()
        self.build()

    def build(self):
        top=ttk.Frame(self,padding=12); top.pack(fill="x")
        ttk.Label(top,text="Product Code").pack(side="left")
        self.code=ttk.Entry(top,width=18); self.code.pack(side="left",padx=8)
        self.code.bind("<Return>",lambda e:self.add_product())
        ttk.Label(top,text="Qty").pack(side="left")
        self.qty=ttk.Spinbox(top,from_=1,to=999,width=7); self.qty.set(1); self.qty.pack(side="left",padx=8)
        ttk.Button(top,text="Add to Cart",command=self.add_product).pack(side="left",padx=5)
        ttk.Button(top,text="Clear",command=self.clear_cart).pack(side="left",padx=5)

        cols=("code","name","qty","price","tax","total")
        self.tree=ttk.Treeview(self,columns=cols,show="headings",height=16)
        for c,h,w in zip(cols,["Code","Product","Qty","Price","Tax %","Line Total"],[100,300,70,110,80,140]):
            self.tree.heading(c,text=h); self.tree.column(c,width=w,anchor="center")
        self.tree.pack(fill="both",expand=True,padx=12)
        self.tree.bind("<Delete>",lambda e:self.remove_selected())
        ttk.Button(self,text="Remove Selected",command=self.remove_selected).pack(anchor="w",padx=12,pady=6)

        pay=ttk.LabelFrame(self,text="Payment",padding=10); pay.pack(fill="x",padx=12,pady=10)
        self.sub= tk.StringVar(value="₹ 0.00"); self.taxv=tk.StringVar(value="₹ 0.00")
        self.disc=tk.StringVar(value="0"); self.total=tk.StringVar(value="₹ 0.00")
        self.paid=tk.StringVar(value="0"); self.change=tk.StringVar(value="₹ 0.00")
        rows=[("Subtotal",self.sub,True),("Tax",self.taxv,True),("Discount",self.disc,False),
              ("Grand Total",self.total,True),("Cash Paid",self.paid,False),("Change",self.change,True)]
        for i,(label,var,ro) in enumerate(rows):
            r=i//3;c=(i%3)*2
            ttk.Label(pay,text=label).grid(row=r,column=c,padx=5,pady=5,sticky="e")
            ent=ttk.Entry(pay,textvariable=var,width=16); ent.grid(row=r,column=c+1,padx=5,pady=5)
            if ro: ent.configure(state="readonly")
        self.disc.trace_add("write",lambda *_:self.update_totals())
        self.paid.trace_add("write",lambda *_:self.update_change())
        ttk.Button(pay,text="SAVE BILL & CREATE RECEIPT",command=self.save_bill).grid(row=2,column=0,columnspan=6,sticky="ew",pady=8)

    def add_product(self):
        product=self.db.get_product(self.code.get().strip())
        if not product:
            messagebox.showerror("Not found","Product code was not found."); return
        try: add_to_cart(self.cart,product,int(self.qty.get()))
        except ValueError as e: messagebox.showerror("Cannot add",str(e)); return
        self.code.delete(0,"end"); self.qty.set(1); self.refresh()

    def remove_selected(self):
        sel=self.tree.selection()
        if sel: remove_from_cart(self.cart,self.tree.index(sel[0])); self.refresh()

    def clear_cart(self):
        self.cart.clear(); self.refresh()

    def refresh(self):
        for x in self.tree.get_children(): self.tree.delete(x)
        for x in self.cart:
            self.tree.insert("", "end",values=(x["code"],x["name"],x["qty"],f"₹ {x['price']:.2f}",
                                               f"{x['tax']:.2f}",f"₹ {x['line_total']:.2f}"))
        self.update_totals()

    def update_totals(self):
        try: d=float(self.disc.get() or 0)
        except ValueError: d=0
        sub,tax,total=calculate_totals(self.cart,d)
        self.sub.set(f"₹ {sub:.2f}"); self.taxv.set(f"₹ {tax:.2f}"); self.total.set(f"₹ {total:.2f}")
        self.update_change()

    def update_change(self):
        try:
            paid=float(self.paid.get() or 0)
            total=float(self.total.get().replace("₹","").strip())
            self.change.set(f"₹ {max(0,paid-total):.2f}")
        except ValueError: self.change.set("₹ 0.00")

    def save_bill(self):
        if not self.cart: messagebox.showwarning("Empty","Add products first."); return
        try:
            d=float(self.disc.get() or 0); paid=float(self.paid.get() or 0)
        except ValueError:
            messagebox.showerror("Invalid","Discount and payment must be numbers."); return
        sub,tax,total=calculate_totals(self.cart,d)
        if paid < total:
            messagebox.showerror("Insufficient payment",f"Grand total is ₹ {total:.2f}."); return
        try:
            no=self.db.create_bill(self.cart,sub,d,tax,total,paid)
            path=self.receipt(no,sub,tax,d,total,paid)
        except Exception as e:
            messagebox.showerror("Save failed",str(e)); return
        messagebox.showinfo("Saved",f"Bill {no} saved.\nReceipt created at:\n{path}")
        if self.on_saved: self.on_saved()
        self.destroy()

    def receipt(self,no,sub,tax,d,total,paid):
        path=os.path.join(RECEIPT_DIR,f"receipt_{no}.txt")
        with open(path,"w",encoding="utf-8") as f:
            f.write("========================================\n")
            f.write("           SUPERMARKET RECEIPT\n")
            f.write("========================================\n")
            f.write(f"Bill No : {no}\nDate    : {datetime.now():%d-%m-%Y %H:%M}\n")
            f.write("----------------------------------------\n")
            for x in self.cart:
                f.write(f"{x['name'][:24]:24} x{x['qty']:3}  ₹{x['line_total']:8.2f}\n")
            f.write("----------------------------------------\n")
            f.write(f"Subtotal: ₹ {sub:.2f}\nTax:      ₹ {tax:.2f}\nDiscount: ₹ {d:.2f}\n")
            f.write(f"TOTAL:    ₹ {total:.2f}\nPaid:     ₹ {paid:.2f}\nChange:   ₹ {paid-total:.2f}\n")
            f.write("========================================\nThank you for shopping!\n")
        return path
