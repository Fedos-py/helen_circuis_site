from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import AnonymousUserMixin, UserMixin, LoginManager, login_user, current_user, logout_user, login_required
import os
from jinja2 import Template
import hashlib
import requests


from flask_forms import *
from private_info import *

file_path = os.path.abspath(os.getcwd())

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{file_path}/db/events.db'
app.config['SECRET_KEY'] = 'helen_secret_key'
login_manager = LoginManager(app)
db = SQLAlchemy(app)
payments_url = "https://securepay.tinkoff.ru/v2/Init"

@login_manager.user_loader
def load_user(email):
    return User.query.filter_by(email=email).first()

class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    locality = db.Column(db.Text)
    location = db.Column(db.Text)
    date = db.Column(db.Text)
    time = db.Column(db.Text)
    hall_length = db.Column(db.Text)
    hall_width = db.Column(db.Text)
    price = db.Column(db.Integer)

class Hall(db.Model):
    __tablename__ = 'halls'

    hall_id = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.Integer)
    place = db.Column(db.Text)
    status = db.Column(db.Text)
    reserver = db.Column(db.Text)


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Text)
    status = db.Column(db.Text)
    reserver = db.Column(db.Text)
    event_id = db.Column(db.Integer)
    places = db.Column(db.Text)


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), nullable=False)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.email)

def get_event_data(id, c_user=' '):
    data = Event.query.filter_by(id=id).all()[0]
    hall_length = int(data.hall_length)
    hall_width = int(data.hall_width)
    data_places = Hall.query.filter_by(id=id).all()
    places = []
    for el in data_places:
        if el.status == 'available':
            places.append([el.place.split('_')[1:], [' ', ' ']])
        elif el.status == 'reserved' and el.reserver == c_user:
            places.append([el.place.split('_')[1:], ['background-color: lime', ' ']])
        elif el.status == 'busy':
            places.append([el.place.split('_')[1:], ['background-color: red', 'disabled']])
        else:
            places.append([el.place.split('_')[1:], ['background-color: yellow', 'disabled']])
    hall = []
    for i in range(hall_length):
        hall.append(places[i * hall_width:(i + 1) * hall_width])
    return data, hall

def get_basket_data(id, reserver):
    basket_data = Hall.query.filter_by(reserver=reserver, id=id).all()
    event_data = Event.query.filter_by(id=id).all()[0]
    basket = [len(basket_data), len(basket_data) * event_data.price, []]
    for el in basket_data:
        basket[2].append(el.place)
    return basket

def generate_ticket(event):
    name = f'ticket_{event.id}_{event.place}_{event.reserver}'
    with open('ticketh.html', encoding='utf-8') as file:
        template = Template(file.read())

    rendered_template = template.render(data=event)

    with open(f'{name}.html', 'w', encoding='utf-8') as file:
        file.write(rendered_template)

    return f'<a href="/ticket/{name}">Место {event.place}</a>'


def get_data_of_current_user():
    tickets_data = Hall.query.filter_by(reserver=current_user.email).all()
    print(tickets_data)
    data = []
    for el in tickets_data:
        event_data = Event.query.filter_by(id=el.id).all()[0]
        print(event_data)
        place = el.place.split('_')
        data.append(
            [f'{event_data.title} в {event_data.locality}', place[1], place[2], event_data.location, event_data.date, event_data.id, event_data.price])
    print(data)
    return data


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contacts')
def contacts():
    return render_template('contacts.html')

@app.route('/reviews')
def reviews():
    return render_template('reviews.html')

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/events')
def events():
    data_events = Event.query.all()
    return render_template('events.html', data=data_events)

@app.route('/auth', methods=['POST', 'GET'])
def auth():
    print(request.args)
    if request.args.get('email'):
        email = request.args.get('email')
        go_to_event_id = request.args.get('event_id')
        print(email, go_to_event_id)
        user = User.query.filter_by(email=email).first()
        if user:
            login_user(user)
            print('success log in')
        else:
            new_user = User(email=email)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            print('success sign up')
        my_road = f'/event/{go_to_event_id}/tickets'
        return redirect(f'/event/{go_to_event_id}/tickets')
    else:
        go_to_event_id = request.args.get('event_id')
        return render_template('auth.html', go_to_event_id=go_to_event_id)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('events'))


@app.route('/ticket/<id>')
def ticket(id):
    print(id)
    return render_template(f'{id}.html')


@app.route('/event/<id>')
def eventid(id):
    data = Event.query.filter_by(id=id).all()
    return render_template('event2.html', data=data)

@app.route('/basket')
@login_required
def basket():
    data = get_data_of_current_user()
    return render_template('basket.html', data=data)

