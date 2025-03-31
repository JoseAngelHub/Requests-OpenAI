import pymssql
from core.config import SERVER, PASSWORD, USERNAME, DATABASE_NAME

"""class Database:
    def __init__(self):
        self.connection_string = (
            f"DRIVER={DRIVER};SERVER={SERVER};"
            f"DATABASE={DATABASE_NAME};UID={USERNAME};PWD={PASSWORD}"
        )
        self.connection = None

    def connect(self):
        try:
            self.connection = pyodbc.connect(self.connection_string)
            logger.info("Conexión a la base de datos establecida correctamente")
        except Exception as e:
            logger.error(f"Error al conectar a la base de datos: {e}")
            self.connection = None

    def disconnect(self):
        if self.connection:
            self.connection.close()
            logger.info("Conexión a la base de datos cerrada")

    def execute_query(self, query, fetch_one=False):
        result = None
        if not self.connection:
            self.connect()
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            if fetch_one:
                result = cursor.fetchone()
            else:
                result = cursor.fetchall()
            logger.info("Consulta ejecutada exitosamente")
        except Exception as e:
            logger.error(f"Error al ejecutar la consulta: {e}")
        return result

    def execute_update(self, query):
        if not self.connection:
            self.connect()
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            self.connection.commit()
            logger.info("Consulta de actualización ejecutada exitosamente")
        except Exception as e:
            logger.error(f"Error al ejecutar consulta de actualización: {e}")

    def __del__(self):
        self.disconnect()"""

def get_connect_db():
    conn = pymssql.connect(SERVER, USERNAME, PASSWORD, DATABASE_NAME, autocommit=True)
    try:
        db = conn.cursor(as_dict=True)
        return db
    except Exception as e:
        return e