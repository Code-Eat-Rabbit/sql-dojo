"""MySQL 连接层：练习库 schema 管理（替代原 SQLite 单文件模式）"""

import time

import pymysql

MYSQL_HOST = "127.0.0.1"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = "practice"


def connect(schema: str | None = None) -> pymysql.connections.Connection:
    """返回 utf8mb4、autocommit 的 PyMySQL 连接，可选直连某个 schema"""
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=schema,
        charset="utf8mb4",
        autocommit=True,
    )


def reset_schema(schema: str) -> pymysql.connections.Connection:
    """DROP + CREATE 指定 schema，返回已选中该 schema 的连接"""
    conn = connect()
    with conn.cursor() as cur:
        cur.execute(f"DROP DATABASE IF EXISTS `{schema}`")
        cur.execute(f"CREATE DATABASE `{schema}` CHARACTER SET utf8mb4")
    conn.select_db(schema)
    return conn


def wait_for_mysql(timeout: int = 60) -> None:
    """轮询等待 MySQL 可连接，超时抛 SystemExit"""
    deadline = time.time() + timeout
    last_err = None
    while time.time() < deadline:
        try:
            connect().close()
            return
        except pymysql.err.OperationalError as e:
            last_err = e
            time.sleep(1)
    raise SystemExit(f"MySQL 在 {timeout}s 内不可达（127.0.0.1:3306）: {last_err}")


if __name__ == "__main__":
    wait_for_mysql()
    conn = connect()
    with conn.cursor() as cur:
        cur.execute("SELECT VERSION()")
        print("MySQL OK, version:", cur.fetchone()[0])
    conn.close()
