#关于实现B站视频爬取功能实现利用到的库
import requests
import re
import json
import os
import time
from tqdm import tqdm

#关于功能GUI可视化用到的库
from tkinter import *
from tkinter.filedialog import *
from tkinter import messagebox
import webbrowser   #用于打开网页
from tkinter import ttk    #用于展示进度条
import random

user_agent_list = [
            "Mozilla/5.0 (Linux; U; Android 2.3.6; en-us; Nexus S Build/GRK39F) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
            "Avant Browser/1.2.789rel1 (http://www.avantbrowser.com)",
            "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.5 (KHTML, like Gecko) Chrome/4.0.249.0 Safari/532.5",
            "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/532.9 (KHTML, like Gecko) Chrome/5.0.310.0 Safari/532.9",
            "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.7 (KHTML, like Gecko) Chrome/7.0.514.0 Safari/534.7",
            "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/534.14 (KHTML, like Gecko) Chrome/9.0.601.0 Safari/534.14",
            "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.14 (KHTML, like Gecko) Chrome/10.0.601.0 Safari/534.14",
            "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.20 (KHTML, like Gecko) Chrome/11.0.672.2 Safari/534.20",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.27 (KHTML, like Gecko) Chrome/12.0.712.0 Safari/534.27",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.24 Safari/535.1",
            "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/535.2 (KHTML, like Gecko) Chrome/15.0.874.120 Safari/535.2",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.36 Safari/535.7",
            "Mozilla/5.0 (Windows; U; Windows NT 6.0 x64; en-US; rv:1.9pre) Gecko/2008072421 Minefield/3.0.2pre",
            "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.10) Gecko/2009042316 Firefox/3.0.10",
            "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.0.11) Gecko/2009060215 Firefox/3.0.11 (.NET CLR 3.5.30729)",
            "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 GTB5",
            "Mozilla/5.0 (Windows; U; Windows NT 5.1; tr; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 ( .NET CLR 3.5.30729; .NET4.0E)",
            "Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1",
            "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0.1) Gecko/20100101 Firefox/4.0.1",
            "Mozilla/5.0 (Windows NT 5.1; rv:5.0) Gecko/20100101 Firefox/5.0",
            "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0a2) Gecko/20110622 Firefox/6.0a2",
            "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:7.0.1) Gecko/20100101 Firefox/7.0.1",
            "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:2.0b4pre) Gecko/20100815 Minefield/4.0b4pre",
            "Mozilla/4.0 (compatible; MSIE 5.5; Windows NT 5.0 )",
            "Mozilla/4.0 (compatible; MSIE 5.5; Windows 98; Win 9x 4.90)",
            "Mozilla/5.0 (Windows; U; Windows XP) Gecko MultiZilla/1.6.1.0a",
            "Mozilla/2.02E (Win95; U)",
            "Mozilla/3.01Gold (Win95; I)",
            "Mozilla/4.8 [en] (Windows NT 5.1; U)",
            "Mozilla/5.0 (Windows; U; Win98; en-US; rv:1.4) Gecko Netscape/7.1 (ax)",
            "HTC_Dream Mozilla/5.0 (Linux; U; Android 1.5; en-ca; Build/CUPCAKE) AppleWebKit/528.5  (KHTML, like Gecko) Version/3.1.2 Mobile Safari/525.20.1",
            "Mozilla/5.0 (hp-tablet; Linux; hpwOS/3.0.2; U; de-DE) AppleWebKit/534.6 (KHTML, like Gecko) wOSBrowser/234.40.1 Safari/534.6 TouchPad/1.0",
            "Mozilla/5.0 (Linux; U; Android 1.5; en-us; sdk Build/CUPCAKE) AppleWebkit/528.5  (KHTML, like Gecko) Version/3.1.2 Mobile Safari/525.20.1",
            "Mozilla/5.0 (Linux; U; Android 2.1; en-us; Nexus One Build/ERD62) AppleWebKit/530.17 (KHTML, like Gecko) Version/4.0 Mobile Safari/530.17",
            "Mozilla/5.0 (Linux; U; Android 2.2; en-us; Nexus One Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
            "Mozilla/5.0 (Linux; U; Android 1.5; en-us; htc_bahamas Build/CRB17) AppleWebKit/528.5  (KHTML, like Gecko) Version/3.1.2 Mobile Safari/525.20.1",
            "Mozilla/5.0 (Linux; U; Android 2.1-update1; de-de; HTC Desire 1.19.161.5 Build/ERE27) AppleWebKit/530.17 (KHTML, like Gecko) Version/4.0 Mobile Safari/530.17",
            "Mozilla/5.0 (Linux; U; Android 2.2; en-us; Sprint APA9292KT Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
            "Mozilla/5.0 (Linux; U; Android 1.5; de-ch; HTC Hero Build/CUPCAKE) AppleWebKit/528.5  (KHTML, like Gecko) Version/3.1.2 Mobile Safari/525.20.1",
            "Mozilla/5.0 (Linux; U; Android 2.2; en-us; ADR6300 Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
            "Mozilla/5.0 (Linux; U; Android 2.1; en-us; HTC Legend Build/cupcake) AppleWebKit/530.17 (KHTML, like Gecko) Version/4.0 Mobile Safari/530.17",
            "Mozilla/5.0 (Linux; U; Android 1.5; de-de; HTC Magic Build/PLAT-RC33) AppleWebKit/528.5  (KHTML, like Gecko) Version/3.1.2 Mobile Safari/525.20.1 FirePHP/0.3",
            "Mozilla/5.0 (Linux; U; Android 1.6; en-us; HTC_TATTOO_A3288 Build/DRC79) AppleWebKit/528.5  (KHTML, like Gecko) Version/3.1.2 Mobile Safari/525.20.1",
            "Mozilla/5.0 (Linux; U; Android 1.0; en-us; dream) AppleWebKit/525.10  (KHTML, like Gecko) Version/3.0.4 Mobile Safari/523.12.2",
            "Mozilla/5.0 (Linux; U; Android 1.5; en-us; T-Mobile G1 Build/CRB43) AppleWebKit/528.5  (KHTML, like Gecko) Version/3.1.2 Mobile Safari 525.20.1",
            "Mozilla/5.0 (Linux; U; Android 1.5; en-gb; T-Mobile_G2_Touch Build/CUPCAKE) AppleWebKit/528.5  (KHTML, like Gecko) Version/3.1.2 Mobile Safari/525.20.1",
            "Mozilla/5.0 (Linux; U; Android 2.0; en-us; Droid Build/ESD20) AppleWebKit/530.17 (KHTML, like Gecko) Version/4.0 Mobile Safari/530.17",
            "Mozilla/5.0 (Linux; U; Android 2.2; en-us; Droid Build/FRG22D) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
            "Mozilla/5.0 (Linux; U; Android 2.0; en-us; Milestone Build/ SHOLS_U2_01.03.1) AppleWebKit/530.17 (KHTML, like Gecko) Version/4.0 Mobile Safari/530.17",
            "Mozilla/5.0 (Linux; U; Android 2.0.1; de-de; Milestone Build/SHOLS_U2_01.14.0) AppleWebKit/530.17 (KHTML, like Gecko) Version/4.0 Mobile Safari/530.17",
            "Mozilla/5.0 (Linux; U; Android 3.0; en-us; Xoom Build/HRI39) AppleWebKit/525.10  (KHTML, like Gecko) Version/3.0.4 Mobile Safari/523.12.2",
            "Mozilla/5.0 (Linux; U; Android 0.5; en-us) AppleWebKit/522  (KHTML, like Gecko) Safari/419.3",
            "Mozilla/5.0 (Linux; U; Android 1.1; en-gb; dream) AppleWebKit/525.10  (KHTML, like Gecko) Version/3.0.4 Mobile Safari/523.12.2",
            "Mozilla/5.0 (Linux; U; Android 2.0; en-us; Droid Build/ESD20) AppleWebKit/530.17 (KHTML, like Gecko) Version/4.0 Mobile Safari/530.17",
            "Mozilla/5.0 (Linux; U; Android 2.1; en-us; Nexus One Build/ERD62) AppleWebKit/530.17 (KHTML, like Gecko) Version/4.0 Mobile Safari/530.17",
            "Mozilla/5.0 (Linux; U; Android 2.2; en-us; Sprint APA9292KT Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
            "Mozilla/5.0 (Linux; U; Android 2.2; en-us; ADR6300 Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
            "Mozilla/5.0 (Linux; U; Android 2.2; en-ca; GT-P1000M Build/FROYO) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
            "Mozilla/5.0 (Linux; U; Android 3.0.1; fr-fr; A500 Build/HRI66) AppleWebKit/534.13 (KHTML, like Gecko) Version/4.0 Safari/534.13",
            "Mozilla/5.0 (Linux; U; Android 3.0; en-us; Xoom Build/HRI39) AppleWebKit/525.10  (KHTML, like Gecko) Version/3.0.4 Mobile Safari/523.12.2",
            "Mozilla/5.0 (Linux; U; Android 1.6; es-es; SonyEricssonX10i Build/R1FA016) AppleWebKit/528.5  (KHTML, like Gecko) Version/3.1.2 Mobile Safari/525.20.1",
            "Mozilla/5.0 (Linux; U; Android 1.6; en-us; SonyEricssonX10i Build/R1AA056) AppleWebKit/528.5  (KHTML, like Gecko) Version/3.1.2 Mobile Safari/525.20.1",
        ]

