# Catálogo de Datos — Producto Comercial

## Descripción general

| Atributo          | Valor                                              |
|-------------------|----------------------------------------------------|
| **Producto**      | Comercial                                          |
| **Base de datos** | `fake` (MySQL 8.x — `www.bigdataybi.com:3306`)    |
| **Tablas**        | `customers`, `products`, `sales`, `shops`          |
| **Dominio**       | Ventas y distribución de productos de limpieza     |
| **Geografía**     | Ecuador (sucursales en Quito, Guayaquil y Cuenca)  |
| **Actualización** | Carga batch via ETL (columna `_loadtime`)          |

### Contexto de negocio

El producto de datos **Comercial** centraliza la información transaccional de una empresa distribuidora de productos de limpieza en Ecuador. Integra cuatro entidades clave:

- **Clientes** (`customers`): personas o empresas que realizan compras.
- **Productos** (`products`): catálogo de artículos disponibles para la venta (detergentes, limpiadores, cloro, etc.).
- **Ventas** (`sales`): líneas de facturación que registran cada transacción comercial.
- **Sucursales** (`shops`): puntos físicos de venta distribuidos en las principales ciudades del país.

Este catálogo está diseñado para permitir consultas SQL analíticas sobre ventas, rendimiento de sucursales, comportamiento de clientes y rotación de inventario.

---

## Diagrama de relaciones (ERD)

```
customers                sales                  products
──────────               ──────────             ──────────
id_cliente ◄─────────── cod_cliente            id_producto ◄─── cod_producto
identificacion           cod_factura                             nombre_producto
nombre                   cod_sucursal ──────►   shops            descripcion
email                    cod_producto            ──────────       precio_unitario
telefono                 fecha_venta             id_sucursal      stock
direccion                cantidad                nombre_sucursal  marca
estado                   precio_unitario         ciudad           _loadtime
_loadtime                _loadtime               latitud
                                                 longitud
                                                 _loadtime
```

**Claves foráneas:**

| Columna en `sales` | Referencia                   |
|--------------------|------------------------------|
| `cod_cliente`      | `customers.id_cliente`       |
| `cod_producto`     | `products.id_producto`       |
| `cod_sucursal`     | `shops.id_sucursal`          |

---

## Tablas

---

### `customers` — Clientes

Registra a todos los clientes que han realizado o pueden realizar compras. Un cliente puede tener múltiples facturas en `sales`.

| Atributo      | Valor                                        |
|---------------|----------------------------------------------|
| Filas         | 10                                           |
| Clave primaria| `id_cliente`                                 |
| Carga ETL     | Batch — `_loadtime = 2025-06-26 19:34:48`   |

#### Columnas

| Columna         | Tipo          | Nulo | PK  | Descripción                                                                                                                                                      | Valores / Ejemplos                                                |
|-----------------|---------------|------|-----|------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------|
| `id_cliente`    | `INT`         | NO   | ✓   | Identificador único del cliente. Clave primaria de la tabla. Utilizar para hacer JOIN con `sales.cod_cliente`.                                                  | `1`, `2`, `3` … `10`                                             |
| `identificacion`| `VARCHAR(45)` | SÍ   | —   | Número de cédula o RUC ecuatoriano del cliente. Las cédulas tienen 10 dígitos; los RUC tienen 13. Puede contener datos de personas naturales o jurídicas.       | `"1705251732"`, `"0700652068"`                                   |
| `nombre`        | `LONGTEXT`    | SÍ   | —   | Nombre completo del cliente tal como aparece en el documento de identidad. Incluye tratamientos honoríficos (`Dr.`, `Sr(a).`) en datos generados.               | `"Josefina Alicia Otero Rosas"`, `"Dr. Estela Serrano"`         |
| `email`         | `LONGTEXT`    | SÍ   | —   | Dirección de correo electrónico del cliente. Normalizado a minúsculas en la capa Silver. Usar para comunicaciones y deduplicación.                              | `"estradaines@icloud.com"`, `"ricardopantoja@gmail.com"`        |
| `telefono`      | `LONGTEXT`    | SÍ   | —   | Número de teléfono del cliente. Formato variable: puede incluir código de área ecuatoriano `(593)` o formato local de 10 dígitos. Puede contener espacios vacíos.| `"(593)958474054"`, `"0919849754"`, `" "` (vacío)              |
| `direccion`     | `LONGTEXT`    | SÍ   | —   | Dirección postal completa del cliente. Incluye calle, número, departamento, ciudad, estado/provincia y código postal. Formato libre, no estructurado.            | `"Prolongación Sudán del Sur 590 Edif. 300, ... NL 34179-3364"` |
| `estado`        | `LONGTEXT`    | SÍ   | —   | Estado comercial del cliente. Determina si el cliente está habilitado para realizar compras. Solo dos valores posibles en producción.                            | `"activo"` (8 clientes), `"inactivo"` (2 clientes)             |
| `_loadtime`     | `TIMESTAMP`   | SÍ   | —   | Fecha y hora en que el registro fue cargado por el proceso ETL desde el sistema fuente. Campo de auditoría, no modificado por el negocio.                       | `"2025-06-26 19:34:48"`                                         |

