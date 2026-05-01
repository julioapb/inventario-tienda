from flask import Blueprint, render_template, request, redirect, session
from app.db import mysql

inventario_bp = Blueprint('inventario', __name__)

@inventario_bp.route('/inventario')
def inventario():

    if 'usuario' not in session:
        return redirect('/')

    pagina = request.args.get('page', 1, type=int)
    buscar = request.args.get('q', '', type=str)

    limite = 10
    offset = (pagina - 1) * limite

    cursor = mysql.connection.cursor()

    # CONSULTA CON STOCK + FILTRO + PAGINACIÓN
    cursor.execute("""
        SELECT 
            p.nombre,
            COALESCE(SUM(
                CASE 
                    WHEN m.tipo = 'entrada' THEN m.cantidad
                    WHEN m.tipo = 'salida' THEN -m.cantidad
                END
            ), 0) as stock
        FROM productos p
        LEFT JOIN movimientos_stock m ON p.id = m.id_producto
        WHERE p.activo = 1
        AND p.nombre LIKE %s
        GROUP BY p.id
        LIMIT %s OFFSET %s
    """, (f"%{buscar}%", limite, offset))

    productos = cursor.fetchall()

    # TOTAL PARA PAGINACIÓN
    cursor.execute("""
        SELECT COUNT(*)
        FROM productos
        WHERE activo = 1
        AND nombre LIKE %s
    """, (f"%{buscar}%",))

    total = cursor.fetchone()[0]

    total_paginas = (total // limite) + (1 if total % limite > 0 else 0)

    return render_template(
        'inventario/listar.html',
        productos=productos,
        pagina=pagina,
        total_paginas=total_paginas,
        buscar=buscar
    )

@inventario_bp.route('/inventario/entrada', methods=['GET', 'POST'])
def entrada():

    if 'usuario' not in session:
        return redirect('/')

    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        id_producto = request.form['id_producto']
        cantidad = request.form['cantidad']

        cursor.execute("""
            INSERT INTO movimientos_stock (id_producto, tipo, cantidad, motivo)
            VALUES (%s, 'entrada', %s, 'compra')
        """, (id_producto, cantidad))

        mysql.connection.commit()

        return redirect('/inventario')

    cursor.execute("SELECT id, nombre FROM productos WHERE activo = 1")
    productos = cursor.fetchall()

    return render_template('inventario/entrada.html', productos=productos)


@inventario_bp.route('/inventario/movimientos')
def movimientos():

    if 'usuario' not in session:
        return redirect('/')

    pagina = request.args.get('page', 1, type=int)
    buscar = request.args.get('q', '', type=str)

    limite = 10
    offset = (pagina - 1) * limite

    cursor = mysql.connection.cursor()

    # CONSULTA CON FILTRO + PAGINACIÓN
    cursor.execute("""
        SELECT 
            p.nombre,
            m.tipo,
            m.cantidad,
            m.fecha
        FROM movimientos_stock m
        JOIN productos p ON p.id = m.id_producto
        WHERE p.nombre LIKE %s
        ORDER BY m.fecha DESC
        LIMIT %s OFFSET %s
    """, (f"%{buscar}%", limite, offset))

    movimientos = cursor.fetchall()

    # TOTAL PARA PAGINACIÓN
    cursor.execute("""
        SELECT COUNT(*)
        FROM movimientos_stock m
        JOIN productos p ON p.id = m.id_producto
        WHERE p.nombre LIKE %s
    """, (f"%{buscar}%",))

    total = cursor.fetchone()[0]

    total_paginas = (total // limite) + (1 if total % limite > 0 else 0)

    return render_template(
        'inventario/movimientos.html',
        movimientos=movimientos,
        pagina=pagina,
        total_paginas=total_paginas,
        buscar=buscar
    )