import pymysql
import json

def obtener_conexion():
    return pymysql.connect(
        host='127.0.0.1',
        user='root',       # Tus credenciales locales
        password='12345',
        database='mydb',
        port=3306,
        cursorclass=pymysql.cursors.DictCursor
    )

def obtener_todos_los_productos():
    """Trae la lista de productos haciendo JOIN con TODAS sus tablas relacionales"""
    try:
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            # Hacemos JOIN de marcas, tipos, clasificaciones, paises y certificaciones
            sql = """
                SELECT 
                    p.id_producto, 
                    p.nombre, 
                    p.modelo,
                    p.sku,
                    p.imagen_url,
                    p.ficha_tecnica_url,
                    m.nombre AS marca, 
                    t.nombre AS tipo,
                    c.nombre AS clasificacion,
                    pa.nombre AS pais,
                    GROUP_CONCAT(cert.nombre SEPARATOR ', ') AS certificaciones
                FROM productos p
                LEFT JOIN marcas m ON p.id_marca = m.id_marca
                LEFT JOIN tipos_producto t ON p.id_tipo = t.id_tipo
                LEFT JOIN clasificaciones c ON p.id_clasificacion = c.id_clasificacion
                LEFT JOIN paises pa ON p.id_pais_origen = pa.id_pais
                LEFT JOIN producto_certificaciones pc ON p.id_producto = pc.id_producto
                LEFT JOIN certificaciones cert ON pc.id_certificacion = cert.id_certificacion
                GROUP BY p.id_producto
                ORDER BY m.nombre ASC, p.nombre ASC
            """
            cursor.execute(sql)
            return cursor.fetchall()
    except Exception as e:
        print(f"Error al obtener productos: {e}")
        return []
    finally:
        if 'conexion' in locals():
            conexion.close()

def obtener_json_producto(id_producto):
    """Obtiene el JSON si ya existe en producto_especificaciones"""
    try:
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            sql = "SELECT especificaciones_tecnicas FROM producto_especificaciones WHERE id_producto = %s"
            cursor.execute(sql, (id_producto,))
            resultado = cursor.fetchone()
            if resultado:
                # Ojo: devolvemos como texto para poder editarlo en la pantalla
                return resultado['especificaciones_tecnicas'] 
            return "{}" # Si no hay nada, devolvemos un JSON vacío
    except Exception as e:
        print(f"Error al obtener JSON: {e}")
        return "{}"
    finally:
        if 'conexion' in locals():
            conexion.close()

def guardar_json_producto(id_producto, json_texto):
    """Guarda o actualiza el JSON en la base de datos"""
    try:
        # Validamos que el texto sea un JSON real antes de guardarlo
        json_valido = json.loads(json_texto) 
        
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            # Insertamos, y si ya existe el id_producto, lo actualizamos (Comando ninja de MySQL)
            sql = """
                INSERT INTO producto_especificaciones (id_producto, especificaciones_tecnicas)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE especificaciones_tecnicas = %s
            """
            cursor.execute(sql, (id_producto, json.dumps(json_valido), json.dumps(json_valido)))
        conexion.commit()
        return True, "JSON guardado correctamente."
    except json.JSONDecodeError:
        return False, "❌ Error: El texto introducido no es un JSON válido. Revisa las comillas o comas."
    except Exception as e:
        return False, f"❌ Error de BD: {e}"
    finally:
        if 'conexion' in locals():
            conexion.close()

def obtener_equipos_por_tag(tag_buscado):
    """Filtra en la BD todos los equipos que tengan el tag específico en su JSON"""
    try:
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            # Traemos todos los productos que ya tienen JSON guardado
            sql = """
                SELECT p.id_producto, p.nombre, p.modelo, m.nombre AS marca, pe.especificaciones_tecnicas
                FROM producto_especificaciones pe
                JOIN productos p ON pe.id_producto = p.id_producto
                LEFT JOIN marcas m ON p.id_marca = m.id_marca
            """
            cursor.execute(sql)
            resultados = cursor.fetchall()
            
            equipos_filtrados = []
            for fila in resultados:
                try:
                    import json
                    json_datos = json.loads(fila['especificaciones_tecnicas'])
                    # Hacemos el match exacto con el tag
                    if json_datos.get("tag_licitacion") == tag_buscado:
                        fila['json_limpio'] = json_datos # Guardamos el diccionario listo
                        equipos_filtrados.append(fila)
                except Exception as e:
                    continue
                    
            return equipos_filtrados
    except Exception as e:
        print(f"Error al filtrar equipos: {e}")
        return []
    finally:
        if 'conexion' in locals():
            conexion.close()

def obtener_lista_tipos_maestra():
    """Trae la lista viva de tipos de producto desde MySQL"""
    try:
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("SELECT nombre FROM tipos_producto ORDER BY nombre ASC")
            # Convertimos los resultados en una lista simple de strings
            return [fila['nombre'] for fila in cursor.fetchall()]
    except Exception as e:
        print(f"Error al obtener tipos: {e}")
        return []
    finally:
        if 'conexion' in locals():
            conexion.close()

def obtener_lista_clasificaciones_maestra():
    """Trae la lista viva de clasificaciones desde MySQL"""
    try:
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("SELECT nombre FROM clasificaciones ORDER BY nombre ASC")
            return [fila['nombre'] for fila in cursor.fetchall()]
    except Exception as e:
        print(f"Error al obtener clasificaciones: {e}")
        return []
    finally:
        if 'conexion' in locals():
            conexion.close()

def obtener_todas_las_plantillas():
    """Trae las plantillas de la BD y las formatea como diccionario"""
    try:
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            sql = "SELECT tag_licitacion, nombre_boton, reglas_especificas, esquema_base FROM ai_plantillas_extraccion"
            cursor.execute(sql)
            resultados = cursor.fetchall()
            
            plantillas_dict = {}
            for fila in resultados:
                # Convertimos el JSON de texto de MySQL a un diccionario de Python
                plantillas_dict[fila['tag_licitacion']] = {
                    "nombre_boton": fila['nombre_boton'],
                    "reglas_especificas": fila['reglas_especificas'],
                    "esquema": json.loads(fila['esquema_base'])
                }
            return plantillas_dict
    except Exception as e:
        print(f"Error al obtener plantillas de BD: {e}")
        return {}
    finally:
        if 'conexion' in locals():
            conexion.close()

def guardar_plantilla_bd(tag, nombre_boton, reglas_especificas, esquema_dict):
    """Inserta o actualiza una plantilla en MySQL"""
    try:
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            esquema_json = json.dumps(esquema_dict, ensure_ascii=False)
            sql = """
                INSERT INTO ai_plantillas_extraccion (tag_licitacion, nombre_boton, reglas_especificas, esquema_base)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    nombre_boton = VALUES(nombre_boton),
                    reglas_especificas = VALUES(reglas_especificas),
                    esquema_base = VALUES(esquema_base)
            """
            cursor.execute(sql, (tag, nombre_boton, reglas_especificas, esquema_json))
        conexion.commit()
        return True, "Plantilla guardada correctamente en BD."
    except Exception as e:
        return False, f"Error al guardar plantilla en BD: {e}"
    finally:
        if 'conexion' in locals():
            conexion.close()