#### Notas de calidad

- `telefono` puede contener valores con solo espacios (campo vacío de hecho). Filtrar con `TRIM(telefono) != ''`.
- `identificacion` no tiene restricción UNIQUE en la base de datos; verificar duplicados antes de usar como clave de negocio.
- El campo `estado` está definido como `LONGTEXT` en lugar de `ENUM` o `VARCHAR`; en consultas usar `LOWER(TRIM(estado))` para comparaciones seguras.

---

### `products` — Productos

Catálogo de productos disponibles para la venta. Son artículos de limpieza del hogar y uso industrial distribuidos a través de las sucursales.

| Atributo      | Valor                                        |
|---------------|----------------------------------------------|
| Filas         | 5                                            |
| Clave primaria| `id_producto` (sin restricción PK en DDL)    |
| Carga ETL     | Batch — `_loadtime = 2025-06-26 19:34:32`   |

#### Columnas

| Columna           | Tipo        | Nulo | Descripción                                                                                                                                                     | Valores / Ejemplos                                              |
|-------------------|-------------|------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| `id_producto`     | `INT`       | SÍ   | Identificador único del producto. Utilizar para hacer JOIN con `sales.cod_producto`. **Nota:** no tiene restricción PRIMARY KEY en DDL, pero es functionally único. | `1`, `2`, `3`, `4`, `5`                                        |
| `nombre_producto` | `LONGTEXT`  | SÍ   | Nombre comercial del producto tal como aparece en el catálogo de ventas. Describe el tipo y uso del artículo.                                                   | `"Detergente Multiusos"`, `"Cloro Concentrado"`, `"Limpiavidrios"` |
| `descripcion`     | `LONGTEXT`  | SÍ   | Descripción larga del producto. Generada en los datos de prueba (Lorem Ipsum en italiano). En producción contiene características técnicas y de uso del artículo. | Texto libre                                                     |
| `precio_unitario` | `FLOAT`     | SÍ   | Precio de venta sugerido por unidad en USD. Este es el precio de catálogo; el precio real facturado puede diferir (ver `sales.precio_unitario`).                | Mín: `7.85` · Máx: `17.50` · Prom: `~13.53`                   |
| `stock`           | `INT`       | SÍ   | Unidades disponibles en inventario al momento de la última carga ETL. No se actualiza en tiempo real con cada venta.                                            | Mín: `118` · Máx: `446`                                        |
| `marca`           | `LONGTEXT`  | SÍ   | Nombre de la marca o razón social del fabricante/proveedor del producto.                                                                                        | `"Cornejo-Garrido S.A."`, `"Limón-Saldaña"`, `"Chacón-Salazar"` |
| `_loadtime`       | `TIMESTAMP` | SÍ   | Fecha y hora de carga ETL. Campo de auditoría.                                                                                                                  | `"2025-06-26 19:34:32"`                                        |

#### Catálogo completo de productos

