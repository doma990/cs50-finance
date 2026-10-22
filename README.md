# CS50 Finance

A stock-trading simulator built with **Python, Flask, SQLite, and Jinja**, completed in December 2022–January 2023 for CS50's Finance problem set.

Users manage a virtual portfolio: look up a stock, buy and sell shares with simulated cash, and review their transaction history. New accounts start with **$10,000 in virtual cash**.

[Project walkthrough](https://doma990.github.io/projects/cs50-finance/) · [Original 2022 assignment](https://cs50.harvard.edu/college/2022/fall/psets/9/finance/)

## What I implemented

Built on CS50's supplied Flask skeleton, authentication helpers, and base templates:

- **Registration:** unique usernames, confirmed passwords, and stored password hashes.
- **Quotes:** a form for looking up a stock symbol through the original IEX integration.
- **Buying and selling:** update cash and holdings, and record each trade with its price and time.
- **Portfolio:** display owned stocks, share quantities, quoted prices, holding values, available cash, and the total value of the stock holdings.
- **History:** a table of the signed-in user's purchases and sales.

### Personal touches

My submission also includes four extensions:

- Change a password after signing in.
- Add simulated cash to an account.
- Start a buy or sell action directly from a portfolio row, with the symbol prefilled.
- Require a password of at least five characters, including a digit and a symbol from the application's allowed set.

## How the application is designed

### Flask routes and sessions

[`app.py`](app.py) handles GET requests to display forms and POST requests to process them. Protected routes use `login_required` from [`helpers.py`](helpers.py). A filesystem-backed session remembers the signed-in user's ID; database queries use that ID to select the user's records.

A trade follows this flow:

**Form → route → stock lookup → cash/holding checks → SQLite updates → redirect to portfolio.**

The original code uses parameterized SQL queries and Werkzeug's password hashing. This is an early learning project; its input validation and multi-step trade updates would need further work for a production application.

### Relational data model

| Table | Stores |
| --- | --- |
| `users` | Username, password hash, and simulated cash balance. |
| `shares_owned` | A user's current share quantity for each stock symbol. |
| `transactions` | Trade type, company, symbol, price, quantity, total, user, and timestamp. |

Current holdings and transaction history are stored separately: one represents the current portfolio, while the other records past activity. See [`schema.sql`](schema.sql).

### Jinja and Bootstrap

[`templates/layout.html`](templates/layout.html) provides the shared navigation and page structure. Other Jinja templates extend it to render forms, portfolio rows, quotes, and trade history. Bootstrap supplies the responsive navigation and tables; the `usd` filter formats currency values.

## Reference image

![CS50 staff example of the Finance portfolio interface](https://cs50.harvard.edu/college/2022/fall/psets/9/finance/finance.png)

*Reference image from the [CS50 2022 Finance specification](https://cs50.harvard.edu/college/2022/fall/psets/9/finance/), courtesy of CS50 / Harvard University. This is the assignment's example interface, not a screenshot of my implementation.*

## Running the original version

**This is a historical source snapshot.** The original quote integration uses IEX Cloud, which has been retired. Live quote, trading, and stock valuation features need a replacement implementation of `lookup(symbol)` in `helpers.py`. It must return a dictionary with `name`, `price`, and `symbol`, or `None` for an invalid symbol.

With Python installed, open a terminal in this repository and install the dependencies:

```sh
python -m pip install -r requirements.txt
```

The original app also checks for an `API_KEY` environment variable at startup. After adapting the quote integration and setting its configuration:

**Windows PowerShell**

```powershell
$env:API_KEY = "your-provider-key"
python -m flask --app app run
```

**macOS / Linux**

```sh
export API_KEY="your-provider-key"
python -m flask --app app run
```

Open the local URL Flask prints. Setting a key alone does not restore the retired IEX service.

The supplied `finance.db` contains an **empty database with the original schema**. It includes no accounts, password hashes, transaction records, or saved sessions from my submission. To recreate a missing database from `schema.sql`:

```sh
python -c "import sqlite3; from pathlib import Path; db = sqlite3.connect('finance.db'); db.executescript(Path('schema.sql').read_text()); db.close()"
```

## Project origin

The application source and templates were imported from my original CS50 submission. The course-managed `me50/doma990` repository remains separate and private; this repository provides a public, documented copy for portfolio visitors. Its import date is not the date the project was originally written.

The project specification, distribution code, and reference image are credited to **CS50 / Harvard University**. My contribution is the completed application behavior and personal extensions described above. This is an educational simulation using virtual money.
