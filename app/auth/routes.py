from flask import Blueprint, render_template, request, redirect, session
from app.db import mysql

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT * FROM usuarios 
            WHERE username = %s AND password = %s
        """, (username, password))

        user = cursor.fetchone()

        if user:
            session['usuario'] = username
            return redirect('/inventario')
        else:
            error = "Usuario o contraseña incorrectos"

    return render_template('login.html', error=error)

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect('/')