| id_producto | nombre_producto         | marca                         | precio_unitario | stock |
|-------------|-------------------------|-------------------------------|-----------------|-------|
| 1           | Detergente Multiusos    | Cornejo-Garrido S.A.          | 16.08           | 299   |
| 2           | Limpiador Desinfectante | Limón-Saldaña                 | 9.54            | 249   |
| 3           | Cloro Concentrado       | Chacón-Salazar                | 7.85            | 118   |
| 4           | Limpiavidrios           | Velásquez-Valdés S.A.         | 17.50           | 314   |
| 5           | Limpiador de Pisos      | Vásquez-Rodríguez y Asociados | 13.25           | 446   |

---

### `sales` — Ventas

Tabla de hechos principal del producto Comercial. Cada fila representa una **línea de venta** dentro de una factura: un producto vendido en una fecha, cantidad y precio determinados, en una sucursal específica a un cliente específico.

| Atributo      | Valor                                                         |
|---------------|---------------------------------------------------------------|
| Filas         | 100                                                           |
| Clave primaria| No definida formalmente (usar `cod_factura` como referencia) |
| Período       | `2025-05-27` a `2025-06-25` (~1 mes de datos)                |
| Carga ETL     | Batch — `_loadtime = 2025-06-26 19:34:51`                   |

#### Columnas

| Columna          | Tipo        | Nulo | FK                      | Descripción                                                                                                                                                     | Valores / Ejemplos                        |
|------------------|-------------|------|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------|
| `cod_factura`    | `INT`       | SÍ   | —                       | Número de factura comercial. Identifica el documento de venta. Una factura puede tener múltiples líneas (múltiples productos). 100 facturas únicas en el dataset. | `1` … `100`                              |
| `cod_sucursal`   | `INT`       | SÍ   | `shops.id_sucursal`     | Código de la sucursal donde se realizó la venta. Permite analizar desempeño por punto de venta y ubicación geográfica.                                          | `1` (Quito), `2` (Guayaquil), `3` (Cuenca) |
| `cod_cliente`    | `INT`       | SÍ   | `customers.id_cliente`  | Código del cliente que realizó la compra. Permite calcular frecuencia de compra, valor de vida del cliente (LTV) y segmentación.                                | `1` … `10`                               |
| `cod_producto`   | `INT`       | SÍ   | `products.id_producto`  | Código del producto vendido. Permite análisis de mix de ventas, productos más/menos vendidos y comparación con inventario.                                      | `1` … `5`                                |
| `fecha_venta`    | `DATE`      | SÍ   | —                       | Fecha en que se realizó la transacción de venta (formato `YYYY-MM-DD`). Usar para análisis de tendencias temporales, ventas por mes/semana/día.                | `"2025-05-27"` … `"2025-06-25"`          |
| `cantidad`       | `INT`       | SÍ   | —                       | Número de unidades del producto vendidas en esa línea de factura. Usar para calcular volumen de ventas en unidades.                                             | Mín: `1` · Máx: `5` · Prom: `2.8`       |
| `precio_unitario`| `DOUBLE`    | SÍ   | —                       | Precio efectivamente cobrado por unidad en la transacción, en USD. Puede diferir del precio de catálogo en `products.precio_unitario` por descuentos o acuerdos comerciales. | Mín: `2.52` · Máx: `19.92` · Prom: `~10.65` |
| `_loadtime`      | `TIMESTAMP` | SÍ   | —                       | Fecha y hora de carga ETL. Campo de auditoría.                                                                                                                  | `"2025-06-26 19:34:51"`                  |

#### Métricas derivadas clave

| Métrica                        | Fórmula SQL                                              |
|--------------------------------|----------------------------------------------------------|
| Monto total de una venta       | `cantidad * precio_unitario`                            |
| Ingresos totales               | `SUM(cantidad * precio_unitario)`                       |
| Ticket promedio por factura    | `SUM(cantidad * precio_unitario) / COUNT(DISTINCT cod_factura)` |
| Unidades vendidas              | `SUM(cantidad)`                                         |
| Ventas por cliente             | `GROUP BY cod_cliente`                                  |
| Ventas por sucursal            | `GROUP BY cod_sucursal`                                 |
| Ventas por producto            | `GROUP BY cod_producto`                                 |

#### Notas de calidad

