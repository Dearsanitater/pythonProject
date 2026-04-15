import os,importlib,django,paramiko
import jpype,jpype.imports,sys
from jpype import JClass
import thrift,thrift_sasl,threading
from queue import Queue

from jpype.types import *
import time
import configparser
jvm_path=r"C:\Program Files\Java\jre1.8.0_201\bin\server\jvm.dll"
config = configparser.ConfigParser(interpolation=None)
config.read(r'resource/config.ini', encoding='utf-8')
#dbname='hyperbase184'


def open_hbase(dbname):
    T1 = T2 = 0;exc_thd, rcv_thd = config.get(dbname, 'exec_threads'), config.get(dbname,'recv_threads')  # hbase_client DRIVER
    ifKerberos = config.get(dbname, 'ker');principal = config.get(dbname, 'principle');keytab = config.get(dbname, 'kpath')
    print(principal, keytab)
    try:
        T1 = time.perf_counter()
        jars = [os.path.join("lib/hbase", i) for i in os.listdir("lib/hbase") if i.endswith(".jar")]
        # 前缀认证
        if ifKerberos == 1:
            jars.append('lib/hyperlib')
            jpype.startJVM(
                "-Djava.security.krb5.conf=lib/krb5.ini",
                "-Djava.security.auth.login.config=lib/hyperlib/jaas.conf",
                "-Dsun.security.krb5.debug=true",
                # "-Dnetworkaddress.cache.ttl=0",
                "-Dfile.encoding=UTF-8",
                "-Djavax.security.auth.useSubjectCredsOnly=false", classpath=jars, jvmpath=jvm_path)
            java_lang_System = jpype.JPackage("java").lang.System
            java_lang_System.setOut(jpype.java.io.PrintStream(jpype.java.io.FileOutputStream("C:\\temp\\jvm_krb5.log")))
            java_lang_System.setErr(jpype.java.io.PrintStream(jpype.java.io.FileOutputStream("C:\\temp\\jvm_krb5_err.log")))
            from org.apache.hadoop.security import UserGroupInformation
            from org.apache.hadoop.conf import Configuration
            conf = Configuration()
            conf.set("hadoop.security.authentication", "kerberos")
            UserGroupInformation.setConfiguration(conf)
            UserGroupInformation.loginUserFromKeytab(principal, keytab)
            print('kerberos票据获取已获取,ugi用户', UserGroupInformation.getCurrentUser())
            from org.apache.hadoop.hbase import HBaseConfiguration
            hbase_conf = HBaseConfiguration.create()
            ugi = UserGroupInformation.getLoginUser()
            from java.security import PrivilegedExceptionAction
            from org.apache.hadoop.hbase.client import ConnectionFactory
            def run():
                return ConnectionFactory.createConnection(hbase_conf)
            action = jpype.JProxy(PrivilegedExceptionAction, dict(run=run))
            conn = ugi.doAs(action)
        else:
            jpype.startJVM(
                "-Dfile.encoding=UTF-8",
                classpath=jars,
                jvmpath=jvm_path
                )
            print('未启用kerberos认证')
            from org.apache.hadoop.hbase import HBaseConfiguration
            from org.apache.hadoop.hbase.client import ConnectionFactory
            from org.apache.hadoop.conf import Configuration
            hbase_conf = HBaseConfiguration.create()
            hbase_conf.set("hbase.zookeeper.quorum", "10.1.111.184")
            hbase_conf.set("hbase.zookeeper.property.clientPort", "2181")
            # 如果有 znode parent 也要加
            hbase_conf.set("zookeeper.znode.parent", "/hbase")
            conn = ConnectionFactory.createConnection(hbase_conf)
            print("HBase 无认证连接成功:", conn)
        print('stablish conn done')
        T2 = time.perf_counter()
    except Exception as e:
        print(f"数据库连接失败！{e}")
        return
    # print(conn, f"hyper 数据库连接成功")
    # conn_pool = Queue()
    # for i in range(int(exc_thd)):
    #    conn_pool.put(ugi.doAs(action))
    # print('THD hyperbase 链接耗时:%f毫秒' % (((T2 - T1) * 1000)))
    return conn

