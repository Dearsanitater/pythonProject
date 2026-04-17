import switch

from db_refactor import ConnectionFactory, get_db_type


class db2_conn(switch.db2_conn):
    def __init__(self, conn):
        raw_conn = getattr(conn, "raw_connection", conn)
        super().__init__(raw_conn)


class read_case(switch.read_case):
    def __init__(self, incr, src, type, *args):
        super().__init__(incr, src, type, *args)
        self._factory = ConnectionFactory()

    def define(self, type, db=None):
        db_type = get_db_type(type)
        if db_type == "sqlserver" and db:
            target_key = db
        elif db and type == db:
            target_key = db
        else:
            target_key = db or type
        session = self._factory.create(target_key, explicit_type=db_type)
        self.type = db_type
        return session.raw_connection, db_type
