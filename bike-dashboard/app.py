from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bikes.db'
db = SQLAlchemy(app)

# Predefined list of bike numbers
BIKES = [f'Bike {i}' for i in range(1, 21)]  # Adjust the number as needed

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    bike = db.Column(db.String(50), nullable=False)

# Create the database tables before the app starts running
with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form.get('name')
        bike = request.form.get('bike')
        
        if name and bike:
            new_reservation = Reservation(name=name, bike=bike)
            db.session.add(new_reservation)
            db.session.commit()
            return redirect(url_for('index'))
        
    reservations = Reservation.query.all()
    return render_template('index.html', bikes=BIKES, reservations=reservations)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)
