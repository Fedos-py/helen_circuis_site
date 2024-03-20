from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import AnonymousUserMixin, UserMixin, LoginManager, login_user, current_user, logout_user, login_required
import os
from jinja2 import Template
import hashlib
import requests
import qrcode
from werkzeug.utils import secure_filename
from functools import wraps


from flask_forms import *
from private_info import *
from mail import send_email

file_path = os.path.abspath(os.getcwd())

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{file_path}/db/events.db'
app.config['SECRET_KEY'] = 'helen_secret_key'
UPLOAD_FOLDER = 'static/img/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
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
    date = db.Column(db.Text)
    time = db.Column(db.Text)
    hall_id = db.Column(db.Integer)
    active = db.Column(db.Integer)
    image = db.Column(db.Text)
    message = db.Column(db.Text)


class Link(db.Model):
    __tablename__ = 'links'

    id = db.Column(db.Integer, primary_key=True)
    goto = db.Column(db.Text)
    count = db.Column(db.Integer)
    status = db.Column(db.Integer)
    qr = db.Column(db.Text)


class Hall(db.Model):
    __tablename__ = 'halls'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    length = db.Column(db.Text)
    width = db.Column(db.Text)
    locality = db.Column(db.Text)
    location = db.Column(db.Text)
    event_id = db.Column(db.Integer)


class HallPlaces(db.Model):
    __tablename__ = 'halls_places'

    id = db.Column(db.Integer, primary_key=True)
    hall_id = db.Column(db.Integer)
    place = db.Column(db.Text)
    status = db.Column(db.Text)
    reserver = db.Column(db.Text)
    price = db.Column(db.Integer)
    event_id = db.Column(db.Integer)


class HallTemplatePlace(db.Model):
    __tablename__ = 'hall_templates_places'

    id = db.Column(db.Integer, primary_key=True)
    hall_id = db.Column(db.Integer)
    place = db.Column(db.Text)
    status = db.Column(db.Text)
    reserver = db.Column(db.Text)
    price = db.Column(db.Integer)


class HallTemplateList(db.Model):
    __tablename__ = 'hall_templates_list'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    length = db.Column(db.Text)
    width = db.Column(db.Text)
    locality = db.Column(db.Text)
    location = db.Column(db.Text)


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
    current_payment = db.Column(db.Integer)

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
    hall = Hall.query.filter_by(id=data.hall_id).all()[0]
    hall_length = int(hall.length)
    hall_width = int(hall.width)
    data_places = HallPlaces.query.filter_by(hall_id=data.hall_id).all()
    places = []
    for el in data_places:
        if el.status == 'available':
            places.append([el.place.split('_')[1:], [' ', ' '], ['visible', el.price]])
        elif el.status == 'reserved' and el.reserver == c_user:
            places.append([el.place.split('_')[1:], ['background-color: lime', ' '], ['visible', el.price]])
        elif el.status == 'busy':
            places.append([el.place.split('_')[1:], ['background-color: red', 'disabled'], ['visible', el.price]])
        elif el.status == 'deleted':
            places.append([el.place.split('_')[1:], [' ', ' '], ['deleted', el.price]])
        else:
            places.append([el.place.split('_')[1:], ['background-color: yellow', 'disabled'], el.price])
    hall = []
    for i in range(hall_length):
        hall.append(places[i * hall_width:(i + 1) * hall_width])
    print(hall)
    return data, hall

def get_basket_data(id, reserver):
    basket_data = HallPlaces.query.filter_by(reserver=reserver, hall_id=id, status='reserved').all()
    event_data = Event.query.filter_by(id=id).all()[0]
    full_price = 0
    basket = [len(basket_data), 0, []]
    for el in basket_data:
        full_price += el.price
        basket[2].append(el.place)
    basket[1] = full_price
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
    tickets_data = HallPlaces.query.filter_by(reserver=current_user.email, status='reserved').all()
    print(tickets_data)
    data = []
    for el in tickets_data:
        event_data = Event.query.filter_by(id=el.hall_id).all()[0]
        hall_data = Hall.query.filter_by(id=el.hall_id).all()[0]
        print(event_data)
        place = el.place.split('_')
        data.append(
            [f'{event_data.title} в {hall_data.locality}', place[1], place[2], hall_data.location, event_data.date, event_data.id, el.price])
    print(data)
    return data


