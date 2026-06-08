from flask import Flask, render_template, request, redirect

app = Flask(__name__)

expenses = []

@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":

        expense = {
            "date": request.form["date"],
            "category": request.form["category"],
            "description": request.form["description"],
            "amount": float(request.form["amount"])
        }

        expenses.append(expense)

        return redirect("/")

    total = sum(exp["amount"] for exp in expenses)

    return render_template(
        "index.html",
        expenses=expenses,
        total=total
    )

@app.route("/delete/<int:index>")
def delete(index):

    if 0 <= index < len(expenses):
        expenses.pop(index)

    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)