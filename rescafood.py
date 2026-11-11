from datetime import datetime
import mysql.connector
import pandas as pd
import streamlit as st

# ==========================================
# CONFIGURACION DE LA PAGINA
# ==========================================

st.set_page_config(
    page_title="RESCAFOOD - Sistema Inteligente",
    page_icon="🌿",
    layout="wide"
)

# ==========================================
# ESTILOS CSS
# ==========================================

st.markdown("""
<style>
.stApp {
    background: linear-gradient(to bottom right, #f0f7f4, #e8f5e9);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #081c15 0%, #1b4332 100%);
    min-width: 340px !important;
    width: 340px !important;
}

[data-testid="stSidebar"] * {
    color: #ffffff !important;
}

[data-testid="stSidebar"] label {
    font-size: 20px !important;
    font-weight: 600 !important;
    padding: 8px 0px !important;
}

[data-testid="stSidebar"] input[type="radio"] {
    transform: scale(1.4) !important;
    margin-right: 12px !important;
}

div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #ffffff 0%, #d8f3dc 100%);
    border-left: 6px solid #2d6a4f;
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0 6px 15px rgba(45, 106, 79, 0.15);
}

h1, h2, h3 {
    color: #1b4332 !important;
    font-weight: 700 !important;
}

.stButton>button {
    background-color: #52b788;
    color: white;
    border-radius: 8px;
    font-weight: bold;
    border: none;
    padding: 0.5rem 1rem;
}

.stButton>button:hover {
    background-color: #2d6a4f;
    color: white;
}
</style>
""", unsafe_allow_html=True)


# ==========================================
# CONEXION A MYSQL
# ==========================================

def conectar_db():
    config = st.secrets["mysql"]
    
    return mysql.connector.connect(
        host=config["host"],
        port=int(config["port"]),
        user=config["user"],
        password=config["password"],
        database=config["database"],
        ssl_verify_cert=True,
        ssl_verify_identity=True
    )
# ==========================================
# CREACION DE TABLAS
# ==========================================

