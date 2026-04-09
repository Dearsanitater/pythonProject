from django.apps import AppConfig
import os,json,pandas
import openpyxl
import multiprocessing
from multiprocessing import Queue,Process,Manager,Event
import queue
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import threading,sys
import ptest,process_test,configparser,sqlite3,uuid
from concurrent.futures import ProcessPoolExecutor
from django.http import JsonResponse,HttpResponse,FileResponse
from django.shortcuts import render,redirect
from django.conf import settings
os.chdir(settings.BASE_DIR)
config_file=r'resource/rule_config.ini'
MEDIA_PATH = os.getenv("EXCEL_MEDIA_PATH", "resource/test_report/report.xlsx")
OUTPUT_PATH = os.getenv("EXCEL_OUTPUT_PATH", "resource/test_report/tmp.xlsx")
process_pool = ProcessPoolExecutor(max_workers=4)
#conn = sqlite3.connect('identifier.sqlite')
exec_task={"rule_id":None}


def exec_switch(request,rule_id):

    #future = process_pool.submit(ptest.incr_switch,ptest.rule(rule_id,'s'))
    stop_event = Event()
    rule_obj=ptest.rule(rule_id,'s')
    p = Process(target=ptest.incr_switch, args=(rule_obj,stop_event))
    p.start()
    try:
        task_id=p.pid
        print('已加入进程池',task_id)
        exec_task[rule_id] = {
            "future": p,'pid':task_id,'stop_event':stop_event
        }
    except Exception as e:
        return JsonResponse({"error": "未知错误", "message": str(e)})
    return redirect('/rule')
def exec_compare(request,rule_id):
    future = process_pool.submit(ptest.start_comp, ptest.rule(rule_id, 'd'))
    try:
        exec_task[rule_id] = {
            "future": future,
            "task_id": rule_id,
        }
        task_id=str(future)
        print('已加入进程池',task_id)
    except Exception as e:
        return JsonResponse({"error": "未知错误", "message": str(e)})
    return redirect('/rule')
def create_rule(request):
    if request.method == 'POST':
        # 获取表单参数
        user_id = int(request.POST.get('user_id'))
        rule_name = request.POST.get('rule_name')
        rule_id = uuid.uuid1()#uuid
        src = request.POST.get('src')
        tgt = request.POST.get('tgt')
        unique_number = int(request.POST.get('unique_number'))
        error_handler = int(request.POST.get('error_handler'))
        print(type(rule_name))
        try:
              # 连接到数据库
            conn = sqlite3.connect('identifier.sqlite')
            cursor = conn.cursor()
            cursor.execute(f'''
                            INSERT INTO main.rule_cmp (user_id, rule_name, rule_id, src, tgt, unique_number, error_handler)
                            VALUES ({user_id}, '{rule_name}', '{rule_id}', '{src}', '{tgt}', {unique_number}, {error_handler})
                        ''')
            conn.commit()  # 提交事务
            conn.close()
            #return redirect('/rule')
        except sqlite3.Error as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        #构建需要写入的内容
        config = configparser.ConfigParser()
        config.read('resource/rule_config.ini',encoding='utf-8')
        if not config.has_section(str(rule_id)):
            config.add_section(str(rule_id))
        config.set(str(rule_id), 'user_id', str(user_id))
        config.set(str(rule_id), 'rule_name', rule_name)
        config.set(str(rule_id), 'rule_id', str(rule_id))
        config.set(str(rule_id), 'src', src)
        config.set(str(rule_id), 'tgt', tgt)
        config.set(str(rule_id), 'unique_number', str(unique_number))
        config.set(str(rule_id), 'error_handler', str(error_handler))
        # 将更改写回配置文件
        with open('resource/rule_config.ini', 'w') as configfile:
            config.write(configfile)
        json_data={'status': 'success', 'message': 'Rule added successfully'}
        # GET 请求返回表单页面
        return redirect('/rule')
    return render(request, 'create_rules.html')
def del_rule(request,rule_id):
    conn = sqlite3.connect('identifier.sqlite')  # 连接到数据库
    cursor = conn.cursor()
    sql=f'''delete from main.rule_cmp where rule_id="{rule_id}"'''
    print(sql)
    config = configparser.ConfigParser()
    config.read('resource/rule_config.ini', encoding='utf-8')
    cursor.execute(sql)
    if config.has_section(rule_id):
        # 删除指定的 section
        config.remove_section(rule_id)
        # 将修改后的配置写回文件
        with open(config_file, 'w', encoding='utf-8') as file:
            config.write(file)
    return JsonResponse({'status': 'success', 'message': '成功删除规则!'}, status=200)
def del_config(request,dbname):
    print(dbname)
    config = configparser.ConfigParser()
    config.read('resource/DB.ini', encoding='utf-8')
    if config.has_section(dbname):
        config.remove_section(dbname)
        with open('resource/DB.ini','w',encoding='utf-8') as file:
            config.write(file)
    return  JsonResponse({'status': 'success', 'message': '成功删除!'}, status=200)
