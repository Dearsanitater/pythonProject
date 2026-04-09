#此模块为比对源库与英方i2stream——queue队列表的功能，改队列后续没有上线，暂时搁置
import os
import re
import sys
import json
import shutil
import compare
import subprocess
active_home=r'C:\Program Files (x86)\i2active-node\etc'
queue = r'D:\Info\iastream-queue-7.1.74.23122113\stream-queue\iastream-queue\bin'
log_dir=r'D:\Info\log'
#SEQ# = 518 / FRAG# = 0 (last frag)
# coding=utf-8
compare_file=r'D:\Info\log\log1.txt'#自动化生成该文件\偏移量问题

class ana_log():
    def __init__(self):
        self.addr=''
        self.tml=[]
        self.templine=''
        self.tbname=''
        self.tmp_list=[]
        self.clock=0
        self.focus={}
        self.offset=None
    def mssrule(self):#解析mssrule
        tmp=[]
        dict={}
        shutil.copy(active_home+'\mssrule.conf',log_dir)
        with open(log_dir+'\mssrule.conf',mode='rb+') as p:
            p.seek(-2,os.SEEK_END)
            a=p.read()
            print(a,type(a))
            p.seek(-1, os.SEEK_END)
            if b'\x00' in p.read():
                p.seek(-1, os.SEEK_END)
                p.write(b' ')
                p.flush()
            else:
                p.close()
        with open(log_dir+'\mssrule.conf',mode='r',encoding='utf-8') as j:
            rule=json.load(j)
        for i in rule:
            dict['name']=i['name']
            dict['uuid'] = i['uuid']
            tmp.append(dict)
            dict={}
        return tmp
    def get_file(self):#REPCTL
        mssrule=self.mssrule()
        reprule=[]
        tmp= {}
        tml= []
        rep = subprocess.Popen(r'.\repctl.bat services', stdout=subprocess.PIPE,cwd=queue,shell=True, text=True)
        rep_rule = rep.communicate()[0]
        r=rep_rule.splitlines()
        # 解析repctl 输出规则
        for a in r:
            if a.startswith('appliedLastSeqno'):
                tmp['lines']=re.findall(r':\s(.*)',a)##re.findall(r'\d+',tmp['lines'][0])
            elif a.startswith('serviceName'):
                tmp['uuid']=re.findall(r':\s(.*)',a)
            elif ('----') in a and tmp:
                reprule.append(tmp)
                tmp={}
            elif ('Finished') in a:
                if not tmp:
                    break
                elif tmp:
                    reprule.append(tmp)
                    tmp = {}
                    break
        # mss与repctl规则对比，生成有效规则字典列表
        for i in mssrule:
            for j in reprule:
                if re.sub('[^a-zA-Z0-9]','',i['uuid'])==re.sub('[^a-zA-Z0-9]','',j['uuid'][0]):
                    tmp['name']=i['name']
                    tmp['uuid']=j['uuid'][0]
                    tmp['rows']=j['lines'][0]
                    tml.append(tmp)
                    tmp = {}
        print(f'已找到repctl对应界面mss规则{len(tml)}条,output\n {tml}')
        #按有效规则列表生成对应文件夹路径，以便保存解析json
        for i in tml:
            try:
                cd = log_dir + '\\' + i['uuid']
                i['dir']=cd
                if os.path.exists(cd):
                    print(f"dir has been exists {cd}")
                    continue
                else:
                    os.mkdir(cd)
                    print(f"create dir successfully where {cd}")
            except OSError as e:
                print(f'error creating dir {e}')
        #print(tml)
        self.tml=tml
    # 挑选规则获取为focus
    def select(self):
        focus={}
        while not focus:
            for l in self.tml:
                print(l)
            a=input('witch fking rule u wana select?')
            while True:
                k = 0
                for i in self.tml:
                    if i['uuid'].lower().startswith(a) or i['name'].startswith(a):
                        k+=1
                        print(i)
                if k==1:
                    if input(f'press enter ensure the rule{i}')=='':
                        focus=i
                        print('The rule u choose is ',focus)
                        break
                    else:
                        if input('a回b退') ==a:continue
                        else :break
                elif k!=1:
                    a=input('精准一些，具体哪条')
                    continue
                elif k==0:
                    input('查无规则，重新输入')
        self.focus=focus
        i= input(f"default offset value is \033[0;32m {self.focus['rows']} \033[0m,input number to set the value or enter to pass")
        if i=='':
            pass
        else:self.focus['rows']=i
        ps=[rf"powershell",rf"cd {queue} ;.\tf.bat -service {self.focus['uuid']} list -from {self.focus['rows']}"]
        file=rf"{queue}+\tf.bat"
        args=['-service',rf"{self.focus['uuid']} list","-from",rf"{self.focus['rows']}"]
        t1=['powershell',rf"cd {queue};.\t1.bat"]
        print(ps)

        #tf = subprocess.Popen(['powershell','-File',file]+args,stdout=subprocess.PIPE,text=True,shell=True)
        tf = subprocess.Popen( ps, stdout=subprocess.PIPE, text=True,errors='ignore')##
        text=tf.communicate()[0]
        with open(self.focus['dir']+r'\a.txt','w+',encoding='gbk') as f:
            f.write(text)
        print('tf存log下%s'%(self.focus['dir']+r'\a.txt'))
        #print(tf.communicate()[0])
    def read(self,num,src_tab):
        addr=self.focus['dir']+r'\a.txt'
        with open(addr,mode='r',encoding='gbk') as f:
            while True:
                self.templine = f.readline()
                if self.templine.startswith('- SQL(0)'):
                    self.templine=re.search(r'- SQL\(0\) = (.+)',self.templine)
                    json_data=json.loads(self.templine.group(1))
                    if json_data['scn'] !="0":
                        self.tmp_list.append(json_data['table'])
                        self.clock+=1
                elif not self.templine:
                    break
        tmp=[]
        err=[]
        for a in src_tab:
            tmp.append(a['tab_name'])
        for b in tmp:
            if b in self.tmp_list:
                continue
            else:
                err.append(b)
        #print(src_tab)
        print('队列中共计表数',self.clock,'\n')
        if num and self.clock and num==self.clock:
            print(f'\033[0;32m YES! \033[0m \t 源库与队列表数相同\t 源端 {num} 备端 {self.clock}')
        else:
            print('\033[0;31m NO! \033[0m \t 源库与队列表数不同\t 源端 %d 备端 %d'%(num, self.clock))
            print(f'缺失表为:\t{len(err)}\n',err)
        return self.tmp_list
class kafka():
    def __init__(self):
        pass




if __name__ == '__main__':
    p=ana_log()
    conn=compare.ergodic_database()
    num,tab_dict=conn.src_tab()
    #tab_dict=conn.src_tab()[1]
    #print(num,tab_dict)

    print('get_file')
    p.get_file()
    p.select()
    print('read')
    p.read(num,tab_dict)
