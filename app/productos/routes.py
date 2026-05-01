from flask import Blueprint, render_template, request, redirect, session
from app.db import mysql

productos_bp = Blueprint('productos', __name__)

# Listar productos
@productos_bp.route('/productos')
def listar_productos():

    if 'usuario' not in session:
        return redirect('/')

    pagina = request.args.get('page', 1, type=int)
    buscar = request.args.get('q', '', type=str)

    limite = 10
    offset = (pagina - 1) * limite

    cursor = mysql.connection.cursor()

    # CONSULTA CON FILTRO Y PAGINACIÓN
    cursor.execute("""
        SELECT id, nombre, sku, precio_compra, precio_venta
        FROM productos
        WHERE activo = 1
        AND (nombre LIKE %s OR sku LIKE %s)
        LIMIT %s OFFSET %s
    """, (f"%{buscar}%", f"%{buscar}%", limite, offset))

    productos = cursor.fetchall()

    # TOTAL DE REGISTROS
    cursor.execute("""
        SELECT COUNT(*)
        FROM productos
        WHERE activo = 1
        AND (nombre LIKE %s OR sku LIKE %s)
    """, (f"%{buscar}%", f"%{buscar}%"))

    total = cursor.fetchone()[0]

    total_paginas = (total // limite) + (1 if total % limite > 0 else 0)

    return render_template(
        'productos/listar.html',
        productos=productos,
        pagina=pagina,
        total_paginas=total_paginas,
        buscar=buscar
    )


# Crear producto
@productos_bp.route('/productos/nuevo', methods=['GET', 'POST'])
def nuevo_producto():

    if 'usuario' not in session:
        return redirect('/')

    if request.method == 'POST':
        nombre = request.form['nombre']
        sku = request.form['sku']
        precio_compra = request.form['precio_compra']
        precio_venta = request.form['precio_venta']

        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO productos (nombre, sku, precio_compra, precio_venta)
            VALUES (%s, %s, %s, %s)
        """, (nombre, sku, precio_compra, precio_venta))

        mysql.connection.commit()

        return redirect('/productos')

    return render_template('productos/formulario.html', titulo="Nuevo producto", producto=None)


# Editar producto
@productos_bp.route('/productos/editar/<int:id>', methods=['GET', 'POST'])
def editar_producto(id):

    if 'usuario' not in session:
        return redirect('/')

    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        nombre = request.form['nombre']
        sku = request.form['sku']
        precio_compra = request.form['precio_compra']
        precio_venta = request.form['precio_venta']

        cursor.execute("""
            UPDATE productos
            SET nombre=%s, sku=%s, precio_compra=%s, precio_venta=%s
            WHERE id=%s
        """, (nombre, sku, precio_compra, precio_venta, id))

        mysql.connection.commit()

        return redirect('/productos')

    cursor.execute("SELECT * FROM productos WHERE id = %s", (id,))
    producto = cursor.fetchone()

    return render_template('productos/formulario.html', titulo="Editar producto", producto=producto)