def udp_config(request,dbname):
    if request.method == 'POST':
        data= json.loads(request.body)
        update_value=data['updatedValues']
        config = configparser.ConfigParser()
        config.read('resource/DB.ini',encoding='utf-8')
        for key,value in update_value.items():
            config.set(data['section'], key, value)
            print(key+'\t'+value)
        with open('resource/DB.ini','w',encoding='utf-8') as file:
            config.write(file)
        return JsonResponse({'status': 'success', 'message': 'Config updated successfully!'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)
def add_config(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        print(type(data),data)
        section=data['section']
        config = configparser.ConfigParser()
        config.read('resource/DB.ini', encoding='utf-8')
        if not config.has_section(data['section']):
            config.add_section(data['section'])
            del data['section']
            for item in data['extraKeys']:
                dic={item['key']:item['value']}
                data={**data,**dic}
            del data['extraKeys']
            for key,value in data.items():
                config.set(section,key,value)
            with open('resource/DB.ini','w',encoding='utf-8') as f:
                config.write(f)
            return JsonResponse({'status': 'success', 'message': 'Config updated successfully!'})
        else:
            JsonResponse({'status': 'error', 'message': 'section名称已存在，添加失败'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)
#修改规则
def ch_rule():
    pass
def shut_rule(request,rule_id):
    if request.method == 'POST':

        if rule_id in list(exec_task.keys()):
            exec_task[rule_id]['stop_event'].set()
            exec_task[rule_id]['future'].join()
            return JsonResponse({"ok":'ok',"message": '未运行'}, status=200)
        else:
            return JsonResponse({"error": "11", "message": '未运行'}, status=500)
    else:
        return JsonResponse({"error": "11", "message": '错误访问方法'}, status=500)



def get_rule(request):

    if request.method=='GET':
        set=(ptest.get_rule())
        response = {'rules':set}
        #return JsonResponse(response)
        return render(request,'rule_home.html',response)
#纯json输出规则界面
def jsonrule(request):
    if request.method=='GET':
        set=(ptest.get_rule())
        response = {'rules':set}
        return JsonResponse(response)
def detail(request,rule_id):
    conn1 = sqlite3.connect('identifier.sqlite')
    cursor=conn1.cursor()
    set=[]
    dict={}
    report=[]
    for item in  ptest.get_rule().items():
        set.append((item[0],item[1]['rule_name']))
        cursor.execute(f"select tbname from main.report_map where uid='{item[0]}' order by inc desc")
        result=cursor.fetchall()
        if result !=0:
            fet=[x[0] for x in result]
        else:fet=[]
        dict[f'{item[0]}']=fet
    print(json.dumps({'rules': set,'files': dict,'rule_id': rule_id}))
    return render(request, 'detail.html', {"rules": json.dumps(set),"files": json.dumps(dict),"rule_id": rule_id})
def serve_excel(request):
    file_path = os.path.join(MEDIA_PATH)  # 直接写死路径
    if os.path.exists(file_path):
        return FileResponse(open(file_path, "rb"), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        return HttpResponse("File not found", status=404)
def download_ffile(request):
    if request.method == 'POST':
        data= json.loads(request.body)
        print(type(data),data)
    try:
        sheets_to_keep = data  # 需要的工作表列表
        # 读取 Excel 并筛选工作表
        with pandas.ExcelFile(MEDIA_PATH) as xls:
            writer = pandas.ExcelWriter(OUTPUT_PATH, engine="xlsxwriter")
            for sheet in sheets_to_keep:
                if sheet in xls.sheet_names:
                    df = xls.parse(sheet)
                    df.to_excel(writer, sheet_name=sheet, index=False)
            writer.close()

        # 返回合并后的文件
        response = FileResponse(open(OUTPUT_PATH, "rb"))
        response["Content-Disposition"] = 'attachment; filename="filtered_output.xlsx"'
        return response

    except Exception as e:
        return HttpResponse(f"处理错误: {str(e)}", status=500)
def download_file(request):
    response = FileResponse(open(MEDIA_PATH, "rb"))
    response["Content-Disposition"] = 'attachment; filename="filtered_output.xlsx"'
    return response

class QueueMaintainer:
    def __init__(self,uuid,pid,usrid):
        self.que_dic={}
        self.pid=pid
        self.uuid=uuid
        self.user=usrid
        self.queue=queue.Queue()
        self.lock = threading.Lock()
        self.running=True
        self.que_dic[f'{pid}']={'uuid':f'{uuid}','queue':self.queue}
        #初始化时就调用异步线程读队列
        self.consumer_thread = threading.Thread(target=self.consume_queue)
        self.consumer_thread.start()
    def write(self,message):
        #with self.lock:#写队列时加锁
        if message.strip():
            #self.que_dic[f'{self.pid}']['queue'].put((self.pid,message))
            self.queue.put((self.pid, message))
    def get_que(self,pid):
        return self.que_dic[f'{self.pid}']
    def consume_queue(self):
        while self.running:
            try:
                with self.lock:
                    if not self.queue.empty():
                        process_id, message = self.queue.get(timeout=1)
                        self.process_message(process_id, message)
                        self.queue.task_done()  # 确保消费完成
                #self.queue.task_done()
            except Exception as e:
                #self.queue.task_done()
                continue

        print(f'进程{self.pid}停止读取队列，已清空队列')
    def stop(self):
        self.running=False
        self.que_dic[f'{self.pid}'] = {'uuid': f'{uuid}', 'queue': queue.Queue()}
        self.consumer_thread.join()
    def flush_q(self):
        self.que_dic[f'{self.pid}'] = {'uuid': f'{uuid}', 'queue': queue.Queue()}
        pass
    def flush(self):
        pass
    def process_message(self, process_id, message):
        """处理队列中的消息，可能是打印到控制台或Web页面"""
        #sys.stdout = sys.__stdout__
        #print(f"[进程{process_id}] {message}")
        channels_layer=get_channel_layer()
        group_name = 'messages_group'
        async_to_sync(channels_layer.group_send)(
            group_name,  # 用户对应的 WebSocket 组
            {
                'type': 'send_message',  # 消息类型
                'rule_id': self.uuid,  # 进程 uuID
                'message': message  # 消息内容
            }
        )


