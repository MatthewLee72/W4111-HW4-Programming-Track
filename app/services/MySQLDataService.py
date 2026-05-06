from __future__ import annotations

import os
import pymysql
import pymysql.cursors

from .AbstractBaseDataService import AbstractBaseDataService


class MySQLDataService(AbstractBaseDataService):
    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self._host = config.get("host", os.getenv("DB_HOST", "localhost"))
        self._port = int(config.get("port", os.getenv("DB_PORT", "3306")))
        self._user = config.get("user", os.getenv("DB_USER", "root"))
        self._password = config.get("password", os.getenv("DB_PASSWORD", ""))
        self._database = config.get("database", os.getenv("DB_NAME", "classicmodels"))
        self._table_name = config["table_name"]
        pk = config.get("primary_key_field", "id")
        self._pk_fields = [pk] if isinstance(pk, str) else list(pk)
        self._pk_separator = "::"

    def _get_connection(self):
        return pymysql.connect(
            host=self._host,
            port=self._port,
            user=self._user,
            password=self._password,
            database=self._database,
            cursorclass=pymysql.cursors.DictCursor,
        )

    def _split_pk(self, primary_key: str) -> tuple:
        parts = primary_key.split(self._pk_separator)
        if len(parts) != len(self._pk_fields):
            raise ValueError(
                f"Expected {len(self._pk_fields)} key part(s), got {len(parts)}"
            )
        return tuple(parts)

    def _pk_where_clause(self) -> str:
        return " AND ".join(f"{col} = %s" for col in self._pk_fields)

    def retrieveByPrimaryKey(self, primary_key: str) -> dict:
        parts = self._split_pk(primary_key)
        sql = f"SELECT * FROM {self._table_name} WHERE {self._pk_where_clause()}"
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, parts)
                result = cursor.fetchone()
        return result if result else {}

    def retrieveByTemplate(self, template: dict) -> list[dict]:
        if not template:
            sql = f"SELECT * FROM {self._table_name}"
        else:
            sql = f"SELECT * FROM {self._table_name} WHERE {' AND '.join(f'{col} = %s' for col in template.keys())}"
        
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, tuple(template.values()))
                result = cursor.fetchall()
        return result if result else []

    def create(self, payload: dict) -> str:
        if len(self._pk_fields) == 1:
            pk = self._pk_fields[0]
            if pk not in payload:
                sql_max = f"SELECT MAX({pk}) AS max_val FROM {self._table_name}"
                with self._get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(sql_max)
                        row = cursor.fetchone()
                        max_val = row["max_val"] if row and row["max_val"] is not None else 0
                        payload[pk] = max_val + 1

        sql = f"INSERT INTO {self._table_name} ({', '.join(payload.keys())}) VALUES ({', '.join(['%s'] * len(payload))})"
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, tuple(payload.values()))
                conn.commit()
        if all(f in payload for f in self._pk_fields):
            return self._pk_separator.join(str(payload[f]) for f in self._pk_fields)
        return str(cursor.lastrowid)


    def updateByPrimaryKey(self, primary_key: str, payload: dict) -> int:
        parts = self._split_pk(primary_key)
        set_clause = ", ".join(f"{col} = %s" for col in payload.keys())
        sql = f"UPDATE {self._table_name} SET {set_clause} WHERE {self._pk_where_clause()}"
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, tuple(payload.values()) + parts)
                conn.commit()
        return cursor.rowcount

    def deleteByPrimaryKey(self, primary_key: str) -> int:
        parts = self._split_pk(primary_key)
        sql = f"DELETE FROM {self._table_name} WHERE {self._pk_where_clause()}"
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, parts)
                conn.commit()
        return cursor.rowcount
