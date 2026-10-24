from flask import Flask, jsonify, request
from threading import Lock

app = Flask(__name__)
_lock = Lock()

CARS = [
    {"id": 1, "model": "E-Class", "price": 10000000, "stock": 10, "brand": "Mercedes-Benz"},
    {"id": 2, "model": "GLC Coupe", "price": 12000000, "stock": 5, "brand": "Mercedes-Benz"},
    {"id": 3, "model": "GLS", "price": 15000000, "stock": 3, "brand": "Mercedes-Benz"},
    {"id": 4, "model": "S-Class", "price": 16000000, "stock": 7, "brand": "Mercedes-Benz"},
    {"id": 5, "model": "G-Class AMG", "price": 25000000, "stock": 2, "brand": "Mercedes-Benz"},
    {"id": 6, "model": "GLE", "price": 20000000, "stock": 4, "brand": "Mercedes-Benz"},
    {"id": 7, "model": "V-Class", "price": 5000000, "stock": 8, "brand": "Mercedes-Benz"},
]

@app.get("/")
def index():
    return jsonify({"service": "AutoSalon API", "status": "ok"})

@app.get("/api/health")
def health():
    return jsonify({"status": "healthy"})

@app.get("/api/cars")
def list_cars():
    q = request.args.get("q", "").strip().lower()
    order = request.args.get("order", "asc")
    with _lock:
        result = [dict(car) for car in CARS if q in car["model"].lower()]
    result.sort(key=lambda car: car["price"], reverse=(order == "desc"))
    return jsonify({"count": len(result), "items": result})

@app.get("/api/cars/<int:car_id>")
def car_detail(car_id):
    car = next((dict(c) for c in CARS if c["id"] == car_id), None)
    if car is None:
        return jsonify({"error": "Car not found"}), 404
    return jsonify(car)

@app.get("/api/stats")
def stats():
    with _lock:
        return jsonify({
            "models": len(CARS),
            "total_stock": sum(c["stock"] for c in CARS),
            "min_price": min(c["price"] for c in CARS),
            "max_price": max(c["price"] for c in CARS),
        })

@app.post("/api/orders")
def create_order():
    data = request.get_json(silent=True) or {}
    car_id = data.get("car_id")
    quantity = data.get("quantity")
    customer = data.get("customer")
    if not isinstance(car_id, int) or not isinstance(quantity, int) or quantity < 1 or not isinstance(customer, dict):
        return jsonify({"error": "car_id, positive integer quantity and customer object are required"}), 400
    with _lock:
        car = next((c for c in CARS if c["id"] == car_id), None)
        if car is None:
            return jsonify({"error": "Car not found"}), 404
        if car["stock"] < quantity:
            return jsonify({"error": "Not enough stock", "available": car["stock"]}), 409
        car["stock"] -= quantity
        order = {"order_id": 100000 + car_id, "car_id": car_id, "quantity": quantity,
                 "total": car["price"] * quantity, "customer": customer}
    return jsonify(order), 201

@app.post("/api/feedback")
def feedback():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    message = data.get("message")
    rating = data.get("rating")
    if not isinstance(name, str) or not name.strip() or not isinstance(message, str) or not message.strip():
        return jsonify({"error": "name and message are required"}), 400
    if not isinstance(rating, int) or not 1 <= rating <= 5:
        return jsonify({"error": "rating must be an integer from 1 to 5"}), 400
    return jsonify({"accepted": True, "name": name, "rating": rating}), 201

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
