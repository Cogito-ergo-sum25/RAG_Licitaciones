import pymysql
import json

def obtener_json_producto(id_producto):
    try:
        conexion = pymysql.connect(
            host='127.0.0.1',
            user='root',
            password='12345',
            database='mydb',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conexion.cursor() as cursor:
            sql = "SELECT especificaciones_tecnicas FROM producto_especificaciones WHERE id_producto = %s"
            cursor.execute(sql, (id_producto,))
            resultado = cursor.fetchone()
            
            if resultado:
                # Retorna el JSON listo para usar
                return json.loads(resultado['especificaciones_tecnicas'])
            return None
            
    except Exception as e:
        print(f"Error de base de datos: {e}")
    finally:
        if 'conexion' in locals():
            conexion.close()