def get_token(request):
    t = []

    for key, value in request.items():
        if key == "TerminalKey" or key == "Amount" or key == "OrderId" or key == "Password" or key == "PaymentId":
            t.append({key: value})
    t = sorted(t, key=lambda x: list(x.keys())[0])
    t = "".join(str(value) for item in t for value in item.values())
    sha256 = hashlib.sha256()
    sha256.update(t.encode('utf-8'))
    t = sha256.hexdigest()
    return t


def create_qr(url, filename):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(f'{file_path}/static/img/{filename}')

def add_link(goto):
    link = Link(goto=goto, count=0, status=1)
    db.session.add(link)
    db.session.commit()
    create_qr(f'https://teatr-gamma.ru/link/{link.id}', f'qr-link-{link.id}.png')
    link.qr = f'qr-link-{link.id}.png'
    db.session.commit()


def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if isinstance(current_user, AnonymousUserMixin):
            return f'Данная страница доступна только администраторам. <a href="/admin_auth">Авторизоваться</a>'
        elif current_user.email == 'admin':
            return func(*args, **kwargs)
        else:
            return f'Данная страница доступна только администраторам.'
    return decorated_view


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


@app.route('/events', methods=['POST', 'GET'])
@admin_required
def events():
    data_events = Event.query.all()
    halls = Hall.query.all()
    if request.method == 'POST':
        id = int(list(request.form.keys())[-1])
        event = Event.query.filter_by(id=id).all()[0]
        hall = Hall.query.filter_by(id=id).all()[0]
        if request.form['title'] != event.title:
            event.title = request.form['title']
        if request.form['hall'] != hall.title:
            hall.title = request.form['hall']
        if request.form['locality'] != hall.locality:
            hall.locality = request.form['locality']
        if request.form['location'] != hall.location:
            hall.location = request.form['location']
        if request.form['date'] != event.date:
            event.date = request.form['date']
        if request.form['time'] != event.time:
            event.time = request.form['time']
        if 'checkbox' in request.form and event.active == 0:
            event.active = 1
        elif 'checkbox' not in request.form and event.active == 1:
            event.active = 0
        db.session.commit()
    return render_template('events.html', data=data_events, halls=halls)

@app.route('/auth', methods=['POST', 'GET'])
def auth():
    print(request.args)
    if request.args.get('email'):
        email = request.args.get('email')
        if email != 'admin':
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
            return redirect('admin_auth')
    else:
        go_to_event_id = request.args.get('event_id')
        return render_template('auth.html', go_to_event_id=go_to_event_id)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('afisha'))


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
    data_events = Event.query.filter_by(active=1).all()
    if len(data_events) == 0:
        return '<center>В данный момент нет доступных мероприятий!<br><a href="/">Вернуться на главную страницу</a></center>'
    else:
        dop_data = Hall.query.all()
        print(dop_data)
        print(data_events[0].image)
        return render_template('afisha.html', data=data_events, dop_data=dop_data)

@app.route('/map/<address>')
def map(address):
    return render_template('map.html', address=address)

@app.route('/payment')
def payment():
    data = get_data_of_current_user()
    amount = 0
    places = ''
    Items_FFD_12 = []
    for el in data:
        amount += el[-1]
        places += f'{el[1]}_{el[2]} '
        Items_FFD_12.append({
            "Name": f'Билет на мероприятие. Ряд: {el[1]}. Место:{el[2]}.',
            "Price": el[-1] * 100,
            "Quantity": 1,
            "Amount": el[-1] * 100,
            "Tax": "vat20",
            "PaymentMethod": "full_prepayment",
            "PaymentObject": "service",
            "MeasurementUnit": "HUR"
        })
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
        "Description": f"Оплата билетов. {data[0][0]}",
        "Receipt": {
            "FfdVersion": "1.2",
            "Taxation": "osn",
            "Email": current_user.email,
            "Items": Items_FFD_12
        }
    }

    t = get_token(r)
    r["Token"] = t
    print(r)
    response = requests.post(payments_url, headers={'Content-Type': 'application/json'}, json=r)
    print(response)
    print(response.json())
    user = User().query.filter_by(email=current_user.email).all()[0]
    user.current_payment = response.json()['PaymentId']
    db.session.commit()
    return redirect(response.json()['PaymentURL'])


@app.route('/success_redirect/', methods=['GET'])
def success_redirect():
    return redirect('/success')

