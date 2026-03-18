import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

def connect_db():
    conn = sqlite3.connect("inventory.db")
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            price REAL NOT NULL,
            stock_quantity INTEGER NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Sales (
            sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            quantity_sold INTEGER NOT NULL,
            total_price REAL NOT NULL,
            sale_date TEXT NOT NULL,
            FOREIGN KEY(product_id) REFERENCES Products(product_id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    return conn

class InventoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Sales and Inventory System")
        self.root.geometry("900x750") # Increased height for restock UI
        self.conn = connect_db()
        
        self.pad = {'padx': 5, 'pady': 5}
        
        # Define Tags for row coloring
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_products = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_products, text="📦 Manage Products")
        self.setup_products_tab()
        
        self.tab_sales = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_sales, text="🛒 Sales & Transactions")
        self.setup_sales_tab()

    def setup_products_tab(self):
        # --- Top Section: Add Product ---
        controls_frame = ttk.Frame(self.tab_products)
        controls_frame.pack(fill="x", padx=10, pady=(10, 0))

        input_frame = ttk.LabelFrame(controls_frame, text="Add New Product", padding=10)
        input_frame.pack(side="left", fill="both", expand=True)

        ttk.Label(input_frame, text="Name:").grid(row=0, column=0, **self.pad)
        self.ent_name = ttk.Entry(input_frame, width=20)
        self.ent_name.grid(row=0, column=1, **self.pad)

        ttk.Label(input_frame, text="Category:").grid(row=0, column=2, **self.pad)
        self.ent_category = ttk.Entry(input_frame, width=20)
        self.ent_category.grid(row=0, column=3, **self.pad)

        ttk.Label(input_frame, text="Price (₱):").grid(row=1, column=0, **self.pad)
        self.ent_price = ttk.Entry(input_frame, width=20)
        self.ent_price.grid(row=1, column=1, **self.pad)

        ttk.Label(input_frame, text="Initial Stock:").grid(row=1, column=2, **self.pad)
        self.ent_stock = ttk.Entry(input_frame, width=20)
        self.ent_stock.grid(row=1, column=3, **self.pad)

        btn_add = ttk.Button(input_frame, text="➕ Add Product", command=self.add_product)
        btn_add.grid(row=2, column=0, columnspan=4, pady=(10, 0), sticky='ew')

        # --- Middle Section: Search & Delete ---
        action_frame = ttk.Frame(self.tab_products)
        action_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(action_frame, text="Search Name:", font=('Arial', 10, 'bold')).pack(side="left", padx=(0, 5))
        self.ent_search = ttk.Entry(action_frame, width=20)
        self.ent_search.pack(side="left", padx=5)
        self.ent_search.bind("<KeyRelease>", self.search_products)
        
        btn_delete = ttk.Button(action_frame, text="🗑️ Delete Selected", style='Danger.TButton', command=self.delete_product)
        btn_delete.pack(side="right", padx=(5, 0))
        self.style.configure('Danger.TButton', foreground='red')

        # --- Main Section: Product Table ---
        table_frame = ttk.Frame(self.tab_products)
        table_frame.pack(fill="both", expand=True, padx=10)

        columns = ("ID", "Name", "Category", "Price", "Stock")
        self.tree_prod = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # Visual tag for low stock
        self.tree_prod.tag_configure('low_stock', background='#ffcccc') 
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree_prod.yview)
        self.tree_prod.configure(yscrollcommand=scrollbar.set)
        
        for col in columns:
            self.tree_prod.heading(col, text=col)
            self.tree_prod.column(col, width=100, anchor="center")
        
        self.tree_prod.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- Bottom Section: RESTOCK CONTROL ---
        restock_frame = ttk.LabelFrame(self.tab_products, text="📦 Quick Restock Inventory", padding=10)
        restock_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(restock_frame, text="Product ID:").grid(row=0, column=0, **self.pad)
        self.ent_restock_id = ttk.Entry(restock_frame, width=10)
        self.ent_restock_id.grid(row=0, column=1, **self.pad)

        ttk.Label(restock_frame, text="Add Quantity:").grid(row=0, column=2, **self.pad)
        self.ent_restock_amt = ttk.Entry(restock_frame, width=10)
        self.ent_restock_amt.grid(row=0, column=3, **self.pad)

        btn_restock = ttk.Button(restock_frame, text="🔄 Restock Now", command=self.restock_product)
        btn_restock.grid(row=0, column=4, padx=10)
        
        self.refresh_products()

    def setup_sales_tab(self):
        input_frame = ttk.LabelFrame(self.tab_sales, text="Record a Sale", padding=10)
        input_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(input_frame, text="Product ID:").grid(row=0, column=0, **self.pad)
        self.ent_sale_id = ttk.Entry(input_frame, width=15)
        self.ent_sale_id.grid(row=0, column=1, **self.pad)

        ttk.Label(input_frame, text="Quantity Sold:").grid(row=0, column=2, **self.pad)
        self.ent_sale_qty = ttk.Entry(input_frame, width=15)
        self.ent_sale_qty.grid(row=0, column=3, **self.pad)

        btn_sell = ttk.Button(input_frame, text="🛒 Process Sale", command=self.record_sale)
        btn_sell.grid(row=0, column=4, padx=15, pady=5)

        columns = ("Sale ID", "Product Name", "Qty Sold", "Total Price", "Date")
        self.tree_sales = ttk.Treeview(self.tab_sales, columns=columns, show="headings")
        for col in columns:
            self.tree_sales.heading(col, text=col)
            self.tree_sales.column(col, width=120, anchor="center")
        self.tree_sales.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.refresh_sales()

    def add_product(self):
        name = self.ent_name.get().strip()
        category = self.ent_category.get().strip()
        price_str = self.ent_price.get().strip()
        stock_str = self.ent_stock.get().strip()

        if not name:
             messagebox.showerror("Input Error", "Product Name is required.")
             return

        try:
            price = float(price_str)
            stock = int(stock_str)
            if price < 0 or stock < 0: raise ValueError("Negative values.")
            
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO Products (name, category, price, stock_quantity) VALUES (?, ?, ?, ?)",
                           (name, category, price, stock))
            self.conn.commit()
            
            for ent in [self.ent_name, self.ent_category, self.ent_price, self.ent_stock]: ent.delete(0, tk.END)
            self.refresh_products()
            messagebox.showinfo("Success", f"Product '{name}' added!")
        except ValueError:
            messagebox.showerror("Input Error", "Invalid Price or Stock.")

    def restock_product(self):
        """Adds stock to an existing product."""
        try:
            prod_id = self.ent_restock_id.get().strip()
            amount = self.ent_restock_amt.get().strip()

            if not prod_id or not amount:
                messagebox.showerror("Input Error", "Enter Product ID and Amount.")
                return

            cursor = self.conn.cursor()
            # Verify product exists
            cursor.execute("SELECT name FROM Products WHERE product_id = ?", (prod_id,))
            product = cursor.fetchone()

            if product:
                cursor.execute("UPDATE Products SET stock_quantity = stock_quantity + ? WHERE product_id = ?", 
                               (int(amount), prod_id))
                self.conn.commit()
                self.refresh_products()
                self.ent_restock_id.delete(0, tk.END)
                self.ent_restock_amt.delete(0, tk.END)
                messagebox.showinfo("Restock", f"Added {amount} units to {product[0]}.")
            else:
                messagebox.showerror("Error", "Product ID not found.")
        except ValueError:
            messagebox.showerror("Input Error", "Please enter numbers only.")

    def record_sale(self):
        try:
            prod_id = self.ent_sale_id.get().strip()
            qty_sold = int(self.ent_sale_qty.get().strip())
            
            cursor = self.conn.cursor()
            cursor.execute("SELECT name, price, stock_quantity FROM Products WHERE product_id = ?", (prod_id,))
            product = cursor.fetchone()
            
            if not product:
                messagebox.showerror("Error", "Product not found.")
                return
                
            name, price, current_stock = product
            if qty_sold > current_stock:
                messagebox.showerror("Stock Error", "Insufficient stock!")
                return
                
            total_price = price * qty_sold
            sale_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute("INSERT INTO Sales (product_id, quantity_sold, total_price, sale_date) VALUES (?, ?, ?, ?)",
                           (prod_id, qty_sold, total_price, sale_date))
            cursor.execute("UPDATE Products SET stock_quantity = stock_quantity - ? WHERE product_id = ?",
                           (qty_sold, prod_id))
            self.conn.commit()
            
            self.refresh_products()
            self.refresh_sales()
            messagebox.showinfo("Sale Successful", f"Sold {qty_sold}x {name}.")
        except ValueError:
            messagebox.showerror("Input Error", "Invalid entries.")

    def search_products(self, event=None):
        search_query = self.ent_search.get().strip()
        for row in self.tree_prod.get_children(): self.tree_prod.delete(row)
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM Products WHERE name LIKE ?", ('%' + search_query + '%',))
        for row in cursor.fetchall():
            tag = 'low_stock' if row[4] < 5 else ''
            self.tree_prod.insert("", tk.END, values=(row[0], row[1], row[2], f"₱{row[3]:.2f}", row[4]), tags=(tag,))

    def delete_product(self):
        selected = self.tree_prod.selection()
        if not selected: return
        product_id = self.tree_prod.item(selected)['values'][0]
        if messagebox.askyesno("Confirm", "Delete this product and all sales history?"):
            self.conn.cursor().execute("DELETE FROM Products WHERE product_id = ?", (product_id,))
            self.conn.commit()
            self.refresh_products()
            self.refresh_sales()

    def refresh_products(self):
        for row in self.tree_prod.get_children(): self.tree_prod.delete(row)
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM Products")
        for row in cursor.fetchall():
            # If stock < 5, apply the 'low_stock' tag (red background)
            tag = 'low_stock' if row[4] < 5 else ''
            formatted_row = (row[0], row[1], row[2], f"₱{row[3]:.2f}", row[4])
            self.tree_prod.insert("", tk.END, values=formatted_row, tags=(tag,))

    def refresh_sales(self):
        for row in self.tree_sales.get_children(): self.tree_sales.delete(row)
        cursor = self.conn.cursor()
        cursor.execute("SELECT s.sale_id, p.name, s.quantity_sold, s.total_price, s.sale_date FROM Sales s JOIN Products p ON s.product_id = p.product_id")
        for row in cursor.fetchall():
            self.tree_sales.insert("", tk.END, values=(row[0], row[1], row[2], f"₱{row[3]:.2f}", row[4]))

if __name__ == "__main__":
    root = tk.Tk()
    app = InventoryApp(root)
    root.mainloop()