def inicializar_bd():

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            codigo INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            categoria VARCHAR(100) NOT NULL,
            cantidad INT NOT NULL,
            precio_original FLOAT NOT NULL,
            fecha_ingreso VARCHAR(20) NOT NULL,
            fecha_caducidad VARCHAR(20) NOT NULL,
            estado VARCHAR(100),
            descuento INT,
            precio_actual FLOAT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimientos_aprovechamiento (
            id INT AUTO_INCREMENT PRIMARY KEY,
            codigo_producto INT NOT NULL,
            nombre_producto VARCHAR(255) NOT NULL,
            tipo_movimiento VARCHAR(30) NOT NULL,
            cantidad INT NOT NULL,
            precio_unitario FLOAT NOT NULL DEFAULT 0,
            responsable_destino VARCHAR(255),
            fecha_movimiento DATETIME NOT NULL,
            FOREIGN KEY (codigo_producto)
            REFERENCES productos(codigo)
        )
    """)

    conexion.commit()
    cursor.close()
    conexion.close()


# ==========================================
# CALCULO DE DESCUENTOS
# ==========================================

def calcular_reglas_descuento(dias_restantes, precio_original):

    if dias_restantes > 5:
        descuento = 0
        estado = "Activo 🟢"

    elif dias_restantes in [5, 4]:
        descuento = 15
        estado = "Proximo a vencer - 15% 🟡"

    elif dias_restantes in [3, 2]:
        descuento = 30
        estado = "Proximo a vencer - 30% 🟠"

    elif dias_restantes == 1:
        descuento = 60
        estado = "Disponible Donacion / 60% 🔴"

    else:
        descuento = 100
        estado = "Caducado ❌"

    precio_actual = precio_original * (1 - descuento / 100)

    return descuento, estado, precio_actual


# ==========================================
# INICIALIZAR BASE DE DATOS
# ==========================================

inicializar_bd()


# ==========================================
# MENU LATERAL
# ==========================================

st.sidebar.markdown(
    '<h1 style="color: #52b788; text-align: center; '
    'font-size: 28px;">🌿 RESCAFOOD</h1>',
    unsafe_allow_html=True
)

st.sidebar.markdown(
    '<p style="text-align: center; color: #b7e4c7; '
    'font-size: 16px;">Gestión Inteligente de Perecederos</p>',
    unsafe_allow_html=True
)

st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navegación Principal",
    [
        "🏠  Inicio",
        "📦  Inventario",
        "➕  Registrar Producto",
        "🏷️  Descuentos",
        "🤝  Donaciones",
        "♻️  Aprovechamiento",
        "📊  Reportes"
    ]
)


# ==========================================
# CARGAR PRODUCTOS
# ==========================================

conexion = conectar_db()

df = pd.read_sql(
    "SELECT * FROM productos",
    conexion
)

conexion.close()


# ==========================================
# ACTUALIZAR ESTADOS SEGUN CADUCIDAD
# ==========================================

if not df.empty:

    hoy = datetime.now().date()

    conexion = conectar_db()
    cursor = conexion.cursor()

    for index, row in df.iterrows():

        f_cad = datetime.strptime(
            row["fecha_caducidad"], "%Y-%m-%d"
        ).date()

        dias = (f_cad - hoy).days

        desc, est, p_act = calcular_reglas_descuento(
            dias,
            row["precio_original"]
        )

        cursor.execute(
            """
            UPDATE productos
            SET estado = %s,
                descuento = %s,
                precio_actual = %s
            WHERE codigo = %s
            """,
            (est, desc, p_act, row["codigo"])
        )

    conexion.commit()
    cursor.close()
    conexion.close()

    conexion = conectar_db()

    df = pd.read_sql(
        "SELECT * FROM productos",
        conexion
    )

    conexion.close()


# ==========================================
# 1. VISTA INICIO - PANEL DE CONTROL
# ==========================================

if menu == "🏠  Inicio":

    st.title("🚀 Panel Principal - Rescafood")

    st.markdown(
        "### Control de inventario, vencimientos y aprovechamiento"
    )

    st.write(
        "Aquí puedes consultar el estado de los productos y "
        "conocer qué acciones debes realizar para evitar "
        "pérdidas y desperdicio de alimentos."
    )

    st.markdown("---")

    if not df.empty:

        # Crear una copia para organizar la información
        panel = df.copy()

        hoy = datetime.now().date()

        # Calcular días restantes para cada producto
        panel["fecha_caducidad"] = pd.to_datetime(
            panel["fecha_caducidad"]
        ).dt.date

        panel["Dias restantes"] = panel["fecha_caducidad"].apply(
            lambda fecha: (fecha - hoy).days
        )

        # Clasificar los productos
        panel["Situacion"] = panel["Dias restantes"].apply(
            lambda dias:
                "VENCIDO" if dias < 0
                else "VENCE HOY" if dias == 0
                else "PROXIMO A VENCER" if dias <= 5
                else "ACTIVO"
        )

        # Recomendar qué hacer con cada producto
        def recomendar_accion(fila):

            dias = fila["Dias restantes"]

            if dias < 0:
                return "♻️ Enviar a compostaje"

            elif dias == 0:
                return "⚠️ Atención inmediata: revisar y aprovechar hoy"

            elif dias == 1:
                return "🤝 Priorizar donación o venta inmediata"

            elif dias <= 5:
                return "🏷️ Aplicar descuento y priorizar venta"

            elif fila["descuento"] > 0:
                return "🛒 Mantener en promoción"

            else:
                return "✅ Mantener en inventario"

        panel["Accion recomendada"] = panel.apply(
            recomendar_accion,
            axis=1
        )

        # Clasificar productos
        proximos = panel[
            (panel["Dias restantes"] > 0)
            & (panel["Dias restantes"] <= 5)
        ]

        vencidos = panel[
            panel["Dias restantes"] < 0
        ]

        vencen_hoy = panel[
            panel["Dias restantes"] == 0
        ]

        descuentos = panel[
            panel["descuento"] > 0
        ]

        # Indicadores principales
        st.markdown("### 📊 Resumen del inventario")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "📦 Total productos",
            len(panel)
        )

        col2.metric(
            "⚠️ Próximos a vencer",
            len(proximos)
        )

        col3.metric(
            "❌ Productos vencidos",
            len(vencidos)
        )

        col4.metric(
            "🏷️ En descuento",
            len(descuentos)
        )

        st.markdown("---")

        # PRODUCTOS QUE VENCEN HOY
        st.markdown("### 🚨 Productos que vencen hoy")

        if vencen_hoy.empty:

            st.success(
                "No hay productos cuya fecha de vencimiento sea hoy."
            )

        else:

            st.warning(
                "Estos productos requieren atención inmediata."
            )

            st.dataframe(
                vencen_hoy[
                    [
                        "codigo",
                        "nombre",
                        "categoria",
                        "cantidad",
                        "fecha_caducidad",
                        "precio_actual",
                        "Accion recomendada"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )

        st.markdown("---")

        # PRODUCTOS PROXIMOS A VENCER
        st.markdown("### ⏳ Productos próximos a vencer")

        if proximos.empty:

            st.success(
                "No hay productos próximos a vencer en los siguientes 5 días."
            )

        else:

            st.warning(
                "Revisa estos productos y prioriza su venta o donación."
            )

            st.dataframe(
                proximos[
                    [
                        "codigo",
                        "nombre",
                        "categoria",
                        "cantidad",
                        "fecha_caducidad",
                        "Dias restantes",
                        "descuento",
                        "precio_original",
                        "precio_actual",
                        "Accion recomendada"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )

        st.markdown("---")

        # PRODUCTOS VENCIDOS
        st.markdown("### ❌ Productos vencidos")

        if vencidos.empty:

            st.success(
                "No hay productos vencidos registrados."
            )

        else:

            st.error(
                "Estos productos no deben venderse ni donarse. "
                "Revisa su estado y gestiona su destino como residuo."
            )

            st.dataframe(
                vencidos[
                    [
                        "codigo",
                        "nombre",
                        "categoria",
                        "cantidad",
                        "fecha_caducidad",
                        "Dias restantes",
                        "Accion recomendada"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )

        st.markdown("---")

        # PRODUCTOS EN DESCUENTO
        st.markdown("### 🏷️ Productos con descuento")

        if descuentos.empty:

            st.info(
                "Actualmente no hay productos con descuentos aplicados."
            )

        else:

            st.write(
                "Estos productos tienen un precio reducido según "
                "su fecha de caducidad."
            )

            st.dataframe(
                descuentos[
                    [
                        "codigo",
                        "nombre",
                        "cantidad",
                        "fecha_caducidad",
                        "Dias restantes",
                        "descuento",
                        "precio_original",
                        "precio_actual",
                        "Accion recomendada"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )

        st.markdown("---")

        # RECOMENDACIONES GENERALES
        st.markdown("### 💡 Recomendaciones del sistema")

        if len(vencidos) > 0:

            st.error(
                "♻️ COMPOSTAJE: revisa los productos vencidos y "
                "registra su aprovechamiento como compostaje."
            )

        if len(vencen_hoy) > 0:

            st.warning(
                "🚨 ATENCIÓN INMEDIATA: revisa los productos que "
                "vencen hoy y gestiona su destino antes de finalizar el día."
            )

        if len(proximos) > 0:

            st.info(
                "🏷️ VENTA Y DONACIÓN: prioriza los productos próximos "
                "a vencer. Puedes aplicar descuentos y registrar "
                "donaciones desde Aprovechamiento."
            )

        if len(descuentos) > 0:

            st.success(
                "🛒 PROMOCIONES: aprovecha los descuentos para "
                "incentivar la venta de los productos disponibles."
            )

        if (
            len(vencidos) == 0
            and len(vencen_hoy) == 0
            and len(proximos) == 0
        ):

            st.success(
                "✅ El inventario se encuentra sin productos "
                "próximos a vencer."
            )

    else:

        st.info(
            "📦 Todavía no hay productos registrados. "
            "Ingresa al módulo Registrar Producto para comenzar."
        )

# ==========================================
# 2. VISTA INVENTARIO
# ==========================================

elif menu == "📦  Inventario":

    st.title("📦 Módulo de Inventario Dinámico")

    st.markdown("---")

    if not df.empty:

        busqueda = st.text_input(
            "🔍 Buscar producto por nombre o categoría:"
        )

        if busqueda:

            df_filtrado = df[
                df["nombre"].str.contains(
                    busqueda, case=False, na=False
                )
                |
                df["categoria"].str.contains(
                    busqueda, case=False, na=False
                )
            ]

        else:

            df_filtrado = df

        st.dataframe(
            df_filtrado,
            use_container_width=True,
            hide_index=True
        )

        st.markdown("### 🗑️ Gestión de Retiro y Eliminación")

        id_eliminar = st.number_input(
            "Ingrese el Código (ID) del producto a eliminar:",
            min_value=0,
            step=1
        )

        if st.button("🗑️ Eliminar Producto"):

            if id_eliminar > 0:

                conexion = conectar_db()
                cursor = conexion.cursor()

                try:

                    cursor.execute(
                        "DELETE FROM productos WHERE codigo = %s",
                        (int(id_eliminar),)
                    )

                    conexion.commit()

                    st.success(
                        f"Producto con ID {id_eliminar} eliminado."
                    )

                    st.rerun()

                except mysql.connector.Error as error:

                    conexion.rollback()

                    st.error(
                        "No se puede eliminar este producto porque "
                        "tiene movimientos registrados. "
                        f"Detalle: {error}"
                    )

                finally:

                    cursor.close()
                    conexion.close()

    else:

        st.info(
            "📂 No hay productos registrados todavía. "
            "Añade el primero desde el menú lateral."
        )


# ==========================================
# 3. REGISTRAR PRODUCTO
# ==========================================

elif menu == "➕  Registrar Producto":

    st.title("➕ Registro de Nuevo Lote")

    st.markdown("---")

    with st.form("form_producto"):

        col_a, col_b = st.columns(2)

        with col_a:

            nombre = st.text_input("Nombre del producto")

            categoria = st.selectbox(
                "Categoría",
                [
                    "Fruver 🍎",
                    "Lácteos 🥛",
                    "Panadería 🍞",
                    "Carnes 🥩",
                    "Abarrotes 📦"
                ]
            )

            cantidad = st.number_input(
                "Cantidad disponible",
                min_value=1,
                step=1
            )

        with col_b:

            precio_original = st.number_input(
                "Precio original ($)",
                min_value=0.0,
                step=500.0
            )

            fecha_caducidad = st.date_input(
                "Fecha de caducidad"
            )

        submitted = st.form_submit_button(
            "💾 Guardar y Auditar Producto"
        )

        if submitted:

            if nombre.strip():

                f_ing = datetime.now().strftime("%Y-%m-%d")

                f_cad_str = fecha_caducidad.strftime("%Y-%m-%d")

                dias = (
                    fecha_caducidad - datetime.now().date()
                ).days

                desc, est, p_act = calcular_reglas_descuento(
                    dias,
                    precio_original
                )

                conexion = conectar_db()
                cursor = conexion.cursor()

                cursor.execute(
                    """
                    INSERT INTO productos
                    (
                        nombre,
                        categoria,
                        cantidad,
                        precio_original,
                        fecha_ingreso,
                        fecha_caducidad,
                        estado,
                        descuento,
                        precio_actual
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        nombre,
                        categoria,
                        int(cantidad),
                        precio_original,
                        f_ing,
                        f_cad_str,
                        est,
                        desc,
                        p_act
                    )
                )

                conexion.commit()
                cursor.close()
                conexion.close()

                st.success(
                    "🎉 Producto registrado exitosamente."
                )

            else:

                st.error(
                    "❌ Por favor ingrese el nombre del producto."
                )


