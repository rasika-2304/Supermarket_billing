import tkinter as tk
from tkinter import ttk, messagebox


class ProductsWindow(tk.Toplevel):
    def __init__(self,parent,db,on_changed=None):
        super().__init__(parent)
        self.db=db; self.on_changed=on_changed; self.selected=None
        self.title("Product Management"); self.geometry("1000x600")
        self.build(); self.refresh()

    def build(self):
        form=ttk.LabelFrame(self,text="Product Details",padding=10); form.pack(fill="x",padx=12,pady=12)
        labels=["Code","Name","Category","Price","Stock","Tax %"]
        self.vars=[tk.StringVar() for _ in labels]
        for i,l in enumerate(labels):
            ttk.Label(form,text=l).grid(row=0,column=i,padx=5,sticky="w")
            ttk.Entry(form,textvariable=self.vars[i],width=16).grid(row=1,column=i,padx=5,pady=5)
        for i,(t,c) in enumerate([("Add",self.add),("Update",self.update),("Delete",self.delete),("Clear",self.clear)]):
            ttk.Button(form,text=t,command=c).grid(row=2,column=i,pady=8)

        sf=ttk.Frame(self,padding=12); sf.pack(fill="x")
        ttk.Label(sf,text="Search").pack(side="left")
        self.search=tk.StringVar()
        e=ttk.Entry(sf,textvariable=self.search,width=35); e.pack(side="left",padx=8)
        self.search.trace_add("write",lambda *_:self.refresh())

        cols=("id","code","name","category","price","stock","tax")
        self.tree=ttk.Treeview(self,columns=cols,show="headings")
        for c,h in zip(cols,["ID","Code","Name","Category","Price","Stock","Tax %"]):
            self.tree.heading(c,text=h)
        self.tree.pack(fill="both",expand=True,padx=12,pady=(0,12))
        self.tree.bind("<<TreeviewSelect>>",self.select)

    def values(self):
        code,name,cat=self.vars[0].get().strip(),self.vars[1].get().strip(),self.vars[2].get().strip()
        if not code or not name: raise ValueError("Code and name are required.")
        price=float(self.vars[3].get()); stock=int(self.vars[4].get()); tax=float(self.vars[5].get())
        if min(price,stock,tax)<0: raise ValueError("Values cannot be negative.")
        return code,name,cat,price,stock,tax

    def add(self):
        try: self.db.add_product(*self.values()); self.clear(); self.refresh(); self.changed()
        except Exception as e: messagebox.showerror("Add failed",str(e))

    def update(self):
        if not self.selected: return
        try: self.db.update_product(self.selected,*self.values()); self.clear(); self.refresh(); self.changed()
        except Exception as e: messagebox.showerror("Update failed",str(e))

    def delete(self):
        if self.selected and messagebox.askyesno("Confirm","Delete selected product?"):
            try: self.db.delete_product(self.selected); self.clear(); self.refresh(); self.changed()
            except Exception as e: messagebox.showerror("Delete failed",str(e))

    def changed(self):
        if self.on_changed: self.on_changed()

    def clear(self):
        self.selected=None
        for v in self.vars: v.set("")

    def refresh(self):
        for x in self.tree.get_children(): self.tree.delete(x)
        for p in self.db.list_products(self.search.get() if hasattr(self,"search") else ""):
            self.tree.insert("", "end",values=(p["id"],p["code"],p["name"],p["category"],
                                               f"{p['price']:.2f}",p["stock"],f"{p['tax']:.2f}"))

    def select(self,_=None):
        sel=self.tree.selection()
        if not sel:return
        vals=self.tree.item(sel[0],"values"); self.selected=int(vals[0])
        for v,x in zip(self.vars,vals[1:]):v.set(x)
