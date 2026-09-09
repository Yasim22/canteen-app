import os
from functools import wraps
from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash)
from models import db, MenuItem, Order, OrderItem
from sms import send_sms, normalize_phone


def seed_menu():
    if MenuItem.query.count() == 0:
        db.session.add_all([
            MenuItem(name="Jollof Rice & Chicken", price=35.0),
            MenuItem(name="Waakye Special", price=25.0),
            MenuItem(name="Fried Rice & Egg", price=28.0),
            MenuItem(name="Kenkey & Fish", price=20.0),
            MenuItem(name="Sobolo (500ml)", price=8.0),
        ])
        db.session.commit()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret-change-me"),
        SQLALCHEMY_DATABASE_URI="sqlite:///canteen.db",
        STAFF_PASSWORD=os.getenv("STAFF_PASSWORD", "staff123"),
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    with app.app_context():
        db.create_all()
        seed_menu()

    def staff_required(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not session.get("staff"):
                return redirect(url_for("staff_login"))
            return f(*args, **kwargs)
        return wrapper

    # ---------- Feature 1: browse menu ----------
    @app.route("/")
    def menu():
        items = MenuItem.query.filter_by(available=True).all()
        return render_template("menu.html", items=items)

    # ---------- Feature 2: place order ----------
    @app.route("/order", methods=["POST"])
    def place_order():
        name = request.form.get("customer_name", "").strip()
        phone = normalize_phone(request.form.get("phone", ""))
        if not name or len(phone) < 10:
            flash("Please enter your name and a valid phone number.")
            return redirect(url_for("menu"))

        order = Order(customer_name=name, phone=phone)
        for item in MenuItem.query.filter_by(available=True):
            try:
                qty = int(request.form.get(f"qty_{item.id}", 0))
            except ValueError:
                qty = 0
            if qty > 0:
                order.items.append(OrderItem(menu_item_id=item.id, qty=qty,
                                             unit_price=item.price))
        if not order.items:
            flash("Select at least one item.")
            return redirect(url_for("menu"))

        db.session.add(order)
        db.session.commit()
        send_sms(order.phone,
                 f"Hi {name}, order #{order.id} received. "
                 f"Total GHS {order.total:.2f}. We'll text you when it's ready.")
        return redirect(url_for("status", order_id=order.id))

    # ---------- Feature 3: track order ----------
    @app.route("/order/<int:order_id>")
    def status(order_id):
        order = db.get_or_404(Order, order_id)
        return render_template("status.html", order=order)

    # ---------- Feature 4: staff dashboard ----------
    @app.route("/staff/login", methods=["GET", "POST"])
    def staff_login():
        if request.method == "POST":
            if request.form.get("password") == app.config["STAFF_PASSWORD"]:
                session["staff"] = True
                return redirect(url_for("staff_dashboard"))
            flash("Wrong password.")
        return render_template("staff_login.html")

    @app.route("/staff")
    @staff_required
    def staff_dashboard():
        orders = (Order.query.filter(Order.status != "COLLECTED")
                  .order_by(Order.created_at).all())
        return render_template("staff.html", orders=orders)

    # ---------- Feature 5: SMS "ready" alert ----------
    @app.route("/staff/order/<int:order_id>/ready", methods=["POST"])
    @staff_required
    def mark_ready(order_id):
        order = db.get_or_404(Order, order_id)
        order.status = "READY"
        db.session.commit()
        send_sms(order.phone,
                 f"Hi {order.customer_name}, order #{order.id} is READY for pickup!")
        return redirect(url_for("staff_dashboard"))

    @app.route("/staff/order/<int:order_id>/collected", methods=["POST"])
    @staff_required
    def mark_collected(order_id):
        order = db.get_or_404(Order, order_id)
        order.status = "COLLECTED"
        db.session.commit()
        return redirect(url_for("staff_dashboard"))

    return app


if __name__ == "__main__":
    create_app().run(debug=True)