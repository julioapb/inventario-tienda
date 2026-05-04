# Sistema de Inventario y Punto de Venta (POS)

Aplicación web desarrollada con Python (Flask) y MySQL para la gestión de inventario y ventas en pequeños negocios.

El sistema permite controlar productos, stock, ventas diarias y cierres de caja de forma sencilla, funcionando completamente en entorno local sin necesidad de internet.

---

## Funcionalidades

### Gestión de productos
- Crear, editar y desactivar productos
- Control de precios de compra y venta
- Búsqueda y paginación

### Control de inventario
- Sistema basado en movimientos (entradas y salidas)
- Cálculo automático de stock
- Historial de movimientos
- Búsqueda y paginación

### Caja (Punto de venta)
- Búsqueda de productos por nombre o SKU
- Carrito de compra
- Selección de método de pago (efectivo / tarjeta)
- Cálculo de cambio
- Validación de stock en tiempo real

### Cierre de caja
- Resumen diario de ventas
- Separación por método de pago
- Registro de cierres
- Historial de cierres de caja

---

## Tecnologías utilizadas

- Python 3
- Flask
- MySQL
- Bootstrap 5
- HTML / CSS / JavaScript

---

## Instalación

### 1. Clonar repositorio

```bash
git clone https://github.com/julioapb/inventario-tienda.git
cd inventario-tienda