- `sales` contiene ventas asociadas a `cod_sucursal` con valores fuera del rango de `shops.id_sucursal` (3 sucursales registradas, pero 4 distintas en ventas). Verificar integridad referencial antes de hacer JOIN con `shops`.
- No hay restricción de clave primaria formal; si una misma factura tiene múltiples productos, habrá múltiples filas con el mismo `cod_factura`.

---

### `shops` — Sucursales

Catálogo de puntos de venta físicos de la empresa. Las tres sucursales se encuentran en las principales ciudades del Ecuador, con sus coordenadas geográficas para análisis de geolocalización.

| Atributo      | Valor                                        |
|---------------|----------------------------------------------|
| Filas         | 3                                            |
| Clave primaria| `id_sucursal` (sin restricción PK en DDL)    |
| Carga ETL     | Batch — `_loadtime = 2025-06-26 19:34:50`   |

#### Columnas

| Columna           | Tipo        | Nulo | Descripción                                                                                                                                   | Valores / Ejemplos                                   |
|-------------------|-------------|------|-----------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------|
| `id_sucursal`     | `INT`       | SÍ   | Identificador único de la sucursal. Utilizar para hacer JOIN con `sales.cod_sucursal`.                                                       | `1`, `2`, `3`                                       |
| `nombre_sucursal` | `LONGTEXT`  | SÍ   | Nombre comercial de la sucursal, incluyendo ciudad y zona. Usar en reportes para identificar el punto de venta de forma legible.              | `"Sucursal Quito Sur"`, `"Sucursal Guayaquil Norte"` |
| `ciudad`          | `LONGTEXT`  | SÍ   | Ciudad donde está ubicada la sucursal. Permite análisis geográfico agregado a nivel de ciudad.                                               | `"Quito"`, `"Guayaquil"`, `"Cuenca"`               |
| `latitud`         | `DOUBLE`    | SÍ   | Coordenada geográfica de latitud de la sucursal (WGS84). Valores negativos indican hemisferio sur. Usar para mapas y análisis de proximidad. | `-0.251` (Quito), `-2.1406` (Guayaquil)             |
| `longitud`        | `DOUBLE`    | SÍ   | Coordenada geográfica de longitud de la sucursal (WGS84). Valores negativos indican al oeste del meridiano de Greenwich.                     | `-78.5243` (Quito), `-79.8891` (Guayaquil)          |
| `_loadtime`       | `TIMESTAMP` | SÍ   | Fecha y hora de carga ETL. Campo de auditoría.                                                                                               | `"2025-06-26 19:34:50"`                             |

#### Catálogo completo de sucursales

| id_sucursal | nombre_sucursal           | ciudad    | latitud  | longitud  |
|-------------|---------------------------|-----------|----------|-----------|
| 1           | Sucursal Quito Sur        | Quito     | -0.2510  | -78.5243  |
| 2           | Sucursal Guayaquil Norte  | Guayaquil | -2.1406  | -79.8891  |
| 3           | Sucursal Cuenca Centro    | Cuenca    | -2.8996  | -79.0045  |

---

## Consultas SQL de referencia

### Ventas totales por sucursal

```sql
SELECT
    sh.nombre_sucursal,
    sh.ciudad,
    COUNT(DISTINCT s.cod_factura)          AS total_facturas,
    SUM(s.cantidad)                        AS unidades_vendidas,
    ROUND(SUM(s.cantidad * s.precio_unitario), 2) AS ingresos_totales
FROM sales s
JOIN shops sh ON s.cod_sucursal = sh.id_sucursal
GROUP BY sh.id_sucursal, sh.nombre_sucursal, sh.ciudad
ORDER BY ingresos_totales DESC;
```

### Productos más vendidos (por ingresos)

```sql
SELECT
    p.nombre_producto,
    p.marca,
    SUM(s.cantidad)                              AS unidades_vendidas,
    ROUND(SUM(s.cantidad * s.precio_unitario), 2) AS ingresos_totales,
    ROUND(AVG(s.precio_unitario), 2)             AS precio_promedio_venta
FROM sales s
JOIN products p ON s.cod_producto = p.id_producto
GROUP BY p.id_producto, p.nombre_producto, p.marca
ORDER BY ingresos_totales DESC;
```

### Clientes con mayor gasto total (top 5)