class Application(Frame):
    def __init__(self,master = None):
        super().__init__(master)
        self.master = master
        self.bgcolor = 'white'
        self.fgcolor = 'black'
        self.pack()
        self.createWidget()

    def createWidget(self):
        #创建相应标签
        self.label01 =Label(self,text = '文件ffmpeg的路径:',width=20,height=2,bg = self.bgcolor,fg = self.fgcolor,font = ('宋体',10))
        self.label02 =Label(self,text = '视频保存路径:',width=20,height=2,bg = self.bgcolor,fg = self.fgcolor,font = ('宋体',10))
        self.label03 =Label(self,text = '视频网址:',width=20,height=2,bg = self.bgcolor,fg = self.fgcolor,font = ('宋体',10))
        self.label04 =Label(self,text = '视频昵称(可自动获取):',width=20,height=2,bg = self.bgcolor,fg = self.fgcolor,font = ('宋体',10))
        self.label05 = Label(self,text = "cookie(可以为空):",width=20,height=2,bg = self.bgcolor,fg = self.fgcolor,font = ('宋体',10))

        self.label01.grid(row = 0,column=0,sticky= W)
        self.label02.grid(row = 1,column=0,sticky= W)
        self.label03.grid(row = 2,column=0,sticky= W)
        self.label04.grid(row = 3,column=0,sticky= W)
        self.label05.grid(row=4, column=0, sticky=W)

        #创建相应功能按钮
        self.btn01 = Button(self,text = '选择路径',command = self.find_file01)
        self.btn02 = Button(self,text = '选择路径',command = self.find_file02)
        self.btn03 = Button(self,text = '打开bilibili网站',command = self.open_web)
        self.btn04 = Button(self,text = '点击自动获取',command=lambda: self.find_names(str(self.video_http.get())))
        self.btn05 = Button(self,text = '开始下载',command = self.download)
        self.progressone = ttk.Progressbar(self,name = '进度条',value = 0,mode='determinate', orient=HORIZONTAL)

        self.btn01.grid(row = 0,column = 7,sticky=NSEW)
        self.btn02.grid(row = 1,column = 7,sticky=NSEW)
        self.btn03.grid(row = 2,column = 7,sticky=NSEW)
        self.btn04.grid(row = 3,column = 7,sticky=NSEW)
        self.btn05.grid(row = 5,column = 2,columnspan=3,sticky= NSEW)
        self.progressone.grid(row = 6 ,column = 0,columnspan=8,sticky= NSEW )


        #创建单行文本框
        #1.创建变量并建立但文本行
        self.ffmpeg_lujing = StringVar()
        self.ffmpeg_lujing.set('请点击按钮选择ffmpeg.exe路径')
        self.entry01 = Entry(self,textvariable=self.ffmpeg_lujing,width=40,exportselection=0,font = ('宋体',10))

        self.keep_lujing = StringVar()
        self.keep_lujing.set('请输入视频将保存的路径:')
        self.entry02 = Entry(self,textvariable = self.keep_lujing,width=40,exportselection=0,font = ('宋体',10))

        self.video_http = StringVar()
        self.video_http.set('请输入视频地址,点击按钮打开B站')
        self.entry03 = Entry(self,textvariable = self.video_http,width=40,exportselection=0,font = ('宋体',10))

        self.video_names = StringVar()
        self.video_names.set('可手动输入,也可以点击自动获取')
        self.entry04 = Entry(self,textvariable= self.video_names,width=40,exportselection=0,font = ('宋体',10))

        self.cookie = StringVar()
        self.cookie.set('1')
        self.entry05 = Entry(self, textvariable=self.cookie, width=40, exportselection=0, font=('宋体', 10))

        self.entry01.grid(row=0,column=1,columnspan=6)
        self.entry02.grid(row=1,column=1,columnspan=6)
        self.entry03.grid(row=2,column=1,columnspan=6)
        self.entry04.grid(row=3,column=1,columnspan=6)
        self.entry05.grid(row=4,column=1,columnspan=6)

    def find_file01(self):   #实现选择ffmpeg.exe路径
        filename = askopenfilename(filetypes = [('应用程序','.exe')])
        self.ffmpeg_lujing.set(str(filename))
        print('选择的ffmpeg的路径是: ',filename)
        messagebox.askquestion('ffmpeg.exe路径','您选择的ffmpeg路径是: '+str(filename))

    def find_file02(self):   #实现选择保存路径
        filename = askdirectory()
        self.keep_lujing.set(str(filename))
        print('选择的保存路径是: ',filename)
        messagebox.askquestion('保存路径','您选择的保存路径是: '+str(filename))

    def open_web(self):     #实现打开bilibili网页
        webbrowser.open('https://www.bilibili.com/')

    def find_names(self,url):   #实现自动获取视频名称
        print('获取视频昵称:'+str(url))
        if url == '请输入视频地址,点击按钮打开B站' or url == '':
            messagebox.showwarning('视频地址','您还未输入视频地址')
        else :
            name = 'none'
            headers = {
                "User-Agent": random.choice(user_agent_list),
            }
            resp = requests.get(url,headers=headers)
            page_content = resp.text
            obj = re.compile(r'<title data-vue-meta="true">(?P<title>.*?)</title>', re.S)
            result = obj.finditer(page_content)
            for it in result:
                name = it.group('title')
            if name == 'none':
                messagebox.showwarning('获取视频昵称','获取失败,请手动输入')
            else:
                self.video_names.set(name)


    def download(self):
        if self.ffmpeg_lujing.get() == '请点击按钮选择ffmpeg.exe路径' or self.ffmpeg_lujing.get() == '':
            messagebox.showwarning('ffmpeg路径','您还未选择ffmpeg保存路径(PS:本程序需要下载ffmpeg)')
            return

        if self.keep_lujing.get() == '请输入视频将保存的路径:' or self.keep_lujing.get() == '':
            messagebox.showwarning('保存路径','您还未选择视频需要保存的目录')
            return

        if self.video_http.get() == '请输入视频地址,点击按钮打开B站' or self.video_http.get() == '':
            messagebox.showwarning('视频地址','您还输入B站视频地址')
            return

        if self.video_names.get() == '可手动输入,也可以点击自动获取' or self.video_names.get() == '':
            messagebox.showwarning('视频地址','您还输入B站视频地址')
            return

        messagebox.showinfo('提示','此窗口可能会卡死,请勿关闭窗口,可在后台观察进度')

        self.progressbar_start()

        url = str(self.video_http.get())
        # 使用re.sub方法进行匹配和替换
        page_count = 1
        new_url = re.sub(r"\?.*", "?p=1", url)
        retry_count = 0
        while True:
            new_url = re.sub(r"p=\d+", f"p={page_count}", new_url)
            _headers = {
                'User-Agent': random.choice(user_agent_list),
                "Cookie":str(self.cookie.get()),
            }
            print("url:", new_url)

            resp = requests.get(new_url, headers=_headers)
            if resp.status_code != 200:
                print(resp.status_code)
                retry_count += 1
                if retry_count > 10:
                    print(f"当前第{page_count}个视频下载失败,结束任务")
                    break
                continue

            page_content = resp.text
            # print(page_content)

            obj = re.compile(r'<script>window.__playinfo__=(?P<data>.*?)</script>', re.S)

            try:
                result = obj.finditer(page_content)

                for it in result:
                    Data = it.group('data')
                    # print(Data)
                data_json = json.loads(Data)
                videosrcurl = data_json['data']['dash']['video'][0]['baseUrl']
                audiosrcurl = data_json['data']['dash']['audio'][0]['baseUrl']
                print('videosrcurl: '+str(videosrcurl))
                print('audiosrcurl: '+str(audiosrcurl))

                _headers = {
                    'User-Agent': random.choice(user_agent_list),
                    'Referer': url
                }
                print('开始下载视频以及音频,请耐心等待')
                video = requests.get(videosrcurl, headers=_headers, stream=True)
                print('开始写入视频')
                with open(self.keep_lujing.get() + '/video.mp4', mode='wb') as f:
                    for data in tqdm(video.iter_content(chunk_size=1024)):
                        f.write(data)
                print('视频写入完成')
                # print('休息5s')
                # time.sleep(5)
                audio = requests.get(audiosrcurl, headers=_headers, stream=True)
                print('开始写入音频')
                with open(self.keep_lujing.get() + '/audio.mp3', mode='wb') as f:
                    for data in tqdm(audio.iter_content(chunk_size=1024)):
                        f.write(data)
                print('音频写入完成')

                self.find_names(new_url)
                name = str(self.video_names.get())

                print('开始合成最终视频')
                # with open(self.keep_lujing.get() + f'/{name}.mp4', mode='wb') as f:
                # 因为下文os.system写了合并后的文件,就不用提前创建了,提前创建的话,后面就需要在后台确认是否覆盖,不方便用户
                Ffmpeg = self.ffmpeg_lujing.get().replace('.exe','')
                os.system(
                    f'{Ffmpeg} -i {self.keep_lujing.get()}/video.mp4 -i {self.keep_lujing.get()}/audio.mp3 -acodec copy -vcodec copy {self.keep_lujing.get()}/{name}_{page_count}.mp4')
                print('合成成功！')
                video.close()
                audio.close()

                os.remove(self.keep_lujing.get() + '/video.mp4')
                os.remove(self.keep_lujing.get() + '/audio.mp3')
                print('视频下载完成，请到文件夹中查询')
                retry_count = 0

                page_count += 1

                time.sleep(random.random()*5)

            except:
                print("获取Data列表失败，开始重试")
                retry_count +=1
                if retry_count > 10:
                    print(f"当前第{page_count}个视频下载失败,结束任务")
                    break
                continue

        messagebox.showinfo('下载成功','视频下载完成，请到文件夹中查询')

        self.progressbar_stop()

    def progressbar_start(self):
        self.progressone.start()

    def progressbar_stop(self):
        self.progressone.stop()


root = Tk()
root.geometry('600x225+500+200')
root.title('B站视频下载')

app = Application(master=root)

root.mainloop()

