from flask import Flask, render_template, request, redirect
import json
import threading
from main import track_prices, load_products
from main import get_price, price_per_gram

app = Flask(__name__)

def save_products(products):
    with open("products.json", "w") as f:
        json.dump(products, f, indent=4)
@app.route("/edit", methods=["POST"])
def edit_product():
    index = int(request.form.get("index"))
    new_target = float(request.form.get("target_price"))

    products = load_products()

    if 0 <= index < len(products):
        products[index]["target_price"] = new_target

        with open("products.json", "w") as f:
            json.dump(products, f, indent=4)

    return redirect("/")


@app.route("/")
def index():
    products = load_products()

    enhanced_products = []

    for p in products:
        current_price = get_price(p["url"])

        ppg = None
        if current_price:
            ppg = price_per_gram(
                current_price,
                p.get("total_weight"),
                p.get("protein_percentage")
            )

        enhanced_products.append({
            **p,
            "current_price": current_price,
            "ppg": ppg
        })

    return render_template("index.html", products=enhanced_products)

@app.route("/add", methods=["POST"])
def add():
    product = {
        "url": request.form["url"],
        "name": request.form["name"],
        "target_price": float(request.form["price"]),
        "total_weight": float(request.form.get("weight") or 0),
        "protein_percentage": float(request.form.get("protein") or 0)
    }

    products = load_products()
    products.append(product)
    save_products(products)

    return redirect("/")

@app.route("/delete/<int:index>")
def delete(index):
    products = load_products()

    if index < len(products):
        products.pop(index)
        save_products(products)

    return redirect("/")

tracker_started = False

@app.route("/start")
def start():
    global tracker_started

    if not tracker_started:
        thread = threading.Thread(target=track_prices)
        thread.daemon = True
        thread.start()
        tracker_started = True

    return redirect("/")


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)