@app.route('/success')
def success():
    """
    page = 'Список купленных билетов: <br>'
    tickets_data = Hall.query.filter_by(reserver=current_user.email).all()
    print(tickets_data)
    for event in tickets_data:
        page += f'{generate_ticket(event)}<br>'
    print(page)
    """
    user = User.query.filter_by(email=current_user.email).all()[0]
    r = {
        "TerminalKey": tinkoff_terminalkey,
        "Password": tinkoff_password,
        "PaymentId": user.current_payment
    }

    t = get_token(r)
    r["Token"] = t
    print(r)
    response = requests.post('https://securepay.tinkoff.ru/v2/GetState', headers={'Content-Type': 'application/json'}, json=r)
    print(response)
    print(response.json())
    status = response.json()['Status']
    print(status)
    if status == 'CONFIRMED':
        order = Order.query.filter_by(reserver=current_user.email).all()[-1]
        tickets = order.places.split(' ')[:-1]
        places = []
        for elem in tickets:
            print(f'n_{elem}')
            ticket = HallPlaces.query.filter_by(reserver=current_user.email, event_id=order.event_id, place=f'n_{elem}').all()[0]
            ticket.status = 'busy'
            el_pl = elem.split('_')
            places.append(f'Ряд:{el_pl[0]}. Место:{el_pl[1]}.')
        user.current_payment = 0
        order.status = 'success'
        db.session.commit()
        event = Event.query.filter_by(id=order.event_id).all()[0]
        hall = Hall.query.filter_by(event_id=event.id).all()[0]
        send_email(current_user.email, f'Здравствуйте! Вы успешно приобрели билеты на нашем сайте <b>teatr-gamma.ru</b> <br>Мероприятие: <b>{event.title} {event.date} в {event.time}</b> <br> Место проведения: <b>{hall.title}({hall.locality}, {hall.location})</b><br> Ваши места: <b>{", ".join(places)}</b>')
        return "<center><h3>Вы успешно оплатили выбранные билеты.<br>Билеты отправлены на указанную почту.<br><a href='/'>Вернуться на главную страницу</a></h3></center>"
    else:
        return f"<center><h3 style='color: red'>К сожалению, оплата не прошла. Статус платежа {status}<br>Побробуйте снова!<br><a href='/basket'>Вернуться к корзине</a></h3></center>"


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
def tickets_old(id):
    event = Event.query.filter_by(id=id).all()[0]
    if event.active == 1:
        if isinstance(current_user, AnonymousUserMixin):
            data, hall = get_event_data(id)
            return render_template('tickets_anon.html', data=hall, event=data)
        else:
            if request.method == 'POST':
                button_value = request.form['button']
                print(f'Нажата кнопка с значением {button_value}')
                id = Event.query.filter_by(id=id).all()[0].hall_id
                get_place = HallPlaces.query.filter_by(hall_id=id, place=button_value).all()[0]
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
    else:
        return 'продажи на данное мероприятие в данный момент закрыты'

@app.route('/admin_auth', methods=['GET', 'POST'])
def admin_auth():
    if isinstance(current_user, AnonymousUserMixin):
        goto = request.args.get('goto')
        if goto == None:
            goto = 'index'
        if request.args.get('password'):
            password = request.args.get('password')
            if password == admin_password:
                user = User.query.filter_by(email='admin').first()
                login_user(user)
                return redirect(url_for(goto))
        return render_template('admin_auth.html', goto=goto)
    else:
        return f'welcome, {current_user.email}'


@app.route('/create_event', methods=['GET', 'POST'])
@admin_required
def create_event():
    form = CreateEventForm()
    if form.validate_on_submit():
        hall_for_copy = int(request.form['halls'])
        hall_father = HallTemplateList.query.filter_by(id=hall_for_copy).all()[0]
        hall_father_places = HallTemplatePlace.query.filter_by(hall_id=hall_for_copy).all()
        title = request.form['title']
        date = request.form['date']
        time = request.form['time']
        image = request.form['images']
        event = Event(title=title, date=date, time=time, hall_id=0, active=0, image=image)
        db.session.add(event)
        db.session.commit()
        hall = Hall(title=hall_father.title, length=hall_father.length, width=hall_father.width, locality=hall_father.locality, location=hall_father.location, event_id=event.id)
        db.session.add(hall)
        db.session.commit()
        id = Hall.query.filter_by(title=hall_father.title, length=hall_father.length, width=hall_father.width, locality=hall_father.locality, location=hall_father.location, event_id=event.id).all()[0].id
        event_id = Event.query.filter_by(title=title, date=date, time=time, hall_id=0).all()[0].id
        for elem in hall_father_places:
            place = HallPlaces(hall_id=id, place=elem.place, status=elem.status, reserver=" ", price=elem.price, event_id=event_id)
            db.session.add(place)
        db.session.commit()
        event = Event.query.filter_by(title=title, date=date, time=time, hall_id=0).all()[0]
        event.hall_id = id
        db.session.commit()

        return f'<h1>Вы успешно создали мероприятие. Event id={id}</h1>'
    else:
        halls = HallTemplateList.query.filter_by().all()
        images = files = os.listdir(UPLOAD_FOLDER)
        return render_template('create_event.html', title='Новое мероприятие', form=form, halls=halls, images=images)


