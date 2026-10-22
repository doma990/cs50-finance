import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from time import ctime

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
# Stocks user owns
def index():
    """Show portfolio of stocks"""
    # Name and cash
    user = db.execute("SELECT username, cash FROM users WHERE id = ?", session["user_id"])

    # Stocks and number of shares
    stocks = db.execute("SELECT symbol, shares FROM shares_owned WHERE person_id = ?", session["user_id"])

    # Preparing list
    meow = []
    # Total price
    oo = 0

    # stock = {"symbol": "", "shares": ""}
    for stock in stocks:
        # Getting stock information
        # stockInfo = {"name": "", "price": "", "symbol": ""}
        stockInfo = lookup(stock["symbol"])

        # Appending dictionary
        meow.append({
            "symbol": stockInfo['symbol'],
            "name": stockInfo['name'],
            "shares": stock['shares'],
            "price": stockInfo['price'],
            "total": stock['shares'] * stockInfo['price']
        })

        oo += stock['shares'] * stockInfo['price']

    return render_template("index.html", name=user[0]["username"], cash=user[0]["cash"], stocks=meow, oo=oo)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    # Load portofolio
    if request.method == "POST":

        # User requested from index
        if request.form.get("index"):
            return render_template("buy.html", symbol=request.form["index"])

        # Ensuring that symbol is valid
        if not request.form.get("symbol") or not lookup(request.form["symbol"]):
            return apology("Invalid symbol!")

        # Symbol is valid
        stock = lookup(request.form["symbol"])

        # Ensuring that shares exist
        if not request.form.get("shares"):
            return apology("Number of shares!")

        # Ensuring that shares is int
        shares = request.form["shares"]
        if not shares.isdigit():
            return apology("Only integers are allowed!")

        # Convereting from str to int
        shares = int(shares)

        # Cash is returned if valid, otherwise None is returned
        total_price = shares * stock["price"]
        cash = valid_shares(total_price)

        # Can't afford
        if not cash:
            return apology("Can't afford!")

        # Completing purchase
        # Updating cash amount for user
        db.execute("UPDATE users SET cash = ? WHERE id = ?", cash - total_price, session["user_id"])

        # Saving transaction
        db.execute("INSERT INTO transactions (company, symbol, quote, shares, total, person_id, date_time) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   stock["name"], stock["symbol"], stock["price"], shares, total_price, session["user_id"], ctime())

        # Remembring number of shares of this symbol for this user
        alreadyExists = db.execute("SELECT shares FROM shares_owned WHERE person_id = ? AND symbol = ?",
                                   session["user_id"], stock["symbol"])

        # If user has previous shares for this stock
        if alreadyExists:

            # Update user's shares for this stock
            db.execute("UPDATE shares_owned SET shares = ? WHERE person_id = ? AND symbol = ?",
                       shares + alreadyExists[0]["shares"], session["user_id"], stock["symbol"])

        # If user doesn't have any shares for this stock
        else:

            # Add new column
            db.execute("INSERT INTO shares_owned (person_id, symbol, shares) VALUES (?,?,?)",
                       session["user_id"], stock["symbol"], shares)

        # Done
        return redirect("/")

    # Load form
    return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    tsts = db.execute("SELECT * FROM transactions WHERE person_id = ?", session["user_id"])
    return render_template("history.html", tsts=tsts)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Reset password
        if request.form.get("reset"):
            return redirect("/reset_pass")

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/reset_pass", methods=["GET", "POST"])
@login_required
def reset_password():

    # User submitted the form
    if request.method == "POST":
        # Fields are left blank
        if not request.form.get("new_pass") or not request.form.get("confirmation"):
            return render_template("resetpass.html", alert="Please fill all the fields!")

        # Fields are not matched
        if request.form["new_pass"] != request.form["confirmation"]:
            return render_template("resetpass.html", alert="Passwords not matched!")

        # All things are ok
        db.execute("UPDATE users SET hash = ? WHERE id = ?",
                   generate_password_hash(request.form["new_pass"], method='pbkdf2:sha256', salt_length=8),
                   session["user_id"])

        # Log out
        return redirect("/logout")

    # Loading form
    return render_template("resetpass.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    # Load quoted
    if request.method == "POST":
        # Stock quote
        info = lookup(request.form.get("symbol"))

        # Checking validity
        if not info:
            return apology("Invalid quote name!")

        # Formating share price
        info["price"] = usd(info["price"])

        # Rendering quote info
        return render_template("quoted.html", info=info)

    # Load form
    return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User previously registered
    if request.method == "POST":

        # Ensuring name is valid
        if not request.form.get("username") or not check_db(request.form["username"]):
            return apology("Invalid username!")

        # Ensuring password is valid
        if not request.form.get("password") or not request.form.get("confirmation"):
            return apology("Please fill all fields!")

        if request.form["password"] != request.form["confirmation"]:
            return apology("Passwords are not matched!")

        # Ensuring that password satisfies the conditions
        if not formula(request.form["password"]):
            return render_template("register.html", alert="Password must include at least one number, one symbol (e.g. '#' .. '&') and of length 5")

        # Registering user
        session["user_id"] = db.execute("INSERT INTO users (username, hash) VALUES (?, ?)",
                                        # Username
                                        request.form["username"],
                                        # Hashed password
                                        generate_password_hash(request.form["password"], method='pbkdf2:sha256', salt_length=8))

        # Success!
        return redirect("/")

    # First time
    return render_template("register.html")


@app.route("/addmoney", methods=["GET", "POST"])
@login_required
def addMoney():
    # User submitted the form
    if request.method == "POST":

        # Validity
        if not request.form.get("cash") or int(request.form["cash"]) < 1:
            return render_template("add_money.html", alert="Invalid cash!")

        # Adding cash
        db.execute("UPDATE users SET cash = ? WHERE id = ?",
                   db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"] + int(request.form["cash"]),
                   session["user_id"])

        # Success!
        return redirect("/")

    return render_template("add_money.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # User submitted the form
    if request.method == "POST":

        # User requested via index
        if request.form.get("index"):
            return render_template("sell.html", symbol=request.form["index"])

        # If inputs are not valid
        if not request.form.get("symbol") or not lookup(request.form["symbol"]) or not request.form.get("shares"):
            return apology("Invalid stock name and/or Number of shares!")

        # Converting from str to int
        shares = int(request.form["shares"])

        # Getting number of shares
        shares_in = db.execute("SELECT shares FROM shares_owned WHERE person_id = ? AND symbol = ?",
                               session["user_id"], request.form["symbol"])

        shares_in = shares_in[0]["shares"]

        # If user doesn't have stocks already
        if shares_in == 0:
            return apology("You don't have any shares for this stock!")

        # Check if number of shares inputed is valid
        if shares > shares_in:
            return apology("Invalid number of shares!")

        # All things are OK
        # Getting stock info
        stock_info = lookup(request.form["symbol"])

        # Saving transaction
        db.execute("INSERT INTO transactions (company, symbol, quote, shares, total, person_id, date_time, trans_type) VALUES (?,?,?,?,?,?,?,?)",
                   # Company name and stock symbol and stock price
                   stock_info["name"], stock_info["symbol"], stock_info["price"],
                   # Number of shares and total cash and person id
                   shares, stock_info["price"] * shares, session["user_id"],
                   # Current date and transaction type
                   ctime(), "SELL")

        # Getting current cash
        cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        cash = cash[0]["cash"]

        # Adding money
        cash += shares * stock_info["price"]

        # Saving user's cash
        db.execute("UPDATE users SET cash = ? WHERE id = ?", cash, session["user_id"])

        # Editing number of shares
        db.execute("UPDATE shares_owned SET shares = ? WHERE person_id = ? AND symbol = ?",
                   shares_in - shares, session["user_id"], stock_info["symbol"])

        # Success!
        return redirect("/")

    # Getting owned stocks
    symbols = db.execute("SELECT symbol FROM shares_owned WHERE person_id = ?", session["user_id"])

    # Loading form
    return render_template("sell.html", symbols=symbols)


# Returns True if no similar usernames, otherwise False
def check_db(word):
    # Looking for similar usernames
    data = db.execute("SELECT * FROM users WHERE username = ?", word)

    # No matched usernames
    if not data:
        return True

    # There's matched usernames
    return False


# Password formula
# Returns true if the password mathces the formula, otherwise false
def formula(password):
    # Checking length
    if len(password) < 5:
        return False

    # Preparing lists
    numbers = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
    symbols = ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '_', '+', '=', ';', ':', '[', ']', '{', '}']

    # Initializing
    num = False
    symbol = False

    # Check for numbers
    for i in numbers:
        # Password includes a number
        if i in password:
            num = True
            break

    # Password doesn't include a number
    if not num:
        return False

    # Check for symbols
    for i in symbols:
        # Password includes a symbol
        if i in password:
            return True

    # Password doesn't match the formula
    return False


# Product is the total cash for number of shares with certain price


def valid_shares(Product):
    # Getting cash amount
    cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
    cash = cash[0]["cash"]

    # Failure
    if Product > cash:
        return None

    # Success
    return cash

