import tkinter as tk
from tkinter import ttk


class HistoryWindow(tk.Toplevel):
    def __init__(self,parent,db):
        super().__init__(parent)
        self.db=db; self.title("Bill History"); self.geometry("1000x560")
        frame=ttk.Frame(self,padding=12); frame.pack(fill="both",expand=True)
        cols=("bill","date","subtotal","discount","tax","total","paid","change")
        self.tree=ttk.Treeview(frame,columns=cols,show="headings")
        for c,h in zip(cols,["Bill No","Date","Subtotal","Discount","Tax","Total","Paid","Change"]):
            self.tree.heading(c,text=h); self.tree.column(c,width=120,anchor="center")
        self.tree.pack(fill="both",expand=True); self.tree.bind("<Double-1>",self.view)
        ttk.Label(frame,text="Double-click a bill to view details.").pack(pady=8)
        self.refresh()

    def refresh(self):
        for x in self.tree.get_children():self.tree.delete(x)
        for b in self.db.list_bills():
            self.tree.insert("", "end",values=(b["bill_no"],b["created_at"],f"₹ {b['subtotal']:.2f}",
                f"₹ {b['discount']:.2f}",f"₹ {b['tax']:.2f}",f"₹ {b['total']:.2f}",
                f"₹ {b['paid']:.2f}",f"₹ {b['change_amount']:.2f}"))

    def view(self,_=None):
        sel=self.tree.selection()
        if not sel:return
        no=self.tree.item(sel[0],"values")[0]
        bill,items=self.db.get_bill(no)
        w=tk.Toplevel(self); w.title("Bill "+no); w.geometry("650x500")
        t=tk.Text(w,font=("Consolas",10)); t.pack(fill="both",expand=True,padx=10,pady=10)
        lines=["SUPERMARKET BILL","="*55,f"Bill No: {bill['bill_no']}",f"Date: {bill['created_at']}","-"*55]
        for x in items:
            lines.append(f"{x['name'][:25]:25} {x['qty']:>4} x {x['price']:>8.2f} = {x['line_total']:>9.2f}")
        lines += ["-"*55,f"Subtotal: ₹ {bill['subtotal']:.2f}",f"Tax: ₹ {bill['tax']:.2f}",
                  f"Discount: ₹ {bill['discount']:.2f}",f"TOTAL: ₹ {bill['total']:.2f}",
                  f"Paid: ₹ {bill['paid']:.2f}",f"Change: ₹ {bill['change_amount']:.2f}","="*55]
        t.insert("1.0","\n".join(lines)); t.configure(state="disabled")