@app.route('/create_hall', methods=['GET', 'POST'])
@admin_required
def new_hall():
    form = CreateHallForm()
    if form.validate_on_submit():
        print('нажали кнопку')
        title = request.form['title']
        locality = request.form['locality']
        location = request.form['location']
        length = request.form['hall_length']
        width = request.form['hall_width']
        event = HallTemplateList(title=title, length=length,  width=width, locality=locality, location=location)
        db.session.add(event)
        db.session.commit()
        id = HallTemplateList.query.filter_by(title=title, length=length,  width=width, locality=locality, location=location).all()[0].id
        print(id)
        for n in range(1, int(length) + 1):
            for m in range(1, int(width) + 1):
                place = HallTemplatePlace(hall_id=id, place=f'n_{n}_{m}', status='available', reserver=' ', price=0)
                db.session.add(place)
        db.session.commit()
        return f"Создан новый шаблон. Теперь можно <a href='/edit_hall/{id}'> его редактировать </a>"
    return render_template('create_hall.html', title='Новый зал', form=form)


@app.route('/edit_hall/<id>', methods=['GET', 'POST'])
@admin_required
def edit_hall(id):
    get_price = False
    if request.method == 'POST':
        print(request.form)
        if "button" in request.form.keys():
            print("ОГОГО")
            button_value = request.form['button']
            print(f'Нажата кнопка с значением {button_value}')
            get_place = HallTemplatePlace.query.filter_by(hall_id=id, place=button_value).all()[0]
            if get_place.status == 'deleted':
                get_place.status = 'available'
            else:
                get_place.status = 'deleted'
            db.session.commit()
        elif "button_save" in request.form.keys():
            for key in request.form.keys():
                if key != "button_save":
                    get_places = HallTemplatePlace.query.filter_by(hall_id=id).all()
                    for el in get_places:
                        if el.place.split('_')[1] == key:
                            el.price = request.form[key]
            db.session.commit()

    template_data = HallTemplateList.query.filter_by(id=id).all()[0]
    data = HallTemplatePlace.query.filter_by(hall_id=id).all()
    print(data)
    places = []
    hall_width = int(template_data.width)
    hall_length = int(template_data.length)
    for el in data:
        place = el.place.split('_')[1:]
        if el.status == 'deleted':
            place.append('background-color: red')
        else:
            place.append(' ')
        place.append(el.price)
        places.append(place)
    hall = []
    for i in range(hall_length):
        hall.append(places[i * hall_width:(i + 1) * hall_width])
    print(hall)

    return render_template('edit_hall.html', title='Новый зал', name=template_data.title, data=hall)


@app.route('/fail_redirect/', methods=['GET'])
def fail_redirect():
    message = request.args.get('Message')
    return redirect(f'/fail/{message}')


@app.route('/fail/<error>')
def fail(error):
    return f"<center><h3 style='color: red'>К сожалению, оплата не прошла.<br>Ошибка: {error} Побробуйте снова!<br><a href='/basket'>Вернуться к корзине</a></h3></center>"


@app.route('/link/<id>')
def link_redirect(id):
    link = Link.query.filter_by(id=id).all()[0]
    link.count += 1
    db.session.commit()
    return redirect(f'/{link.goto}')


@app.route('/links')
@admin_required
def links():
    data = Link.query.all()
    return render_template('links.html', data=data)

@app.route('/create_link', methods=['GET', 'POST'])
@admin_required
def create_link():
    form = CreateLinkForm()
    if form.validate_on_submit():
        add_link(request.form['link'])
        return 'Успешно создана ссылка. <a href="/links"> Вернуться к ссылкам</a>'
    return render_template('create_link.html', form=form)


@app.route('/admin')
def admin():
    return render_template('admin.html')


@app.route('/upload', methods=['GET', 'POST'])
@admin_required
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'Вы не выбрали файл! <a href="/upload">Вернуться</a>'
        file = request.files['file']
        if file.filename == '':
            return 'Вы не выбрали файл! <a href="/upload">Вернуться</a>'
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return f'успешно сохранили файл <a href="/static/img/{filename}">Посмотреть картинку</a>'
        print('POST')
    return render_template('upload.html')

if __name__ == "__main__":
    app.run()