# ==========================================
# 4. DESCUENTOS
# ==========================================

elif menu == "🏷️  Descuentos":

    st.title("🏷️ Módulo de Descuentos Escalonados")

    st.markdown("---")

    st.write(
        "Esquema comercial automatizado para incentivar "
        "la venta antes del vencimiento:"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("🟢 Más de 5 días: Precio normal (0%)")
        st.markdown("🟡 5 a 4 días restantes: 15% de descuento")
        st.markdown("🟠 3 a 2 días restantes: 30% de descuento")
        st.markdown("🔴 1 día restante: 60% de descuento")

    with col2:

        st.info(
            "💡 Beneficio comercial: recuperar parte del "
            "capital invertido y reducir el desperdicio."
        )


# ==========================================
# 5. DONACIONES
# ==========================================

elif menu == "🤝  Donaciones":

    st.title("🤝 Red de Donación y Apoyo Social")

    st.markdown("---")

    st.write(
        "Consulta los productos que han sido registrados "
        "como donaciones."
    )

    conexion = conectar_db()

    donaciones = pd.read_sql(
        """
        SELECT
            nombre_producto AS Producto,
            cantidad AS Cantidad,
            responsable_destino AS Beneficiario,
            fecha_movimiento AS Fecha
        FROM movimientos_aprovechamiento
        WHERE tipo_movimiento = 'Donación'
        ORDER BY fecha_movimiento DESC
        """,
        conexion
    )

    conexion.close()

    if donaciones.empty:

        st.info(
            "Todavía no se han registrado donaciones."
        )

    else:

        st.dataframe(
            donaciones,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Unidades de alimentos donadas",
            int(donaciones["Cantidad"].sum())
        )


# ==========================================
# 6. APROVECHAMIENTO: VENTA, DONACION O COMPOSTAJE
# ==========================================

elif menu == "♻️  Aprovechamiento":

    st.title("♻️ Gestión de aprovechamiento de productos")

    st.write(
        "Selecciona un producto y decide si se venderá, "
        "se donará o se destinará al compostaje. "
        "La cantidad se descontará del inventario."
    )

    st.markdown("---")

    if df.empty:

        st.warning(
            "No hay productos registrados. "
            "Primero agrega productos al inventario."
        )

    else:

        disponibles = df[df["cantidad"] > 0].copy()

        if disponibles.empty:

            st.info(
                "No hay existencias disponibles para gestionar."
            )

        else:

            opciones = {
                int(row["codigo"]): (
                    f'{row["nombre"]} | ID {int(row["codigo"])} | '
                    f'Stock: {int(row["cantidad"])}'
                )
                for _, row in disponibles.iterrows()
            }

            with st.form("form_aprovechamiento"):

                codigo = st.selectbox(
                    "Selecciona el producto:",
                    options=list(opciones.keys()),
                    format_func=lambda x: opciones[x]
                )

                producto = disponibles[
                    disponibles["codigo"] == codigo
                ].iloc[0]

                destino = st.radio(
                    "¿Qué deseas hacer con el producto?",
                    ["Venta", "Donación", "Compostaje"],
                    horizontal=True
                )

                cantidad = st.number_input(
                    "Cantidad que deseas gestionar:",
                    min_value=1,
                    max_value=int(producto["cantidad"]),
                    value=1,
                    step=1
                )

                if destino == "Venta":

                    st.info(
                        f"Precio unitario con descuento: "
                        f"${float(producto['precio_actual']):,.2f}"
                    )

                    responsable = st.text_input(
                        "Nombre del comprador (opcional)"
                    )

                elif destino == "Donación":

                    responsable = st.text_input(
                        "Nombre de la fundación o beneficiario"
                    )

                else:

                    responsable = st.text_input(
                        "Responsable o lugar de compostaje (opcional)"
                    )

                    st.caption(
                        "Los residuos orgánicos pueden aprovecharse "
                        "para producir compost."
                    )

                confirmar = st.form_submit_button(
                    "Confirmar movimiento"
                )

            if confirmar:

                fecha_caducidad = datetime.strptime(
                    str(producto["fecha_caducidad"]),
                    "%Y-%m-%d"
                ).date()

                vencido = (
                    fecha_caducidad < datetime.now().date()
                )

                if vencido and destino in ["Venta", "Donación"]:

                    st.error(
                        "El producto está vencido y no se puede "
                        "vender ni donar. Puedes registrarlo "
                        "para compostaje."
                    )

                elif destino == "Donación" and not responsable.strip():

                    st.error(
                        "Debes indicar quién recibirá la donación."
                    )

                else:

                    precio = (
                        float(producto["precio_actual"])
                        if destino == "Venta"
                        else 0.0
                    )

                    conexion = conectar_db()
                    cursor = conexion.cursor()

                    try:

                        cursor.execute(
                            """
                            SELECT cantidad
                            FROM productos
                            WHERE codigo = %s
                            FOR UPDATE
                            """,
                            (int(codigo),)
                        )

                        existencia = cursor.fetchone()

                        if (
                            existencia is None
                            or int(existencia[0]) < int(cantidad)
                        ):

                            conexion.rollback()

                            st.error(
                                "La cantidad disponible cambió. "
                                "Actualiza la página e inténtalo nuevamente."
                            )

                        else:

                            cursor.execute(
                                """
                                UPDATE productos
                                SET cantidad = cantidad - %s
                                WHERE codigo = %s
                                """,
                                (int(cantidad), int(codigo))
                            )

                            cursor.execute(
                                """
                                INSERT INTO movimientos_aprovechamiento
                                (
                                    codigo_producto,
                                    nombre_producto,
                                    tipo_movimiento,
                                    cantidad,
                                    precio_unitario,
                                    responsable_destino,
                                    fecha_movimiento
                                )
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                                """,
                                (
                                    int(codigo),
                                    str(producto["nombre"]),
                                    destino,
                                    int(cantidad),
                                    precio,
                                    responsable.strip(),
                                    datetime.now()
                                )
                            )

                            conexion.commit()

                            if destino == "Venta":

                                total = precio * int(cantidad)

                                st.success(
                                    f"Venta registrada correctamente. "
                                    f"Total: ${total:,.2f}. "
                                    "El inventario fue actualizado."
                                )

                            elif destino == "Donación":

                                st.success(
                                    "Donación registrada correctamente. "
                                    "El inventario fue actualizado."
                                )

                            else:

                                st.success(
                                    "Producto destinado al compostaje. "
                                    "El inventario fue actualizado."
                                )

                            st.rerun()

                    except Exception as error:

                        conexion.rollback()

                        st.error(
                            f"No se pudo registrar el movimiento: {error}"
                        )

                    finally:

                        cursor.close()
                        conexion.close()

    # HISTORIAL DE MOVIMIENTOS

    st.markdown("### 📋 Historial de aprovechamiento")

    conexion = conectar_db()

    historial = pd.read_sql(
        """
        SELECT
            nombre_producto AS Producto,
            tipo_movimiento AS Destino,
            cantidad AS Cantidad,
            precio_unitario AS 'Precio unitario',
            responsable_destino AS 'Comprador / Beneficiario / Responsable',
            fecha_movimiento AS Fecha
        FROM movimientos_aprovechamiento
        ORDER BY fecha_movimiento DESC
        """,
        conexion
    )

    conexion.close()

    if historial.empty:

        st.info(
            "Todavía no hay ventas, donaciones o registros de compostaje."
        )

    else:

        st.dataframe(
            historial,
            use_container_width=True,
            hide_index=True
        )


# ==========================================
# 7. REPORTES
# ==========================================

elif menu == "📊  Reportes":

    st.title("📊 Panel de Impacto y Sostenibilidad")

    st.markdown("---")

    conexion = conectar_db()

    resumen = pd.read_sql(
        """
        SELECT
            tipo_movimiento,
            COALESCE(SUM(cantidad), 0) AS total
        FROM movimientos_aprovechamiento
        GROUP BY tipo_movimiento
        """,
        conexion
    )

    conexion.close()

    totales = dict(
        zip(resumen["tipo_movimiento"], resumen["total"])
    )

    vendidos = int(totales.get("Venta", 0))
    donados = int(totales.get("Donación", 0))
    compostados = int(totales.get("Compostaje", 0))

    col1, col2, col3 = st.columns(3)

    col1.metric("🛒 Productos vendidos", vendidos)
    col2.metric("💚 Productos donados", donados)
    col3.metric("🌱 Productos compostados", compostados)

    st.markdown("### 📊 Distribución del aprovechamiento")

    chart_data = pd.DataFrame({
        "Destino": [
            "Venta",
            "Donación",
            "Compostaje"
        ],
        "Cantidad": [
            vendidos,
            donados,
            compostados
        ]
    })

    st.bar_chart(
        chart_data,
        x="Destino",
        y="Cantidad",
        color="#2d6a4f"
    )
