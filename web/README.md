# Walmart Shopping System - Flask Web Application

A web-based shopping cart application built with Flask that replicates the functionality of the original Tkinter-based Walmart Shopping System.

## Features

- **Shopping Cart Management**
  - Add items with name, price, and quantity
  - Update item quantities
  - Remove items from cart
  - Clear entire cart
  - Real-time tax calculation (10.44% tax rate)

- **Transaction Processing**
  - Complete transactions with automatic ID generation
  - Save transaction data to CSV file
  - Calculate subtotals, tax, and totals

- **Receipt Management**
  - View all transaction history
  - Display detailed receipts for individual transactions
  - Print-friendly receipt format
  - Delete transactions

- **Web Interface**
  - Responsive Bootstrap design
  - Walmart-themed styling
  - Flash messages for user feedback
  - Mobile-friendly interface

## Installation

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**
   ```bash
   python app.py
   ```

3. **Access the Application**
   - Open your web browser and go to `http://localhost:5000`

## Usage

### Shopping Cart
1. Navigate to the main page
2. Add items by entering name, price, and quantity
3. View your cart with calculated taxes and totals
4. Update quantities or remove items as needed
5. Complete your transaction when ready

### View Receipts
1. Click on "Receipts" in the navigation
2. Browse all completed transactions
3. Click "View" to see detailed receipt
4. Print receipts or delete transactions as needed

## File Structure

```
web/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── templates/         # HTML templates
│   ├── base.html      # Base template with navigation
│   ├── index.html     # Shopping cart page
│   ├── receipts.html  # Transaction history
│   └── receipt.html   # Individual receipt view
└── transactions.csv   # Transaction data (auto-generated)
```

## Data Storage

Transaction data is stored in `transactions.csv` with the following columns:
- Transaction_ID
- Date
- Time
- Item_Name
- Price
- Quantity
- Subtotal
- Tax
- Total

## Customization

- **Tax Rate**: Modify `TAX_RATE` in the `ShoppingItem` class
- **Styling**: Update the CSS in `templates/base.html`
- **Database**: Replace CSV storage with a proper database by modifying `TransactionManager`

## Original System

This Flask application is based on the Tkinter-based `walmart_shopping_system.py` and maintains all core functionality while providing a modern web interface.