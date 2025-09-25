"""OpenAQ Air Quality Dashboard with Flask."""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from openaq import OpenAQ   # from py-openaq / openaq package

app = Flask(__name__)

# ---------- Part 3: Database setup ----------
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
DB = SQLAlchemy(app)

class Record(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True)
    datetime = DB.Column(DB.String, nullable=False)   # store UTC datetime as string
    value = DB.Column(DB.Float, nullable=False)       # PM2.5 value

    def __repr__(self):
        return f"< Time {self.datetime} --- Value {self.value} >"

# ---------- Part 2: OpenAQ helper ----------
def get_results():
    """
    Call OpenAQ measurements endpoint for parameter='pm25'
    and return a list of (utc_datetime_string, value) tuples.
    """
    api = OpenAQ()
    status, body = api.measurements(parameter="pm25")
    if status != 200 or not body:
        return []

    results = body.get("results", [])
    tuples = []
    for item in results:
        # date -> { 'utc': ..., 'local': ... }
        utc = item.get("date", {}).get("utc")
        val = item.get("value")
        if utc is None or val is None:
            continue
        tuples.append((utc, val))
    return tuples

# ---------- Part 1 / 4: Routes ----------
@app.route("/")
def root():
    """Return a stringified list of records with value >= 10 from DB."""
    risky = Record.query.filter(Record.value >= 10).all()
    # convert to list of tuples for clearer display
    display = [(r.datetime, r.value) for r in risky]
    return str(display)

@app.route("/refresh")
def refresh():
    """
    Drop & recreate the DB, fetch fresh measurements from OpenAQ,
    insert them as Record objects, then return the root() view.
    """
    DB.drop_all()
    DB.create_all()

    data = get_results()
    for dt, val in data:
        rec = Record(datetime=dt, value=val)
        DB.session.add(rec)

    DB.session.commit()
    return root()

if __name__ == "__main__":
    # optional: run with python aq_dashboard.py
    app.run(debug=True)