class connFactory():
    def __init__(self,dbname):
        self.conn=open_hbase(dbname)
        self.all_value=[]
        self.src_col = {'tab_num': 0, 'tab_name': '', 'tab_col': []}
        self.col={'col_name': '', 'col_num': 1, 'len': None, 'null': 'NO', 'num_pre': 1, 'num_scale': 1, 'time_sh': None, 'type': 'text'}
        #self.conn_pool=Queue()
        self.schema=config.get(dbname,'namespace')
        self.Configuration = JClass("org.apache.hadoop.conf.Configuration")
        self.HBaseConfiguration = JClass("org.apache.hadoop.hbase.HBaseConfiguration")
        self.ConnectionFactory = JClass("org.apache.hadoop.hbase.client.ConnectionFactory")
        self.TableName = JClass("org.apache.hadoop.hbase.TableName")
        self.Scan = JClass("org.apache.hadoop.hbase.client.Scan")
        self.ResultScanner = JClass("org.apache.hadoop.hbase.client.ResultScanner")
        self.Bytes = JClass("org.apache.hadoop.hbase.util.Bytes")
        self.Admin = JClass("org.apache.hadoop.hbase.client.Admin")
    def scan_tb(self,tblist):
        conn=self.conn
        tbno=0;final=[]
        try:
            for tbname in tblist:
                sctbname=f'{self.schema}:'+tbname;tbno+=1
                scan = self.Scan()
                table = conn.getTable(self.TableName.valueOf(sctbname))
                scanner=table.getScanner(scan)
                result_dict={};new_value={};n=0;tmp=[]
                for result in scanner:
                    rowkey = self.Bytes.toString(result.getRow())#1
                    #colkey = n
                    row_data = {}
                    for cell in result.listCells():
                        cf = self.Bytes.toString(cell.getFamilyArray(), cell.getFamilyOffset(), cell.getFamilyLength())
                        qual = self.Bytes.toString(cell.getQualifierArray(), cell.getQualifierOffset(), cell.getQualifierLength())
                        val = self.Bytes.toString(cell.getValueArray(), cell.getValueOffset(), cell.getValueLength())
                        row_data[f"{qual}"] = val
                    if len(row_data)>n:n+=1
                    else:n=len(row_data)#记录最多字段行，n是tmp列表的索引
                    tmp.append(row_data.copy())
                scanner.close()
                table.close()
                result_dict['tab_col'],new_value['tab_col'] = self.pret_col(tmp,n);result_dict['tab_name']=tbname;result_dict['tab_num']=tbno
                new_value['tab_name']=tbname
                final.append(result_dict)
                self.all_value.append(new_value)
            #print(final)
            return tbno,final
        finally:
            #self.conn_pool.put(conn)
            print(row_data)
            pass

    def pret_col(self,tmp,n):#按照tmp中字段最多的行来确定表的字段结构，n是该行在tmp中的索引，tmp是所有行的列表
        tab_col=[]
        col = {'col_name': '', 'col_num': 1, 'len': None, 'null': 'NO', 'num_pre': 1, 'num_scale': 1, 'time_sh': None,'type': 'text'}
        if not tmp:
            return [],[]

        for item in list(tmp[n-1].keys()):
            col['col_name']=item
            tab_col.append(col.copy())
        all_keys = set().union(*tmp)
        new_tmp = [{k: d.get(k,'') for k in all_keys} for d in tmp]
        #print(new_tmp)
                #standard=(standard+(tmp[n-1]-standard)).copy
        return  tab_col,new_tmp
    def hb_tab(self):
        conn=self.conn
        admin=conn.getAdmin()
        tbs=admin.listTableNamesByNamespace(self.schema)
        result=[]
        for t in tbs:
            result.append(str(t.getQualifierAsString()))
        #self.conn_pool.put(conn)
        return result
    def get_conn(self,dbname):
        return open_hbase(dbname)
if __name__=='__main__':
    cf=connFactory('hyperbase184')
    cf.hb_tab()
    cf.scan_tb(cf.hb_tab())
    #scan_table(conn,"dbo:tab_nopk1")