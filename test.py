import sqlite3
from sqlite3 import Error
from decimal import Decimal


def conn_db(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    return conn


def create_table_if_not_exists(conn, tableName):
    try:
        c = conn.cursor()
        c.execute(f"CREATE TABLE IF NOT EXISTS '{tableName}' ("
                  "school_name TEXT,"
                  "country TEXT,"
                  "oversea_course TEXT,"
                  "oversea_code TEXT,"
                  "ust_course TEXT,"
                  "ust_code TEXT,"
                  "credit INTEGER,"
                  "ref TEXT"
                  ")")
    except Error as e:
        print(e)


def insert_data(conn, tableName, data):
    try:
        c = conn.cursor()

        c.execute(f"INSERT INTO '{tableName}' VALUES (?,?,?,?,?,?,?,?)", data)
    except Error as e:
        print(e)


def search(conn, tableName, school_name=None, country=None, oversea_course=None, oversea_code=None, ust_course=None, ust_code=None, credit=None, ref=None):
    try:
        c = conn.cursor()
        query = {
            "school_name": school_name,
            "country": country,
            "oversea_course": oversea_course,
            "oversea_code": oversea_code,
            "ust_course": ust_course,
            "ust_code": ust_code,
            "credit": credit,
            "ref": ref
        }

        def make_query_str(key, value):
            if type(value) == str:
                return f"{key}='{value}'"
            elif type(value) == int:
                return f"{key}={value}"
            else:
                return f"UNIMPLEMENTED TYPE {type(value)}"

        query_str = " AND ".join([make_query_str(key, value)
                                  for key, value in query.items() if value is not None])

        print(f"SELECT * FROM '{tableName}'" + (f"WHERE {query_str}" if len(query_str) > 0 else ""))
        return c.execute(f"SELECT * FROM '{tableName}'" + (f"WHERE {query_str}" if len(query_str) > 0 else "")).fetchall()

    except Error as e:
        print(e)


if __name__ == "__main__":
    conn = conn_db("credit_transfer.db")
    if conn is not None:
        # create_table_if_not_exists(conn, "test")
        print(conn.cursor().execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchone())
        # print(conn.cursor().execute("SELECT * from test").fetchall())
        # search(conn, "test", school_name="HAHA", credit=7)
        import re
        # print(int(re.findall(r'\d+', "7 credits")[0]))
        # conn.cursor().execute(f"INSERT INTO '2022-23 Spring_Any_COMP' VALUES ('sdff', 'adsf', 'asdfgg' ,'adg' ,'hsd', 'adf' , 3, 'asdga')")
        # print(conn.cursor().execute(f"SELECT * FROM '2022-23 Spring_Any_COMP'").fetchall())
        print(search(conn, "2022-23 Spring_Any_COMP", country="Denmark"))
        # conn.cursor().execute("DELETE FROM '2022-23 Spring_Any_COMP' WHERE school_name='sdff'")
        conn.commit()
        conn.cursor().close()
        conn.close()
        
