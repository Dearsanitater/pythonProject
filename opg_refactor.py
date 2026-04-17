

from db_refactor import ConnectionFactory, get_db_type


class MysqlConn():
    def __init__(self, database):
        #super().__init__(database)
        self.database = database
        self._factory = ConnectionFactory()
        self._session = None

    def _open_with_factory(self, explicit_type=None):
        self._session = self._factory.create(self.database, explicit_type=explicit_type or get_db_type(self.database))
        self.currentConn = self._session.raw_connection
        try:
            self.cursor = self.currentConn.cursor()
        except Exception:
            self.cursor = None
        return self.currentConn

    def open(self):
        return self._open_with_factory()

    def open_mssql(self):
        return self._open_with_factory("sqlserver")

    def open_oracle(self):
        return self._open_with_factory("oracle")

    def open_pg(self):
        return self._open_with_factory("postgre")

    def open_clickhouse(self):
        return self._open_with_factory("clickhouse")

    def open_dm(self):
        return self._open_with_factory("dm")

    def open_db2_odbc(self):
        return self._open_with_factory("db2")

    def open_as400_odbc(self):
        return self._open_with_factory("db2_as400")

    def open_obora(self):
        return self._open_with_factory("ob_oracle")

    def open_hive(self):
        return self._open_with_factory("hive")
