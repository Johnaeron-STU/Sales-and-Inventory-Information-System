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
        self.root.geometry("900x650")
        self.conn = connect_db()
        
        self.pad = {'padx': 5, 'pady': 5}
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_products = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_products, text="📦 Manage Products")
        self.setup_products_tab()
        
        self.tab_sales = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_sales, text="🛒 Sales & Transactions")
        self.setup_sales_tab()

    def setup_products_tab(self):
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

        action_frame = ttk.Frame(self.tab_products)
        action_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(action_frame, text="Search Product Name:", font=('Arial', 10, 'bold')).pack(side="left", padx=(0, 5))
        self.ent_search = ttk.Entry(action_frame, width=30)
        self.ent_search.pack(side="left", padx=5)
        self.ent_search.bind("<KeyRelease>", self.search_products)
        
        btn_clear = ttk.Button(action_frame, text="❌ Clear", command=self.clear_search)
        btn_clear.pack(side="left", padx=5)

        style = ttk.Style()
        style.configure('Danger.TButton', foreground='red')
        
        btn_delete = ttk.Button(action_frame, text="🗑️ Delete Selected Product", 
                                style='Danger.TButton', command=self.delete_product)
        btn_delete.pack(side="right", padx=(20, 0))

        columns = ("ID", "Name", "Category", "Price", "Stock")
        self.tree_prod = ttk.Treeview(self.tab_products, columns=columns, show="headings")
        
        scrollbar = ttk.Scrollbar(self.tab_products, orient="vertical", command=self.tree_prod.yview)
        self.tree_prod.configure(yscrollcommand=scrollbar.set)
        
        for col in columns:
            self.tree_prod.heading(col, text=col)
            if col == "Name":
                self.tree_prod.column(col, width=200, anchor="w", stretch=True)
            else:
                self.tree_prod.column(col, width=100, anchor="center")
        
        self.tree_prod.pack(fill="both", expand=True, padx=(10, 0), pady=(0, 10), side="left")
        scrollbar.pack(side="right", fill="y", pady=(0, 10))
        
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
            if col == "Product Name":
                 self.tree_sales.column(col, width=200, anchor="w")
            else:
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
            
            if price < 0 or stock < 0:
                 raise ValueError("Values cannot be negative.")
                
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO Products (name, category, price, stock_quantity) VALUES (?, ?, ?, ?)",
                           (name, category, price, stock))
            self.conn.commit()
            
            self.ent_name.delete(0, tk.END)
            self.ent_category.delete(0, tk.END)
            self.ent_price.delete(0, tk.END)
            self.ent_stock.delete(0, tk.END)
            
            self.ent_search.delete(0, tk.END)
            self.refresh_products()
            messagebox.showinfo("Success", f"Product '{name}' added successfully!")
            
        except ValueError as e:
            msg = "Please ensure Price and Stock are valid, positive numbers."
            if "negative" in str(e):
                msg = str(e)
            messagebox.showerror("Input Error", msg)

    def record_sale(self):
        try:
            prod_id_str = self.ent_sale_id.get().strip()
            qty_sold_str = self.ent_sale_qty.get().strip()
            
            if not prod_id_str or not qty_sold_str:
                 messagebox.showerror("Input Error", "Product ID and Quantity Sold are required.")
                 return

            prod_id = int(prod_id_str)
            qty_sold = int(qty_sold_str)
            
            if qty_sold <= 0:
                messagebox.showerror("Input Error", "Quantity sold must be at least 1.")
                return

            cursor = self.conn.cursor()
            cursor.execute("SELECT name, price, stock_quantity FROM Products WHERE product_id = ?", (prod_id,))
            product = cursor.fetchone()
            
            if product is None:
                messagebox.showerror("Error", f"Product ID {prod_id} not found.")
                return
                
            name, price, current_stock = product
            
            if qty_sold > current_stock:
                messagebox.showerror("Stock Error", f"Insufficient stock! Only {current_stock} units left for {name}.")
                return
                
            total_price = price * qty_sold
            sale_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            try:
                cursor.execute("INSERT INTO Sales (product_id, quantity_sold, total_price, sale_date) VALUES (?, ?, ?, ?)",
                               (prod_id, qty_sold, total_price, sale_date))
                cursor.execute("UPDATE Products SET stock_quantity = stock_quantity - ? WHERE product_id = ?",
                               (qty_sold, prod_id))
                self.conn.commit()
                
                self.ent_sale_id.delete(0, tk.END)
                self.ent_sale_qty.delete(0, tk.END)
                
                new_stock = current_stock - qty_sold
                low_stock_msg = f"\n⚠️ Warning: {name} is now low in stock ({new_stock} units)." if new_stock < 5 else ""

                self.refresh_products()
                self.refresh_sales()
                messagebox.showinfo("Sale Successful", f"Sold {qty_sold}x {name}.\nTotal: ₱{total_price:.2f}.{low_stock_msg}")

            except sqlite3.Error as e:
                self.conn.rollback() 
                messagebox.showerror("Database Error", f"Transaction failed: {e}")

        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numerical values for ID and Quantity.")

    def search_products(self, event=None):
        search_query = self.ent_search.get().strip()
        if not search_query:
            self.refresh_products()
            return

        for row in self.tree_prod.get_children():
            self.tree_prod.delete(row)
            
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM Products WHERE name LIKE ?", ('%' + search_query + '%',))
        for row in cursor.fetchall():
            formatted_row = (row[0], row[1], row[2], f"₱{row[3]:.2f}", row[4])
            self.tree_prod.insert("", tk.END, values=formatted_row)
            
    def clear_search(self):
        self.ent_search.delete(0, tk.END)
        self.refresh_products()

    def delete_product(self):
        selected_item = self.tree_prod.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a product from the list to delete.")
            return

        product_values = self.tree_prod.item(selected_item)['values']
        product_id = product_values[0]
        product_name = product_values[1]

        confirm = messagebox.askyesno("Confirm Deletion", 
                                       f"Are you sure you want to delete '{product_name}'?\n\n"
                                       f"This will also delete ALL related sales records permanently!")
        if confirm:
            try:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM Products WHERE product_id = ?", (product_id,))
                self.conn.commit()
                
                self.ent_search.delete(0, tk.END)
                self.refresh_products()
                self.refresh_sales()
                messagebox.showinfo("Deleted", f"Product '{product_name}' and its sales history were successfully deleted.")
                
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"An error occurred during deletion: {e}")

    def refresh_products(self):
        for row in self.tree_prod.get_children():
            self.tree_prod.delete(row)
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM Products")
        for row in cursor.fetchall():
            formatted_row = (row[0], row[1], row[2], f"₱{row[3]:.2f}", row[4])
            self.tree_prod.insert("", tk.END, values=formatted_row)

    def refresh_sales(self):
        for row in self.tree_sales.get_children():
            self.tree_sales.delete(row)
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT s.sale_id, p.name, s.quantity_sold, s.total_price, s.sale_date 
            FROM Sales s JOIN Products p ON s.product_id = p.product_id
        ''')
        for row in cursor.fetchall():
            formatted_row = (row[0], row[1], row[2], f"₱{row[3]:.2f}", row[4])
            self.tree_sales.insert("", tk.END, values=formatted_row)

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use('clam')
    
    app = InventoryApp(root)
    root.mainloop()