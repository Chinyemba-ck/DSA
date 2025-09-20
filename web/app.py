from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import csv
import datetime
import os
from typing import List, Dict, Optional

app = Flask(__name__)
app.secret_key = 'walmart-shopping-system-secret-key-2025'

class ShoppingItem:
    TAX_RATE = 0.1044  # 10.44% tax rate

    def __init__(self, name: str, price: float, quantity: int = 1):
        self.name = name
        self.price = price
        self.quantity = quantity

    def get_subtotal(self) -> float:
        return self.price * self.quantity

    def get_tax(self) -> float:
        return self.get_subtotal() * self.TAX_RATE

    def get_total(self) -> float:
        return self.get_subtotal() + self.get_tax()

    def to_dict(self):
        return {
            'name': self.name,
            'price': self.price,
            'quantity': self.quantity,
            'subtotal': self.get_subtotal(),
            'tax': self.get_tax(),
            'total': self.get_total()
        }

class TransactionManager:
    def __init__(self, filename: str = "transactions.csv"):
        self.filename = filename
        self.init_database()

    def init_database(self):
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['Transaction_ID', 'Date', 'Time', 'Item_Name', 'Price', 'Quantity', 'Subtotal', 'Tax', 'Total'])

    def save_transaction(self, cart_items: List[ShoppingItem], transaction_total: float) -> str:
        transaction_id = f"TXN_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        current_date = datetime.date.today().strftime('%Y-%m-%d')
        current_time = datetime.datetime.now().strftime('%H:%M:%S')

        with open(self.filename, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            for item in cart_items:
                writer.writerow([
                    transaction_id,
                    current_date,
                    current_time,
                    item.name,
                    f"{item.price:.2f}",
                    item.quantity,
                    f"{item.get_subtotal():.2f}",
                    f"{item.get_tax():.2f}",
                    f"{item.get_total():.2f}"
                ])

        return transaction_id

    def get_all_transactions(self) -> List[Dict]:
        transactions = []
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    transactions.append(row)
        return transactions

    def get_transaction_by_id(self, transaction_id: str) -> List[Dict]:
        transactions = []
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['Transaction_ID'] == transaction_id:
                        transactions.append(row)
        return transactions

    def delete_transaction(self, transaction_id: str) -> bool:
        if not os.path.exists(self.filename):
            return False

        all_transactions = []
        with open(self.filename, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames
            for row in reader:
                if row['Transaction_ID'] != transaction_id:
                    all_transactions.append(row)

        with open(self.filename, 'w', newline='', encoding='utf-8') as file:
            if fieldnames:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_transactions)

        return True

class ShoppingCart:
    def __init__(self):
        self.items = []
        self.transaction_manager = TransactionManager()

    def add_item(self, item: ShoppingItem):
        existing_item = self.find_item(item.name)
        if existing_item:
            existing_item.quantity += item.quantity
        else:
            self.items.append(item)

    def remove_item(self, item_name: str) -> bool:
        for i, item in enumerate(self.items):
            if item.name.lower() == item_name.lower():
                del self.items[i]
                return True
        return False

    def update_item_quantity(self, item_name: str, new_quantity: int) -> bool:
        item = self.find_item(item_name)
        if item:
            if new_quantity <= 0:
                return self.remove_item(item_name)
            else:
                item.quantity = new_quantity
                return True
        return False

    def find_item(self, item_name: str) -> Optional[ShoppingItem]:
        for item in self.items:
            if item.name.lower() == item_name.lower():
                return item
        return None

    def get_total(self) -> float:
        return sum(item.get_total() for item in self.items)

    def get_subtotal(self) -> float:
        return sum(item.get_subtotal() for item in self.items)

    def get_tax(self) -> float:
        return sum(item.get_tax() for item in self.items)

    def clear_cart(self):
        self.items.clear()

    def complete_transaction(self) -> str:
        if not self.items:
            raise ValueError("Cart is empty")

        transaction_id = self.transaction_manager.save_transaction(
            self.items, self.get_total()
        )
        self.clear_cart()
        return transaction_id

# Global transaction manager instance (this can be shared)
transaction_manager = TransactionManager()

def get_cart():
    """Get the cart instance for the current session"""
    if 'cart_items' not in session:
        session['cart_items'] = []

    # Create a temporary cart and populate it with session data
    cart = ShoppingCart()
    cart.transaction_manager = transaction_manager

    # Reconstruct cart items from session
    for item_data in session['cart_items']:
        item = ShoppingItem(
            name=item_data['name'],
            price=item_data['price'],
            quantity=item_data['quantity']
        )
        cart.items.append(item)

    return cart

def save_cart(cart):
    """Save the cart to the session"""
    session['cart_items'] = [item.to_dict() for item in cart.items]
    session.modified = True

@app.route('/')
def index():
    cart = get_cart()
    return render_template('index.html', cart_items=[item.to_dict() for item in cart.items],
                         cart_total=cart.get_total(), cart_subtotal=cart.get_subtotal(),
                         cart_tax=cart.get_tax())

@app.route('/add_item', methods=['POST'])
def add_item():
    try:
        name = request.form.get('name', '').strip()
        price_str = request.form.get('price', '').strip()
        quantity_str = request.form.get('quantity', '').strip()

        # Validate item name
        if not name:
            flash('Please enter an item name', 'error')
            return redirect(url_for('index'))

        if len(name) > 100:
            flash('Item name must be 100 characters or less', 'error')
            return redirect(url_for('index'))

        # Validate price
        if not price_str:
            flash('Please enter a price', 'error')
            return redirect(url_for('index'))

        try:
            price = float(price_str)
        except ValueError:
            flash('Please enter a valid price (numbers only)', 'error')
            return redirect(url_for('index'))

        if price <= 0:
            flash('Price must be greater than 0', 'error')
            return redirect(url_for('index'))

        if price > 999999.99:
            flash('Price must be less than $1,000,000', 'error')
            return redirect(url_for('index'))

        # Validate quantity
        if not quantity_str:
            flash('Please enter a quantity', 'error')
            return redirect(url_for('index'))

        try:
            quantity = int(quantity_str)
        except ValueError:
            flash('Please enter a valid quantity (whole numbers only)', 'error')
            return redirect(url_for('index'))

        if quantity <= 0:
            flash('Quantity must be greater than 0', 'error')
            return redirect(url_for('index'))

        if quantity > 1000:
            flash('Quantity must be 1000 or less', 'error')
            return redirect(url_for('index'))

        cart = get_cart()
        item = ShoppingItem(name, price, quantity)
        cart.add_item(item)
        save_cart(cart)
        flash(f'Added {quantity} x {name} to cart', 'success')

    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')

    return redirect(url_for('index'))

@app.route('/remove_item/<item_name>')
def remove_item(item_name):
    try:
        # Validate item name
        if not item_name or not item_name.strip():
            flash('Invalid item name', 'error')
            return redirect(url_for('index'))

        item_name = item_name.strip()

        cart = get_cart()
        if cart.remove_item(item_name):
            save_cart(cart)
            flash(f'Removed {item_name} from cart', 'success')
        else:
            flash('Item not found in cart', 'error')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')

    return redirect(url_for('index'))

@app.route('/update_quantity', methods=['POST'])
def update_quantity():
    try:
        item_name = request.form.get('item_name', '').strip()
        new_quantity_str = request.form.get('new_quantity', '').strip()

        # Validate item name
        if not item_name:
            flash('Item name is required', 'error')
            return redirect(url_for('index'))

        # Validate quantity
        if not new_quantity_str:
            flash('Please enter a quantity', 'error')
            return redirect(url_for('index'))

        try:
            new_quantity = int(new_quantity_str)
        except ValueError:
            flash('Please enter a valid quantity (whole numbers only)', 'error')
            return redirect(url_for('index'))

        if new_quantity < 0:
            flash('Quantity cannot be negative', 'error')
            return redirect(url_for('index'))

        if new_quantity > 1000:
            flash('Quantity must be 1000 or less', 'error')
            return redirect(url_for('index'))

        cart = get_cart()
        if cart.update_item_quantity(item_name, new_quantity):
            save_cart(cart)
            if new_quantity == 0:
                flash(f'Removed {item_name} from cart', 'success')
            else:
                flash(f'Updated {item_name} quantity to {new_quantity}', 'success')
        else:
            flash('Item not found in cart', 'error')

    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')

    return redirect(url_for('index'))

@app.route('/clear_cart')
def clear_cart_route():
    cart = get_cart()
    cart.clear_cart()
    save_cart(cart)
    flash('Cart cleared', 'success')
    return redirect(url_for('index'))

@app.route('/checkout', methods=['POST'])
def checkout():
    cart = get_cart()
    if not cart.items:
        flash('Cart is empty', 'error')
        return redirect(url_for('index'))

    try:
        transaction_id = cart.complete_transaction()
        save_cart(cart)  # Cart should be empty after transaction
        flash(f'Transaction completed! Transaction ID: {transaction_id}', 'success')
    except Exception as e:
        flash(f'Failed to complete transaction: {str(e)}', 'error')

    return redirect(url_for('index'))

@app.route('/receipts')
def receipts():
    transactions = transaction_manager.get_all_transactions()

    # Group transactions by ID and calculate totals
    unique_transactions = {}
    transaction_totals = {}

    for transaction in transactions:
        tid = transaction['Transaction_ID']
        if tid not in unique_transactions:
            unique_transactions[tid] = transaction
            transaction_totals[tid] = 0.0

        transaction_totals[tid] += float(transaction['Total'])

    # Convert to list for template
    transaction_list = []
    for tid, transaction in unique_transactions.items():
        transaction_list.append({
            'id': transaction['Transaction_ID'],
            'date': transaction['Date'],
            'time': transaction['Time'],
            'total': transaction_totals[tid]
        })

    return render_template('receipts.html', transactions=transaction_list)

@app.route('/receipt/<transaction_id>')
def view_receipt(transaction_id):
    try:
        # Validate transaction ID
        if not transaction_id or not transaction_id.strip():
            flash('Invalid transaction ID', 'error')
            return redirect(url_for('receipts'))

        transaction_id = transaction_id.strip()

        # Basic format validation for transaction ID
        if not transaction_id.startswith('TXN_'):
            flash('Invalid transaction ID format', 'error')
            return redirect(url_for('receipts'))

        transactions = transaction_manager.get_transaction_by_id(transaction_id)
        if not transactions:
            flash('Transaction not found', 'error')
            return redirect(url_for('receipts'))

        receipt_data = generate_receipt_data(transactions)
        if not receipt_data:
            flash('Unable to generate receipt data', 'error')
            return redirect(url_for('receipts'))

        return render_template('receipt.html', receipt=receipt_data, transaction_id=transaction_id)

    except Exception as e:
        flash(f'An error occurred while viewing receipt: {str(e)}', 'error')
        return redirect(url_for('receipts'))

@app.route('/delete_transaction/<transaction_id>')
def delete_transaction(transaction_id):
    try:
        # Validate transaction ID
        if not transaction_id or not transaction_id.strip():
            flash('Invalid transaction ID', 'error')
            return redirect(url_for('receipts'))

        transaction_id = transaction_id.strip()

        # Basic format validation for transaction ID
        if not transaction_id.startswith('TXN_'):
            flash('Invalid transaction ID format', 'error')
            return redirect(url_for('receipts'))

        if transaction_manager.delete_transaction(transaction_id):
            flash('Transaction deleted successfully', 'success')
        else:
            flash('Failed to delete transaction or transaction not found', 'error')

    except Exception as e:
        flash(f'An error occurred while deleting transaction: {str(e)}', 'error')

    return redirect(url_for('receipts'))

def generate_receipt_data(transactions):
    if not transactions:
        return None

    first_transaction = transactions[0]
    receipt_items = []
    subtotal = 0
    total_tax = 0
    grand_total = 0

    for transaction in transactions:
        item_subtotal = float(transaction['Subtotal'])
        item_tax = float(transaction['Tax'])
        item_total = float(transaction['Total'])

        subtotal += item_subtotal
        total_tax += item_tax
        grand_total += item_total

        receipt_items.append({
            'name': transaction['Item_Name'],
            'price': float(transaction['Price']),
            'quantity': int(transaction['Quantity']),
            'subtotal': item_subtotal,
            'tax': item_tax,
            'total': item_total
        })

    return {
        'transaction_id': first_transaction['Transaction_ID'],
        'date': first_transaction['Date'],
        'time': first_transaction['Time'],
        'receipt_items': receipt_items,
        'subtotal': subtotal,
        'tax': total_tax,
        'total': grand_total
    }

if __name__ == '__main__':
    app.run(debug=True, port=5001)