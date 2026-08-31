import tkinter as tk
from tkinter import ttk
from ui.billing import BillingWindow
from ui.products import ProductsWindow
from ui.history import HistoryWindow


class MainWindow(tk.Tk):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.title("Supermarket Billing System")
        self.geometry("950x600")
        self.minsize(850,520)
        self._build()

    def _build(self):
        ttk.Style().configure("Title.TLabel", font=("Segoe UI",22,"bold"))
        ttk.Label(self,text="SUPERMARKET BILLING SYSTEM",style="Title.TLabel").pack(pady=(25,5))
        ttk.Label(self,text="Python Tkinter + SQLite").pack(pady=(0,25))
        bar = ttk.Frame(self); bar.pack(fill="x",padx=20)
        buttons = [
            ("New Bill",self.open_billing),("Products",self.open_products),
            ("Bill History",self.open_history),("Refresh",self.refresh)
        ]
        for i,(t,c) in enumerate(buttons):
            ttk.Button(bar,text=t,command=c,padding=15).grid(row=0,column=i,padx=8,sticky="ew")
            bar.columnconfigure(i,weight=1)
        self.area = ttk.Frame(self); self.area.pack(fill="both",expand=True,padx=30,pady=40)
        self.refresh()

    def refresh(self):
        for w in self.area.winfo_children(): w.destroy()
        p,s,b,sales = self.db.dashboard()
        cards=[("Products",p),("Units in Stock",s),("Bills",b),( "Sales",f"₹ {sales:,.2f}")]
        for i,(a,v) in enumerate(cards):
            box=ttk.LabelFrame(self.area,text=a,padding=25)
            box.grid(row=0,column=i,padx=8,sticky="nsew")
            self.area.columnconfigure(i,weight=1)
            ttk.Label(box,text=str(v),font=("Segoe UI",18,"bold")).pack()
        ttk.Label(self.area,text="Start a new bill from the button above. Stock is reduced automatically when a bill is saved.",
                  wraplength=750,justify="center").grid(row=1,column=0,columnspan=4,pady=40)

    def open_billing(self):
        BillingWindow(self,self.db,self.refresh)

    def open_products(self):
        ProductsWindow(self,self.db,self.refresh)

    def open_history(self):
        HistoryWindow(self,self.db)
