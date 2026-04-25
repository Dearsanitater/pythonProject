#子进程函数文件
import configparser,time
import io
import os,time,random
import sys
import opg
import switch
import ergodic
import compare
import compare_refactor as cr
import openpyxl
import sqlite3
from django.http import HttpResponse
from channels.layers import get_channel_layer
from multiprocessing import Process, Queue, Pool,Manager
#from crm.apps.api.apps import ApiConfig
import crm.apps.api.apps as apps
from django.conf import settings
cfg_dir=f'{settings.BASE_DIR}/resource/rule_config.ini'


def _read_rule_config(parser):
    # 规则配置文件历史上不是纯 UTF-8，这里兼容 GBK。
    last_error = None
    for encoding in ('utf-8', 'gbk', 'utf-8-sig'):
        try:
            parser.read(cfg_dir, encoding=encoding)
            return encoding
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error:
        raise last_error
    return 'utf-8'

config=configparser.RawConfigParser()
_read_rule_config(config)
print("Current working directory:", os.getcwd())

def rule(section,s):
    rule_dic = []
    config = configparser.RawConfigParser()
    _read_rule_config(config)
    #set = {section: dict(config.items(section)) for section in config.sections()}
    set =dict(config[f'{section}'])
    config.read(f'{settings.BASE_DIR}/resource/DB.ini',encoding='utf-8')
    if set['src']=='db2':type_c='db2'
    else:type_c=0
    c = {
        'rule': set['rule_name'],
        'src': set['src'],
        'tgt': set['tgt'],
        'type': config.get(f"{set['src']}",'type'),
        'db':type_c,
        'conn':None,
        'rule_id':set['rule_id'],
        'if_unique':set['unique_number'],
        'usrid':set['user_id'],
        'tgt_type':dict(config[f"{set['tgt']}"])['type']
    }
    if s == 's':
        c['conn']=opg.MysqlConn(set['src'])
        conn = c['conn']
        method_map = {
            "ob_oracle": conn.open_obora, "ob_mysql": conn.open, "mysql": conn.open, "sqlserver": conn.open_mssql,
            "oracle": conn.open_oracle,
            "postgre": conn.open_pg, "db2": conn.open_db2_odbc
        }
        c['conn'] = method_map[f"{c['type']}"]
    else:
        pass
    #rule_dic.append(c)
    return c
def get_rule():
    file_path = cfg_dir
    #print(f"Last modified: {os.path.getmtime(cfg_dir)}")
    config = configparser.RawConfigParser()
    _read_rule_config(config)
    set = {section: dict(config.items(section)) for section in config.sections()}
    return set
def _stop_requested(control):
    if isinstance(control, dict):
        control = control.get('stop_event')
    return bool(control and control.is_set())
def incr_switch(args,control=None):#调用swich执行sql用例
    print(f'进程号{os.getpid()}执行开始,更改输出流至queuemaintainer')
    old_stdout = sys.stdout#更改输出流
    queue_stdout = apps.QueueMaintainer(args['rule_id'],os.getpid(),args['usrid'])
    sys.stdout = queue_stdout
    print(f'进程号{os.getpid()},更改输出流完毕')
    #print(f'进程号{os.getpid()}执行完毕，s总共耗时：\t\t毫秒')
    try:
        conn=args['conn']()
        event=control
        pre_crt = 1#     每个用例文件统一建表后再进行dml、ddl等操作      ，1开启此项，默认0-false
        #mssql, type = p.define(type)
        p = switch.read_case(int(args['if_unique']), args['type'],args['db'] ,switch.db2_case)
        T1 = time.perf_counter()
        for casefile in p.ergodic(args['type']):
            if _stop_requested(control):
                print('收到停止指令，停止继续执行后续case文件')
                break
            p.analysis(casefile,pre_crt)
            p.execute(conn,event)
            if _stop_requested(control):
                print('收到停止指令，当前流程已结束')
                break
        T2 = time.perf_counter()
        print(f'进程号{os.getpid()}执行完毕，s总共耗时：\t\t%f毫秒' % ((T2 - T1) * 1000))
    except Exception as e:
        print(f'子进程异常_{e}')
    finally:
        sys.stdout = old_stdout
        queue_stdout.stop()
    print('恢复输出流\nsubprocess done')
def start_comp(args, control=None):
    print(f'进程号{os.getpid()}执行开始,更改输出流至queuemaintainer')
    old_stdout = sys.stdout  # 更改输出流
    queue_stdout = apps.QueueMaintainer(args['rule_id'], os.getpid(), args['usrid'])
    sys.stdout = queue_stdout
    try:
        print(f'进程号{os.getpid()},更改输出流完毕')#看情况选择是否需要工厂模式提供连接，部分数据库可能不支持
        #print(f'进程号{os.getpid()}执行完毕，s总共耗时：\t\t毫秒')
        #p=compare.ergodic_database()
        p=cr.ergodic_database()#djgano选用工厂提供连接
        dump_excel = ergodic.get_casefile()
        # err_handling
        # 1：自动忽略所有无主键，2：忽略所有出错表，3：忽略所有问题表，4：手动选择
        # if_cpdata 1:比较内容，0 不比较内容
        err_handling, if_cpdata=3,1
        print(args['src'], args['tgt'])
        start_time=time.monotonic()
        p.compare(args['src'], args['tgt'], err_handling, if_cpdata, control=control)
        print('总耗时%.2f毫秒' % ((time.monotonic() - start_time) * 1000))
        p.dump_e(dump_excel)
        print('恢复输出流\nsubprocess done\n记录report和规则关系到表')
    finally:
        sys.stdout = old_stdout
        queue_stdout.stop()
    wb = openpyxl.load_workbook('resource/test_report/report.xlsx', data_only=True)
    last_sheet = wb.worksheets[-1].title
    conn = sqlite3.connect('identifier.sqlite')
    cursor=conn.cursor()
    #记录比对结果工作表sheet和ruleid
    sql = f'''insert into main.report_map (uid,tbname)values('{args['rule_id']}','{last_sheet}')'''
    cursor.execute(sql)
    conn.commit()
    conn.close()
    print(sql)

