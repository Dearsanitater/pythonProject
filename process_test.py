from multiprocessing import Process, Queue,Pool
import os, time, random
import ptest
from django.http import JsonResponse,HttpResponse
import opg
import configparser


def _read_rule_config(parser):
    last_error = None
    for encoding in ('utf-8', 'gbk', 'utf-8-sig'):
        try:
            parser.read(r'resource/rule_config.ini', encoding=encoding)
            return encoding
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error:
        raise last_error
    return 'utf-8'


config=configparser.RawConfigParser()
_read_rule_config(config)
from concurrent.futures import ProcessPoolExecutor
process_pool = ProcessPoolExecutor(max_workers=4)
if __name__=='__ii__':
    #源库增量
    #q = Queue()
    set=[]#set=['db2','oracle']
    rule_dic=ptest.rule()
    print('\n',rule_dic)
    #print(rule_dic)
    #conn=opg.MysqlConn
    with Pool(4) as pool:
        pool.map(ptest.incr_switch, rule_dic)
if __name__ == '__main__':
    rule_id='42f3b9d1-c429-11ef-8f01-c025a5bfc3a3'
    print(type(rule_id))
    with ProcessPoolExecutor(max_workers=4) as pool:
        future = pool.submit(ptest.incr_switch, ptest.rule(rule_id))
        result = future.result()
        print(result)
        #return JsonResponse({"result": result})
# with Pool(4) as pool:
    #     pool.map(ptest.add_proc_task,set)
    # po = Process(target=opg.MysqlConn().open_obora, args=('ob_oracle',))
    # pm = Process(target=opg.MysqlConn().open, args=('ob_mysql',))
    # 启动子进程pw，写入:
    # po.start()
    # # 启动子进程pr，读取:
    # pm.start()
    # # 等待pw结束:
    # po.join()
    # pr进程里是死循环，无法等待其结束，只能强行终止:
    #p.terminate()

