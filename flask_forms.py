from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

    def __repr__(self):
        return '<User %r>' % self.username

class CreateEventForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    locality = StringField('Населённый пункт', validators=[DataRequired()])
    location = StringField('Адрес', validators=[DataRequired()])
    date = StringField('Дата', validators=[DataRequired()])
    time = StringField('Время', validators=[DataRequired()])
    price = StringField('Стоимость посещения мероприятия')
    hall_length = StringField('Длина зала(кол-во рядов)')
    hall_width = StringField('Ширина зала(кол-во рядов)')
    submit = SubmitField('Создать')

    def __repr__(self):
        return '<User %r>' % self.username


class OrderForm(FlaskForm):
    address = StringField('Адрес', validators=[DataRequired()])
    comment = PasswordField('Комментарий к заказу', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    phone = StringField('Номер телефона получателя', validators=[DataRequired()])
    submit = SubmitField('Оформить')

    def __repr__(self):
        return '<User %r>' % self.username


class AddItemForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired()])
    price = StringField('Цена', validators=[DataRequired()])
    image = StringField('Изображение', validators=[DataRequired()])
    about = StringField('Описание', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Добавить')

    def __repr__(self):
        return '<User %r>' % self.username
