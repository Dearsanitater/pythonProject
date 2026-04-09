from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from hbase import Hbase
from hbase.ttypes import *


class HbaseClient(object):
    def __init__(self, host='172.20.77.196', port=19090):
        self.transport = TTransport.TBufferedTransport(TSocket.TSocket(host, port))
        protocol = TBinaryProtocol.TBinaryProtocol(self.transport)
        self.client = Hbase.Client(protocol)

    def get_tables(self):
        self.transport.open()
        tables = self.client.getTableNames()
        self.transport.close()
        return tables