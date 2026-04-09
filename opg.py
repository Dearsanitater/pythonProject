import os,importlib,django,paramiko
import jpype,jpype.imports
from jpype.types import *
import pymysql
import pymssql
import logging
import time
import configparser
import cx_Oracle
import psycopg2
import pyodbc
import clickhouse_driver
import dmPython
import jaydebeapi
import ibm_db
from concurrent.futures import ThreadPoolExecutor
import threading
from pyhive import hive
try:
    from django.conf import settings
    if settings:
        os.chdir(settings.BASE_DIR)
except :
    pass
logger = logging.getLogger(__name__)  #操作日志对象
#-*- coding:utf-8 -*-
config = configparser.ConfigParser(interpolation=None)
config.read(r'resource/config.ini', encoding='utf-8')
#print(os.getcwd())
import pdb
class MysqlConn():

    def __init__(self,database):
        self.currentConn = None
        print(database)
        #pdb.set_trace()
        self.host = config.get(database,'host')
        self.user = config.get(database,'username')
        self.password = config.get(database,'password')
        self.dbName = config.get(database,'databasename')
        self.port = config.getint(database, 'port')
        if database.endswith('gbk'):
            self.charset = "GBK"
        else:
            self.charset = "utf8"
        self.resultlist = []
    def open(self):#mysql类
        T1=T2=0
        try:
            T1=time.perf_counter()
            conn = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                db=self.dbName,
                port=self.port
            )
            #print(self.charset)
            T2=time.perf_counter()
        except pymysql.err.OperationalError as e:
            logger.exception("数据库连接失败！")

        print("mysql数据库连接成功")
        print('%s链接耗时:%f毫秒'%(self.host,((T2 - T1) * 1000)))
        logger.info(f"mysql数据库连接成功")
        self.currentConn = conn  # 数据库连接完成
        self.cursor = self.currentConn.cursor()  # 游标，用来执行数据库
        return self.currentConn
    def open_mssql(self):
        T1=T2=0
        drive_name='ODBC Driver 18 for SQL Server'
        try:
            T1=time.perf_counter()
            #conn = pymssql.connect(host=self.host,user=self.user,password=self.password,database=self.dbName,port=self.port,charset=self.charset)
            conn = pyodbc.connect(f'DRIVER={drive_name};SERVER={self.host};DATABASE={self.dbName};UID={self.user};PWD={self.password};TrustServerCertificate=yes;')
            T2=time.perf_counter()
        except pymysql.err.OperationalError as e:
            logger.exception("数据库连接失败！")
        #print("数据库连接成功\t版本为：%s"%conn.cursor().connection.server_version)
        print('mssql %s 链接耗时: %f毫秒'%(self.host,((T2 - T1) * 1000)))
        logger.info(f"mssql数据库连接成功")
        self.currentConn = conn  # 数据库连接完成
        self.cursor = self.currentConn.cursor()  # 游标，用来执行数据库
        return self.currentConn
    def open_oracle(self):
        T1=T2=0
        p = '%s:%d/%s' % (self.host, self.port, self.dbName)
        try:
            T1=time.perf_counter()

            conn = cx_Oracle.connect(self.user,self.password,p)
            conn.cursor().execute("ALTER SESSION SET NLS_LANGUAGE='AMERICAN'")
            conn.cursor().execute("ALTER SESSION SET NLS_TIMESTAMP_FORMAT='YYYY-MM-DD HH24:MI:SS.FF6'")
            conn.cursor().execute("ALTER SESSION SET NLS_TIMESTAMP_TZ_FORMAT = 'YYYY-MM-DD HH24:MI:SS.FF7 TZH:TZM'")

            T2=time.perf_counter()
        except cx_Oracle.OperationalError as e:
            logger.exception("数据库连接失败！")

        def pretreatment_oracle(cursor, name, default_type, size, precision, scale):
            # HOOK,oracle不对时区进行转换，直接转字符串
            if default_type in (cx_Oracle.DATETIME, cx_Oracle.TIMESTAMP):
                return cursor.var(cx_Oracle.STRING, arraysize=cursor.arraysize)
            return None  # 其他类型使用默认处理
        conn.outputtypehandler= pretreatment_oracle
        print('oracle %s链接耗时: %f毫秒'%(self.host,((T2 - T1) * 1000)))
        logger.info(f"mssql数据库连接成功")
        self.currentConn = conn  # 数据库连接完成
        self.cursor = self.currentConn.cursor()  # 游标，用来执行数据库
        return self.currentConn
    def open_pg(self):
        T1=T2=0
        #p = '%s:%d/%s' % (self.host, self.port, self.dbName)
        try:
            T1=time.perf_counter()
            schema = config.get('postgre', 'schema')
            conn = psycopg2.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.dbName,
                port=self.port,
                client_encoding=self.charset
                ,options='''-c search_path=%s'''%schema
            )
            #set=f'set search_path to {schema}'
            #set = f'ALTER DATABASE {self.dbName} SET search_path TO {schema}'
            T2=time.perf_counter()
        except cx_Oracle.OperationalError as e:
            logger.exception("数据库连接失败！")
        set=0
        print('pg %s链接耗时:%f毫秒\n%s'%(self.host,((T2 - T1) * 1000),set))
        logger.info(f"pg数据库连接成功")
        #ALTER DATABASE your_database_name SET search_path TO %s
        self.currentConn = conn  # 数据库连接完成
        self.cursor = self.currentConn.cursor()  # 游标，用来执行数据库
        #self.cursor.execute(f'{set}')
        return self.currentConn
    def open_clickhouse(self):
        T1=T2=0
        #p = '%s:%d/%s' % (self.host, self.port, self.dbName)
        try:
            T1=time.perf_counter()

            conn = clickhouse_driver.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.dbName,
                port=self.port
            )
            T2=time.perf_counter()
        except cx_Oracle.OperationalError as e:
            logger.exception("数据库连接失败！")
        print('clickhouse %s链接耗时:%f毫秒'%(self.host,((T2 - T1) * 1000)))
        #logger.info(f"pg数据库连接成功")
        self.currentConn = conn  # 数据库连接完成
        self.cursor = self.currentConn.cursor()  # 游标，用来执行数据库
        return self.currentConn
    def open_dm(self):
        T1=T2=0
        dm_python_path = os.path.dirname(dmPython.__file__)
        print("dmPython 安装目录:", dm_python_path)
        try:
            T1=time.perf_counter()
            conn = dmPython.connect(host=self.host,user=self.user,password=self.password,port=self.port,local_code=1)

            T2=time.perf_counter()
        except pymysql.err.OperationalError as e:
            logger.exception("数据库连接失败！")
        #print("数据库连接成功\t版本为：%s"%conn.cursor().connection.server_version)
        print('\ndm %s 链接耗时: %f毫秒'%(self.host,((T2 - T1) * 1000)))
        #print(f"dm数据库连接成功")
        self.currentConn = conn  # 数据库连接完成
        self.cursor = self.currentConn.cursor()  # 游标，用来执行数据库
        return self.currentConn
    def open_db2_odbc(self):
        T1 = T2 = 0
        #IBM DB2 ODBC DRIVER
        try:
            T1 = time.perf_counter()
            dbinfo = (f"DATABASE={self.dbName};HOSTNAME={self.host};PORT={self.port};PROTOCOL=TCPIP;UID={self.user.upper()};PWD={self.password}")
            conn = ibm_db.connect(dbinfo, "", "")
            T2=time.perf_counter()
        except pyodbc.OperationalError as e:
            logger.exception("数据库连接失败！%s",e)
        print('ibm_db2 %s链接耗时:%f毫秒'%(self.host,((T2 - T1) * 1000)))
        print(f"db2 数据库连接成功")
        self.currentConn = conn  # 数据库连接完成,DB2回传连接id
        #self.cursor = self.currentConn.cursor()  # 游标，用来执行数据库
        return self.currentConn

    def open_dm_odbc(self):
        T1=T2=0
        try:
            T1=time.perf_counter()
            conn = pyodbc.connect(
                'DRIVER={DM Driver};SERVER=self.host;UID=self.user;PWD=self.password;DATABASE=self.dbName;charset=self.charset;'
            )
            #conn = ibm_db_dbi.connect("database=***;hostname=你的数据库ip地址;port=端口号;protocol=通信协议（tcp/ip）;UID=用户;PWD=密码","","")
            T2=time.perf_counter()
        except pymysql.err.OperationalError as e:
            logger.exception("数据库连接失败！")

        print("\nDM数据库连接成功")
        print('%s链接耗时:%f毫秒'%(self.host,((T2 - T1) * 1000)))
        self.currentConn = conn  # 数据库连接完成
        self.cursor = self.currentConn.cursor()  # 游标，用来执行数据库
        return self.currentConn
    def open_as400_odbc(self):
        T1=T2=0
        try:
            T1=time.perf_counter()
            conn = pyodbc.connect(
                #DRIVER='{iSeries Access ODBC Driver}',
                DRIVER='{IBM I Access ODBC Driver}',
                system=f'{self.host}',
                UID=f'{self.user}',PWD=f'{self.password}',
                DBQ=f'{self.dbName}',charset=f'{self.charset}'
            )
            #conn = ibm_db_dbi.connect("database=***;hostname=你的数据库ip地址;port=端口号;protocol=通信协议（tcp/ip）;UID=用户;PWD=密码","","")
            T2=time.perf_counter()
        except pymysql.err.OperationalError as e:
            logger.exception("数据库连接失败！")
        print("\nas400数据库连接成功")
        print('%s链接耗时:%f毫秒'%(self.host,((T2 - T1) * 1000)),f'DB={self.dbName}')
        self.currentConn = conn  # 数据库连接完成
        self.cursor = self.currentConn.cursor()  # 游标，用来执行数据库
        return self.currentConn
    def open_obora(self):
        T1 = T2 = 0#jdbc ob_client
        ob_jar=r'lib/oceanbase-client-2.4.1.jar'
        drive='com.alipay.oceanbase.jdbc.Driver'
        jdbc_url = rf"jdbc:oceanbase://{self.host}:{self.port}/{self.dbName}"  # 这里加入了集群名称参数ALTER TABLE t_col_update MODIFY
        username = f"{self.user}"
        password = fr"{self.password}"
        a = drive, jdbc_url, [username, password], ob_jar
        try:
            T1 = time.perf_counter()
            conn=jaydebeapi.connect(drive,jdbc_url,[username, password], ob_jar)
            T2=time.perf_counter()
        except pyodbc.OperationalError as e:
            logger.exception("数据库连接失败！%s",e)
        print(f'ob oracle {a}%s链接耗时:%f毫秒'%(self.host,((T2 - T1) * 1000)))
        print(f"ob oracle 数据库连接成功")
        self.currentConn = conn  # 数据库连接完成
        self.cursor = self.currentConn.cursor()  # 游标，用来执行数据库
        print(self.currentConn)
        return self.currentConn
    def open_hive(self):
        T1=T2=0
        try:
            T1=time.perf_counter()
            # conn = hive.Connection(host='cdh1',username=self.user,port=self.port
            #                     ,kerberos_service_name='hive',auth='KERBEROS',database=self.dbName)
            conn = hive.Connection(
                host='cdh1',  # HiveServer2 主机名
                port=10000,  # HiveServer2 端口号
                auth='KERBEROS',  # 使用 Kerberos 认证
                kerberos_service_name='hive',  # Kerberos 服务名称
                database='default'  # 默认数据库
            )
            T2=time.perf_counter()
        except pymysql.err.OperationalError as e:
            logger.exception("数据库连接失败！")
        #print("数据库连接成功\t版本为：%s"%conn.cursor().connection.server_version)
        print('\nhive %s 链接耗时: %f毫秒'%(self.host,((T2 - T1) * 1000)))
        #print(f"dm数据库连接成功")
        self.currentConn = conn  # 数据库连接完成
        self.cursor = self.currentConn.cursor()  # 游标，用来执行数据库
        return self.currentConn
    def open_hbase(self):

        #self.currentConn = conn  # 数据库连接完成,DB2回传连接id
        #self.cursor = self.currentConn.cursor()  # 游标，用来执行数据库
        return self.currentConn
    def open_hbase_shell(self):
        T1=T2=0
        td_exec=int(config.get('hyperbase','exec_threads'))
        threadPool = ThreadPoolExecutor(max_workers=td_exec, thread_name_prefix="test_")
        try:
            T1=time.perf_counter()
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=self.host, username=self.user, password=self.password)
            # for i in range(td_exec):
            #     threadPool.map(self.ssh_ivk,ssh)

            channel = ssh.invoke_shell()

            channel.send("hbase shell -n\n")
            T2=time.perf_counter()
        except pymysql.err.OperationalError as e:
            logger.exception("数据库连接失败！")
        #print("数据库连接成功\t版本为：%s"%conn.cursor().connection.server_version)
        print('\nhive %s 链接耗时: %f毫秒'%(self.host,((T2 - T1) * 1000)))
        #print(f"dm数据库连接成功")

        return self.currentConn
    def spliteSql(self,sql):
        sqllist = sql.split(';')
        return sqllist[0:-1]
        #最后面会多一条空值
    def execSql(self,sql:str,closeConn = True):
        '''执行sql,支持执行多条sql语句。'''
        self.open()
        sqllist = self.spliteSql(sql)  #先处理传入的sql语句
        logger.info(f"开始执行sql语句")
        with self.cursor as my_cursor:
            for i in sqllist:
                my_cursor.execute(i)         #执行sql语句
                self.resultlist = my_cursor.fetchall()  #获取数据
                self.currentConn.commit()        #提交
        if self.currentConn:
            self.close()
        return self.resultlist
    # def execProc(self):
    def close(self):  #关闭连接
        logger.info(f"关闭数据库连接")
        if self.cursor:
            self.cursor.close()
        self.currentConn.close()

if __name__ == '__main__':
    #print('PyCharm')
    # config = configparser.ConfigParser()
    # config.read(r'C:\Users\DELL\PycharmProjects\pythonProject\resource\config.ini', encoding='utf-8')
    # mysqlconn=MysqlConn('mysql')
    # #print(mysqlconn.host,mysqlconn.port,'\n',mysqlconn.dbName,mysqlconn.password)
    # mysqlconn.open()
    #mssqlconn=MysqlConn('db2').open_db2_odbc()
    mssqlconn = MysqlConn('hyperbase').open_hbase()
    #mssqlconn.open_oracle()
    #mssqlconn.open_db2_odbc()
    #mssqlconn.open_obora()
    #mssqlconn.open_dm()
    #mssqlconn.open_clickhouse()
    #mssqlconn.open_mssql()
    #mssqlconn.open_dm()
    #mysqlconn.open()
    # mysqlconn=MysqlConn('pg')
    # mysqlconn.open_pg()