from flask import render_template, session, redirect, url_for, request
from . import main
from .forms import LoginForm

@main.route('/')
def base():
    return redirect(url_for('main.index'))


@main.route('/login', methods=['GET', 'POST'])
def index():
    form = LoginForm()
    if form.validate_on_submit():
        session['name'] = form.name.data
        session['room'] = form.room.data
        return redirect(url_for('main.presidents'))
    elif request.method == 'GET':
        form.name.data = session.get('name', '')
        form.room.data = session.get('room', '')
    return render_template('index.html', form=form)


@main.route('/presidents')
def presidents():
    name = session.get('name', '')
    room = session.get('room', '')
    if name == '' or room == '':
        return redirect(url_for('main.index'))
    return render_template('presidents.html', name=name, room=room)