```sql
SELECT
    c.id_cliente,
    c.nombre,
    c.email,
    c.estado,
    COUNT(DISTINCT s.cod_factura)                AS total_facturas,
    SUM(s.cantidad)                              AS unidades_compradas,
    ROUND(SUM(s.cantidad * s.precio_unitario), 2) AS gasto_total
FROM sales s
JOIN customers c ON s.cod_cliente = c.id_cliente
GROUP BY c.id_cliente, c.nombre, c.email, c.estado
ORDER BY gasto_total DESC
LIMIT 5;
```

### Ventas por mes

```sql
SELECT
    DATE_FORMAT(fecha_venta, '%Y-%m')            AS mes,
    COUNT(DISTINCT cod_factura)                  AS facturas,
    SUM(cantidad)                                AS unidades,
    ROUND(SUM(cantidad * precio_unitario), 2)    AS ingresos
FROM sales
GROUP BY mes
ORDER BY mes;
```

### Detalle completo de ventas (tabla desnormalizada)

```sql
SELECT
    s.cod_factura,
    s.fecha_venta,
    c.nombre              AS cliente,
    c.estado              AS estado_cliente,
    p.nombre_producto,
    p.marca,
    sh.nombre_sucursal,
    sh.ciudad,
    s.cantidad,
    s.precio_unitario     AS precio_venta,
    p.precio_unitario     AS precio_catalogo,
    ROUND(s.cantidad * s.precio_unitario, 2) AS subtotal
FROM sales s
JOIN customers c  ON s.cod_cliente  = c.id_cliente
JOIN products p   ON s.cod_producto = p.id_producto
JOIN shops sh     ON s.cod_sucursal = sh.id_sucursal
ORDER BY s.fecha_venta DESC, s.cod_factura;
```

### Stock vs ventas (análisis de rotación)

```sql
SELECT
    p.nombre_producto,
    p.stock                                  AS stock_actual,
    SUM(s.cantidad)                          AS unidades_vendidas,
    ROUND(SUM(s.cantidad) / p.stock * 100, 1) AS pct_rotacion
FROM products p
LEFT JOIN sales s ON s.cod_producto = p.id_producto
GROUP BY p.id_producto, p.nombre_producto, p.stock
ORDER BY pct_rotacion DESC;
```

---

## Glosario de negocio

| Término              | Definición                                                                                      |
|----------------------|-------------------------------------------------------------------------------------------------|
| **Factura**          | Documento de venta identificado por `cod_factura`. Puede contener múltiples líneas (productos). |
| **Línea de venta**   | Una fila en `sales`: un producto específico dentro de una factura.                              |
| **Ticket promedio**  | Valor promedio en USD por factura: `SUM(cantidad * precio_unitario) / COUNT(DISTINCT cod_factura)`. |
| **LTV (Life Time Value)** | Gasto total acumulado de un cliente: `SUM(cantidad * precio_unitario)` agrupado por `cod_cliente`. |
| **Sucursal**         | Punto de venta físico identificado por `cod_sucursal` / `id_sucursal`.                         |
| **Estado del cliente** | Indica si el cliente puede comprar: `activo` (habilitado) o `inactivo` (bloqueado/dado de baja). |
| **Precio catálogo**  | `products.precio_unitario` — precio oficial del producto.                                       |
| **Precio de venta**  | `sales.precio_unitario` — precio efectivamente cobrado, puede incluir descuentos.               |
| **_loadtime**        | Timestamp de carga ETL. Presente en todas las tablas. No representa fechas de negocio.         |

---

## Estadísticas del dataset

| Tabla       | Filas | Período de datos              | Particularidad                              |
|-------------|-------|-------------------------------|---------------------------------------------|
| `customers` | 10    | Carga única 2025-06-26        | 8 activos, 2 inactivos                      |
| `products`  | 5     | Carga única 2025-06-26        | Precios entre $7.85 y $17.50               |
| `sales`     | 100   | 2025-05-27 → 2025-06-25      | 100 facturas, 5 productos, 10 clientes      |
| `shops`     | 3     | Carga única 2025-06-26        | Quito, Guayaquil, Cuenca (Ecuador)          |
