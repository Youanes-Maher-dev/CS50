import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


# Ensure transactions table is created if not already existing
def create_transactions_table():
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            shares INTEGER NOT NULL,
            price REAL NOT NULL,
            transacted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """
    )


create_transactions_table()


# After request to ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Route for portfolio of stocks
@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    stocks = db.execute(
        "SELECT symbol, SUM(shares) as total_shares FROM transactions WHERE user_id = :user_id GROUP BY symbol HAVING total_shares > 0",
        user_id=session["user_id"],
    )

    # Debugging output
    print(f"Stocks: {stocks}")

    cash = db.execute(
        "SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"]
    )[0]["cash"]

    total_value = cash
    grand_total = cash

    for stock in stocks:
        quote = lookup(stock["symbol"])
        if quote is None:
            return apology("symbol not found")

        print(f"Quote for {stock['symbol']}: {quote}")  # Debugging output

        stock["name"] = quote["name"]
        stock["price"] = quote["price"]
        stock["value"] = stock["price"] * stock["total_shares"]
        total_value += stock["value"]
        grand_total += stock["value"]

    return render_template(
        "index.html",
        stocks=stocks,
        cash=cash,
        total_value=total_value,
        grand_total=grand_total,
    )


# Route for buying shares
@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock THIRD"""
    if request.method == "POST":
        symbol = request.form.get("symbol").upper()
        shares = request.form.get("shares")
        if not symbol:
            return apology("must provide symbol")
        elif not shares or not shares.isdigit() or int(shares) <= 0:
            return apology("must provide a positive integer number of shares")

        quote = lookup(symbol)
        if quote is None:
            return apology("symbol not found")

        # Debugging output
        print(f"Quote for {symbol}: {quote}")

        if "name" not in quote:
            return apology(f"Missing 'name' in quote for {symbol}", 500)

        price = quote["price"]
        total_cost = int(shares) * price
        cash = db.execute(
            "SELECT cash FROM users WHERE id= :user_id", user_id=session["user_id"]
        )[0]["cash"]

        if cash < total_cost:
            return apology("not enough cash")

        # Update users table
        db.execute(
            "UPDATE users SET cash = cash - :total_cost WHERE id= :user_id",
            total_cost=total_cost,
            user_id=session["user_id"],
        )

        # Add the purchase to the history table
        db.execute(
            "INSERT INTO transactions (user_id, symbol, shares, price) VALUES (:user_id, :symbol, :shares, :price)",
            user_id=session["user_id"],
            symbol=symbol,
            shares=shares,
            price=price,
        )

        flash(f"Bought {shares} shares of {symbol} for {usd(total_cost)}!")
        return redirect("/")
    else:
        return render_template("buy.html")


# Route for viewing transaction history
@app.route("/history")
@login_required
def history():
    transactions = db.execute(
        "SELECT * FROM transactions WHERE user_id = :user_id ORDER BY transacted DESC",
        user_id=session["user_id"],
    )
    return render_template("history.html", transactions=transactions)


# Route for user login
@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        # Ensure username and password are provided
        if not request.form.get("username"):
            return apology("must provide username", 403)
        if not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Log user in
        session["user_id"] = rows[0]["id"]
        return redirect("/")
    else:
        return render_template("login.html")


# Route for user logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# Route for getting stock quotes
@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "POST":
        symbol = request.form.get("symbol")
        quote = lookup(symbol)
        if not quote:
            return apology("invalid symbol", 400)
        return render_template("quote.html", quote=quote)
    else:
        return render_template("quote.html")


# Route for user registration
@app.route("/register", methods=["GET", "POST"])
def register():
    session.clear()
    if request.method == "POST":
        # Ensure all fields are filled
        if not request.form.get("username"):
            return apology("must provide username", 400)
        if not request.form.get("password"):
            return apology("must provide password", 400)
        if not request.form.get("confirmation"):
            return apology("must confirm password", 400)
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 400)

        # Check if username exists
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )
        if len(rows) != 0:
            return apology("username already exists", 400)

        # Insert new user into the database
        db.execute(
            "INSERT INTO users (username, hash) VALUES (?, ?)",
            request.form.get("username"),
            generate_password_hash(request.form.get("password")),
        )
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )
        session["user_id"] = rows[0]["id"]

        return redirect("/")
    else:
        return render_template("register.html")


# Route for selling shares
@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    stocks = db.execute(
        "SELECT symbol, SUM(shares) AS total_shares FROM transactions WHERE user_id = :user_id GROUP BY symbol HAVING total_shares > 0",
        user_id=session["user_id"],
    )

    if request.method == "POST":
        symbol = request.form.get("symbol").upper()
        shares = request.form.get("shares")

        # Validate input
        if not symbol:
            return apology("must provide symbol")
        if not shares or not shares.isdigit() or int(shares) <= 0:
            return apology("must provide a positive integer number of shares")
        shares = int(shares)

        # Check if user owns the stock
        for stock in stocks:
            if stock["symbol"] == symbol:
                if stock["total_shares"] < shares:
                    return apology("not enough shares")

                # Process sale
                quote = lookup(symbol)
                if not quote:
                    return apology("symbol not found")
                price = quote["price"]
                total_sale = shares * price

                db.execute(
                    "UPDATE users SET cash = cash + :total_sale WHERE id = :user_id",
                    total_sale=total_sale,
                    user_id=session["user_id"],
                )
                db.execute(
                    "INSERT INTO transactions (user_id, symbol, shares, price) VALUES (:user_id, :symbol, :shares, :price)",
                    user_id=session["user_id"],
                    symbol=symbol,
                    shares=-shares,
                    price=price,
                )

                flash(f"Sold {shares} shares of {symbol} for {usd(total_sale)}!")
                return redirect("/")
        return apology("symbol not found")
    else:
        return render_template("sell.html", stocks=stocks)


# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
