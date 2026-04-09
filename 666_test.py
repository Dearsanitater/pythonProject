from jpype import startJVM, getDefaultJVMPath, JClass, shutdownJVM
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import threading

# --- 启动 JVM ---
startJVM(getDefaultJVMPath(), "-Djava.class.path=/path/to/hbase-client.jar")

# --- HBase Java 类 ---
Configuration = JClass("org.apache.hadoop.conf.Configuration")
HBaseConfiguration = JClass("org.apache.hadoop.hbase.HBaseConfiguration")
ConnectionFactory = JClass("org.apache.hadoop.hbase.client.ConnectionFactory")
TableName = JClass("org.apache.hadoop.hbase.TableName")
Scan = JClass("org.apache.hadoop.hbase.client.Scan")
ResultScanner = JClass("org.apache.hadoop.hbase.client.ResultScanner")

# --- HBase 配置 ---
conf = HBaseConfiguration.create()
conf.set("hbase.zookeeper.quorum", "127.0.0.1")
conf.set("hbase.zookeeper.property.clientPort", "2181")

# --- 创建固定数量的连接池 ---
POOL_SIZE = 5
conn_pool = Queue()
for _ in range(POOL_SIZE):
    conn_pool.put(ConnectionFactory.createConnection(conf))

# --- 表名列表 ---
table_list = ["table1", "table2", "table3", "table4", "table5", "table6", "table7", "table8"]

# --- 线程安全队列存查询结果 ---
result_queue = Queue()


# --- 工作函数 ---
def scan_table(table_name):
    conn = conn_pool.get()  # 从连接池取 Connection
    try:
        table = conn.getTable(TableName.valueOf(table_name))
        scan = Scan()
        scanner = table.getScanner(scan)

        table_dict = {}
        for result in scanner:
            for cell in result.listCells():
                key = str(cell.getQualifierArray()[
                          cell.getQualifierOffset():cell.getQualifierOffset() + cell.getQualifierLength()])
                value = str(cell.getValueArray()[cell.getValueOffset():cell.getValueOffset() + cell.getValueLength()])
                table_dict[key] = value

        scanner.close()
        table.close()

        result_queue.put((table_name, table_dict))  # 直接消费结果
    finally:
        conn_pool.put(conn)  # 放回连接池


# --- 线程池执行 ---
with ThreadPoolExecutor(max_workers=POOL_SIZE) as executor:
    futures = [executor.submit(scan_table, table_name) for table_name in table_list]
    # 等待所有任务完成
    for f in futures:
        f.result()

# --- 汇总结果 ---
final_dict = {}
while not result_queue.empty():
    table_name, table_dict = result_queue.get()
    final_dict[table_name] = table_dict

print(final_dict)

# --- 关闭所有连接 ---
while not conn_pool.empty():
    conn_pool.get().close()

shutdownJVM()