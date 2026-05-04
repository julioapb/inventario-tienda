from flask import Blueprint, render_template, request, jsonify, session, redirect
from app.db import mysql
from datetime import date
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
from flask import send_file
import io
from datetime import datetime

ventas_bp = Blueprint('ventas', __name__)

# Caja
@ventas_bp.route('/caja')
def caja():

    if 'usuario' not in session:
        return redirect('/')

    return render_template('ventas/caja.html')


# Buscar productos
@ventas_bp.route('/buscar')
def buscar():

    query = request.args.get('q')

    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT 
            p.id,
            p.nombre,
            p.precio_venta,
            COALESCE(SUM(
                CASE 
                    WHEN m.tipo = 'entrada' THEN m.cantidad
                    WHEN m.tipo = 'salida' THEN -m.cantidad
                END
            ), 0) as stock
        FROM productos p
        LEFT JOIN movimientos_stock m ON p.id = m.id_producto
        WHERE p.nombre LIKE %s OR p.sku LIKE %s
        GROUP BY p.id
        LIMIT 10
    """, (f"%{query}%", f"%{query}%"))

    productos = cursor.fetchall()

    resultado = []
    for p in productos:
        resultado.append({
            "id": p[0],
            "nombre": p[1],
            "precio": float(p[2]),
            "stock": int(p[3])
        })

    return jsonify(resultado)


# Guardar venta
@ventas_bp.route('/guardar_venta', methods=['POST'])
def guardar_venta():

    print("ENTRANDO A VALIDAR STOCK")

    data = request.json
    carrito = data['carrito']
    metodo_pago = data['metodo_pago']
    
    cursor = mysql.connection.cursor()

    # VALIDAR STOCK ANTES DE VENDER
    for p in carrito:

        print("Producto:", p['id'], "Cantidad:", p['cantidad'])

        cursor.execute("""
            SELECT 
                COALESCE(SUM(
                    CASE 
                        WHEN tipo = 'entrada' THEN cantidad
                        WHEN tipo = 'salida' THEN -cantidad
                    END
                ), 0)
            FROM movimientos_stock
            WHERE id_producto = %s
        """, (p['id'],))

        stock_actual = cursor.fetchone()[0]

        print("Stock calculado:", stock_actual)

        if p['cantidad'] > stock_actual:
            return jsonify({
                "ok": False,
                "error": f"No hay suficiente stock para {p['nombre']}"
            })

    # CALCULAR TOTAL
    total = sum(p['precio'] * p['cantidad'] for p in carrito)

    # GUARDAR VENTA
    cursor.execute("""
        INSERT INTO ventas (total, metodo_pago)
        VALUES (%s, %s)
    """, (total, metodo_pago))
    
    id_venta = cursor.lastrowid

    # GUARDAR DETALLE Y DESCONTAR STOCK
    for p in carrito:

        subtotal = p['precio'] * p['cantidad']

        cursor.execute("""
            INSERT INTO detalle_venta (id_venta, id_producto, cantidad, precio_unitario, subtotal)
            VALUES (%s, %s, %s, %s, %s)
        """, (id_venta, p['id'], p['cantidad'], p['precio'], subtotal))

        cursor.execute("""
            INSERT INTO movimientos_stock (id_producto, tipo, cantidad, motivo)
            VALUES (%s, 'salida', %s, 'venta')
        """, (p['id'], p['cantidad']))

    mysql.connection.commit()

    return jsonify({"ok": True})

@ventas_bp.route('/cerrar_caja', methods=['POST'])
def cerrar_caja():

    if 'usuario' not in session:
        return jsonify({"ok": False, "error": "No autorizado"})

    cursor = mysql.connection.cursor()
    hoy = date.today()

    # 1. Verificar si ya existe cierre hoy
    cursor.execute("""
        SELECT id FROM cierre_caja
        WHERE fecha = %s
    """, (hoy,))
    
    if cursor.fetchone():
        return jsonify({
            "ok": False,
            "error": "La caja ya fue cerrada hoy"
        })

    # 2. Calcular totales del día
    cursor.execute("""
        SELECT COALESCE(SUM(total), 0)
        FROM ventas
        WHERE DATE(fecha) = %s
    """, (hoy,))
    total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(total), 0)
        FROM ventas
        WHERE DATE(fecha) = %s AND metodo_pago = 'efectivo'
    """, (hoy,))
    efectivo = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(total), 0)
        FROM ventas
        WHERE DATE(fecha) = %s AND metodo_pago = 'tarjeta'
    """, (hoy,))
    tarjeta = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM ventas
        WHERE DATE(fecha) = %s
    """, (hoy,))
    cantidad = cursor.fetchone()[0]

    # 3. Guardar cierre
    cursor.execute("""
        INSERT INTO cierre_caja (fecha, total, efectivo, tarjeta, cantidad_ventas, usuario)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (hoy, total, efectivo, tarjeta, cantidad, session['usuario']))

    mysql.connection.commit()

    return jsonify({
        "ok": True,
        "mensaje": "Caja cerrada correctamente"
    })

@ventas_bp.route('/cierre')
def cierre():

    if 'usuario' not in session:
        return redirect('/')

    cursor = mysql.connection.cursor()
    hoy = date.today()

    # total general
    cursor.execute("""
        SELECT COALESCE(SUM(total), 0)
        FROM ventas
        WHERE DATE(fecha) = %s
    """, (hoy,))
    total = cursor.fetchone()[0]

    # efectivo
    cursor.execute("""
        SELECT COALESCE(SUM(total), 0)
        FROM ventas
        WHERE DATE(fecha) = %s AND metodo_pago = 'efectivo'
    """, (hoy,))
    efectivo = cursor.fetchone()[0]

    # tarjeta
    cursor.execute("""
        SELECT COALESCE(SUM(total), 0)
        FROM ventas
        WHERE DATE(fecha) = %s AND metodo_pago = 'tarjeta'
    """, (hoy,))
    tarjeta = cursor.fetchone()[0]

    # cantidad ventas
    cursor.execute("""
        SELECT COUNT(*)
        FROM ventas
        WHERE DATE(fecha) = %s
    """, (hoy,))
    cantidad = cursor.fetchone()[0]

    return render_template(
        'ventas/cierre.html',
        total=total,
        efectivo=efectivo,
        tarjeta=tarjeta,
        cantidad=cantidad
    )

@ventas_bp.route('/cierres')
def historial_cierres():

    if 'usuario' not in session:
        return redirect('/')

    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT fecha, total, efectivo, tarjeta, cantidad_ventas, usuario
        FROM cierre_caja
        ORDER BY fecha DESC
    """)

    cierres = cursor.fetchall()

    return render_template('ventas/cierres.html', cierres=cierres)