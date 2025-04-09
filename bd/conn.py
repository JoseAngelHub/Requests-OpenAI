import pymssql
from core.config import SERVER, PASSWORD, USERNAME, DATABASE_NAME

def get_connect_db():
    conn = pymssql.connect(SERVER, USERNAME, PASSWORD, DATABASE_NAME, autocommit=True)
    try:
        db = conn.cursor(as_dict=True)
        return db
    except Exception as e:
        return e