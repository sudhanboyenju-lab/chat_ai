from abc import ABC, abstractmethod


class BaseConnector(ABC):
    """Every database backend (MySQL, Postgres, Mongo...) implements this same interface.
    The engine only ever talks to THIS interface, never to a specific database library."""

    @abstractmethod
    def get_all_entities(self, config):
        """Return a dict: {entity_id: {name, detail_field_1, ..., "documents": [...]}}"""
        raise NotImplementedError

    @abstractmethod
    def add_entity(self, config, entity_id, fields: dict, documents: list[str]):
        raise NotImplementedError

    @abstractmethod
    def update_entity(self, config, entity_id, fields: dict, documents: list[str]):
        raise NotImplementedError

    @abstractmethod
    def delete_entity(self, config, entity_id):
        raise NotImplementedError

    def get_dependencies(self, config):
        """Optional: return {entity_id: [{"requires": other_entity_id, "note": str}, ...]}
        for situation-based guidance. Default: no dependency data available -
        subclasses only need to override this if config.dependency_table is used."""
        return {}


class MySQLConnector(BaseConnector):
    def __init__(self, get_connection_fn):
        """get_connection_fn: a zero-argument function returning a mysql.connector connection
        (reuses whatever connection setup the project already has, e.g. your existing db.py)."""
        self.get_connection = get_connection_fn

    def get_all_entities(self, config):
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(f"SELECT * FROM {config.entity_table}")
        rows = cursor.fetchall()

        entities = {}
        for row in rows:
            entity_id = row[config.entity_id_field]
            entities[entity_id] = {f: row[f] for f in [config.entity_name_field, *config.detail_fields]}
            entities[entity_id]["documents"] = []

        if config.child_table:
            cursor.execute(
                f"SELECT {config.child_fk_field}, {config.child_value_field} FROM {config.child_table}"
            )
            child_rows = cursor.fetchall()
            for row in child_rows:
                eid = row[config.child_fk_field]
                if eid in entities:
                    entities[eid]["documents"].append(row[config.child_value_field])

        cursor.close()
        conn.close()
        return entities

    def get_dependencies(self, config):
        if not config.dependency_table:
            return {}

        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            f"SELECT {config.dependency_from_field}, {config.dependency_requires_field}, "
            f"{config.dependency_note_field} FROM {config.dependency_table}"
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        dependencies = {}
        for row in rows:
            entity_id = row[config.dependency_from_field]
            dependencies.setdefault(entity_id, []).append({
                "requires": row[config.dependency_requires_field],
                "note": row.get(config.dependency_note_field),
            })
        return dependencies

    def add_entity(self, config, entity_id, fields: dict, documents: list[str]):
        conn = self.get_connection()
        cursor = conn.cursor()

        columns = [config.entity_id_field, *fields.keys()]
        placeholders = ", ".join(["%s"] * len(columns))
        values = [entity_id, *fields.values()]

        cursor.execute(
            f"INSERT INTO {config.entity_table} ({', '.join(columns)}) VALUES ({placeholders})",
            values
        )

        if config.child_table:
            for doc in documents:
                cursor.execute(
                    f"INSERT INTO {config.child_table} ({config.child_fk_field}, {config.child_value_field}) VALUES (%s, %s)",
                    (entity_id, doc)
                )

        conn.commit()
        cursor.close()
        conn.close()

    def update_entity(self, config, entity_id, fields: dict, documents: list[str]):
        conn = self.get_connection()
        cursor = conn.cursor()

        set_clause = ", ".join([f"{k}=%s" for k in fields])
        cursor.execute(
            f"UPDATE {config.entity_table} SET {set_clause} WHERE {config.entity_id_field}=%s",
            [*fields.values(), entity_id]
        )

        if config.child_table:
            cursor.execute(
                f"DELETE FROM {config.child_table} WHERE {config.child_fk_field}=%s", (entity_id,)
            )
            for doc in documents:
                cursor.execute(
                    f"INSERT INTO {config.child_table} ({config.child_fk_field}, {config.child_value_field}) VALUES (%s, %s)",
                    (entity_id, doc)
                )

        conn.commit()
        cursor.close()
        conn.close()

    def delete_entity(self, config, entity_id):
        conn = self.get_connection()
        cursor = conn.cursor()

        if config.child_table:
            cursor.execute(
                f"DELETE FROM {config.child_table} WHERE {config.child_fk_field}=%s", (entity_id,)
            )
        cursor.execute(
            f"DELETE FROM {config.entity_table} WHERE {config.entity_id_field}=%s", (entity_id,)
        )

        conn.commit()
        cursor.close()
        conn.close()