@app.route('/afisha')
def afisha():
    data_events = Event.query.all()
    print(data_events)
    return render_template('afisha.html', data=data_events)

@app.route('/map/<address>')
def map(address):
    return render_template('map.html', address=address)

@app.route('/payment')
def payment():
    data = get_data_of_current_user()
    amount = 0
    places = ''
    for el in data:
        amount += el[-1]
        places += f'{el[1]}_{el[2]} '
    id = int(data[0][-2])
    amount = amount * 100
    order = Order(amount=amount, status="new", reserver=current_user.email, event_id=id, places=places)
    db.session.add(order)
    db.session.commit()
    oid = Order.query.filter_by(amount=amount, status="new", reserver=current_user.email, event_id=id, places=places).all()[0].id
    print(oid)
    r = {
        "TerminalKey": tinkoff_terminalkey,
        "Amount": amount,
        "OrderId": oid,
        "Password": tinkoff_password,
        "Success URL": "http://127.0.0.1:5000/success",
        "Fail URL": "http://127.0.0.1:5000/fail",
        "Description": f"Оплата билетов. {data[0][0]}"
    }

    t = []

    for key, value in r.items():
        t.append({key: value})
    t = sorted(t, key=lambda x: list(x.keys())[0])
    t = "".join(str(value) for item in t for value in item.values())
    sha256 = hashlib.sha256()
    sha256.update(t.encode('utf-8'))
    t = sha256.hexdigest()
    r["Token"] = t
    print(r)
    response = requests.post(payments_url, headers={'Content-Type': 'application/json'}, json=r)
    print(response)
    print(response.json())
    return redirect(response.json()['PaymentURL'])


@app.route('/success')
def success():
    page = 'Список купленных билетов: <br>'
    tickets_data = Hall.query.filter_by(reserver=current_user.email).all()
    print(tickets_data)
    for event in tickets_data:
        page += f'{generate_ticket(event)}<br>'
    print(page)
    return page



@app.route('/check', methods=['GET', 'POST'])
def button_handler():
    if request.method == 'POST':
        # Выполнение действий по обработке нажатия кнопки
        print(request.form)
        button_value = request.form['button']
        print(f'Нажата кнопка с значением {button_value}')
        return 'Нажата кнопка'
    else:
        # Отображение страницы HTML с кнопкой
        return render_template('check.html')

@app.route('/event/<id>/tickets', methods=['GET', 'POST'])
def tickets(id):
    if isinstance(current_user, AnonymousUserMixin):
        data, hall = get_event_data(id)
        print(data, hall)
        return render_template('tickets_anon.html', data=hall, event=data)
    else:
        if request.method == 'POST':
            print(True)
            print(request.form)
            print(len(request.form))
            button_value = request.form['button']
            print(f'Нажата кнопка с значением {button_value}')
            get_place = Hall.query.filter_by(id=id, place=button_value).all()[0]
            print(get_place)
            if get_place.reserver == current_user.email:
                get_place.reserver = ' '
                get_place.status = 'available'
            else:
                get_place.reserver = current_user.email
                get_place.status = 'reserved'
            db.session.commit()
        data, hall = get_event_data(id, current_user.email)
        basket = get_basket_data(id, current_user.email)
        print(basket)
        return render_template('tickets.html', data=hall, event=data, user=current_user.email, basket=basket)

@app.route('/create_event', methods=['GET', 'POST'])
def create_event():
    form = CreateEventForm()
    if form.validate_on_submit():
        title = request.form['title']
        locality = request.form['locality']
        location = request.form['location']
        date = request.form['date']
        time = request.form['time']
        price = int(request.form['price'])
        hall_length = request.form['hall_length']
        hall_width = request.form['hall_width']
        event = Event(title=title, locality=locality, location=location, date=date, time=time, hall_length=hall_length, hall_width=hall_width, price=price)
        db.session.add(event)
        db.session.commit()
        id = Event.query.filter_by(title=title, locality=locality, location=location, date=date, time=time, hall_length=hall_length, hall_width=hall_width, price=price).all()[0].id
        print(id)
        for n in range(1, int(hall_length) + 1):
            for m in range(1, int(hall_width) + 1):
                hall = Hall(id=id, place=f'n_{n}_{m}', status='available', reserver=' ')
                db.session.add(hall)
        db.session.commit()
        return '<h1>Вы успешно создали мероприятие</h1>'
    else:
        return render_template('create_event.html', title='Новое мероприятие', form=form)


@app.route('/create_hall')
def new_hall():
    return 'Создаём новый зал'


@app.route('/fail')
def fail():
    return 'оплата не прошла'


if __name__ == "__main__":
    app.run()