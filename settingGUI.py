from re import I
import tkinter
from tkinter import ttk
import json
import os
from urllib import request
import requests
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from PIL import Image

class lbl_entry_frame(ttk.Frame):
    def __init__(self, parent, text=None, textvariable=None, validate=None, vfun=None):
        super().__init__(parent)
        lbl = tkinter.Label(self, text=text)
        vcmd = None
        if vfun:
            vcmd = (self.register(vfun), '%P')
        entry = tkinter.Entry(self, textvariable=textvariable, validate=validate, validatecommand=vcmd, invalidcommand=self.invalidcommand)
        lbl.pack()
        entry.pack()
    def invalidcommand(self):
        print('invalid input')

def get_creds(SCOPES):
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

class ScrollableFrame(ttk.Frame):
    def __init__(self, container, bar_x = True, bar_y = True):
        super().__init__(container)
        self.canvas = tkinter.Canvas(self)
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind_all("<MouseWheel>", self.OnMouseWheel)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="n")
        if bar_y:
            self.scrollbar_y = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
            self.scrollbar_y.pack(side=tkinter.RIGHT, fill="y")
            #self.scrollbar_y.grid(row=0, column=1, sticky='nse')
            self.canvas.configure(yscrollcommand=self.scrollbar_y.set)
        if bar_x:
            self.scrollbar_x = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
            self.scrollbar_x.pack(side=tkinter.BOTTOM, fill="x")
            #self.scrollbar_x.grid(row=1, column=0, sticky='swe')
            self.canvas.configure(xscrollcommand=self.scrollbar_x.set)
        self.canvas.pack(side=tkinter.LEFT, fill="both", expand=True)
        #self.canvas.grid(row=0, column=0, sticky='nswe')
    def OnMouseWheel(self, event):
        self.canvas.yview_scroll(int(-event.delta/200),"units")
        return "break"
        
class Setting:
    def __init__(self, parent, creds):
        nb = ttk.Notebook(parent)

        general_tab = tkinter.Frame(nb)
        contents_tab = tkinter.Frame(nb)

        nb.add(general_tab, text='general', sticky='nswe')
        nb.add(contents_tab, text='contents', sticky='nswe')

        self.config = None
        try:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
        except:
            pass
        self.creds = creds
        self.generalsetting = Generalsetting(general_tab, self.config, self.creds)
        self.generalsetting.main_frame.pack(fill='both', expand=True)
        self.calendarsetting = Calendarsetting(contents_tab, self.config, self.creds)
        self.weathersetting = Weathersetting(contents_tab, self.config)
        self.taskssetting = Taskssetting(contents_tab, self.config, self.creds)

        all_contents = ['calendar', 'weather', 'tasks']
        if self.config:
            selected_contents = self.config['general']['contents']
        else:
            selected_contents = []

        unselected_contents = [i for i in all_contents if i not in selected_contents]

        self.frame = tkinter.Frame(parent, bd=4, relief=tkinter.GROOVE)
        self.now_contents = tkinter.Listbox(self.frame, listvariable=tkinter.StringVar(value=selected_contents))
        self.now_contents.bind("<ButtonRelease-1>", self.selected_setting)
        self.now_contents.grid(row=0, column=0, columnspan=2)
        self.button_append = tkinter.Button(self.frame, text='∧', command=self.append_content)
        self.button_append.grid(row=1, column=0)
        self.button_remove = tkinter.Button(self.frame, text='∨', command=self.remove_content)
        self.button_remove.grid(row=1, column=1)
        self.unused_contents = tkinter.Listbox(self.frame, listvariable=tkinter.StringVar(value=unselected_contents))
        self.unused_contents.bind("<ButtonRelease-1>", self.selected_setting)
        self.unused_contents.grid(row=2, column=0, columnspan=2)

        self.initial = Initialmessage(contents_tab)
        self.showing = self.initial
        self.showing.main_frame.pack(fill='both', expand=True)

        self.frame.grid(row=0, column=0, sticky='nswe')
        nb.grid(row=0, column=1, sticky='nswe')

    def append_content(self):
        selected_index = self.unused_contents.curselection()
        selected_content = self.unused_contents.get(selected_index)
        self.unused_contents.delete(selected_index)
        self.now_contents.insert(tkinter.END, selected_content)

    def remove_content(self):
        selected_index = self.now_contents.curselection()
        selected_content = self.now_contents.get(selected_index)
        self.now_contents.delete(selected_index)
        self.unused_contents.insert(tkinter.END, selected_content)
    
    def selected_setting(self, event):
        if not self.now_contents.curselection():
            content_index = self.unused_contents.curselection()
            content = self.unused_contents.get(content_index)
        else:
            content_index = self.now_contents.curselection()
            content = self.now_contents.get(content_index)
        if content == 'calendar':
            try:
                if type(self.showing) is not Calendarsetting:
                    self.showing.main_frame.pack_forget()
            except:
                pass
            self.showing = self.calendarsetting
            self.showing.main_frame.pack(fill='both', expand=True)
        elif content == 'weather':
            try:
                if type(self.showing) is not Weathersetting:
                    self.showing.main_frame.pack_forget()
            except:
                pass
            self.showing = self.weathersetting
            self.showing.main_frame.pack(fill='both', expand=True)
        elif content =='tasks':
            try:
                if type(self.showing) is not Taskssetting:
                    self.showing.main_frame.pack_forget()
            except:
                pass
            self.showing = self.taskssetting
            self.showing.main_frame.pack(fill='both', expand=True)
        else:
            pass

    def summarize(self):
        g = self.generalsetting.save()
        g['contents'] = self.now_contents.get(0, last=tkinter.END)
        config = {"general": g, "calendar": self.calendarsetting.save(), "weather": self.weathersetting.save()}
        return config

    def preview(self):
        global imgtk
        global img
        url = 'https://e-indicator-api.herokuapp.com/preview'
        with open('token.json', 'r') as f:
            access_token = json.load(f)
        data = {'access_token': access_token, 'config': self.summarize()}
        response = requests.post(url, data=json.dumps(data), stream=True)
        with open('preview.bmp', 'wb') as f:
            f.write(response.content)

        img = Image.open('preview.bmp')
        img.show()

    def save(self):
        with open('config.json', 'w') as f:
            f.write(json.dumps(self.summarize()))
        print('config saved as config.json')

class Initialmessage:
    def __init__(self, parent):
        self.main_frame = tkinter.Frame(parent)
        self.initial_message = tkinter.Label(self.main_frame, text='select content')
        self.initial_message.pack()

class Calendarsetting:
    def __init__(self, parent, config, creds):
        calendar_config = config.get('calendar', None)
        if calendar_config:
            self.active_carendarIds = calendar_config.get('calendarIds', [])
            self.x = tkinter.StringVar(value=calendar_config.get('x', None))
            self.y = tkinter.StringVar(value=calendar_config.get('y', None))
            self.width = tkinter.StringVar(value=calendar_config.get('width', None))
            self.height = tkinter.StringVar(value=calendar_config.get('height', None))
            self.font = tkinter.StringVar(value=calendar_config.get('font', None))
            self.fontsize = tkinter.StringVar(value=calendar_config.get('fontsize', None))
            self.fontcolor = tkinter.StringVar(value=calendar_config.get('fontcolor', None))
            self.alpha = tkinter.StringVar(value=calendar_config.get('alpha', None))
            self.event_num = tkinter.StringVar(value=calendar_config.get('event_num', None))
        else:
            self.active_carendarIds = []
            self.x = tkinter.StringVar()
            self.y = tkinter.StringVar()
            self.width = tkinter.StringVar()
            self.height = tkinter.StringVar()
            self.font = tkinter.StringVar()
            self.fontsize = tkinter.StringVar()
            self.fontcolor = tkinter.StringVar()
            self.alpha = tkinter.StringVar()
            self.event_num = tkinter.StringVar()

        self.calendar_service = build('calendar', 'v3', credentials=creds)
        self.calendar_list = self.calendar_service.calendarList().list().execute()['items']
        self.calendar_dict = {}
        for i in self.calendar_list:
            self.calendar_dict[i['summary']] = i['id']

        self.main_frame = ScrollableFrame(parent)

        frame1 = tkinter.Frame(self.main_frame.scrollable_frame, bd=2, relief=tkinter.GROOVE)
        lbl1 = tkinter.Label(frame1, text='select calendar')
        lbl1.pack()
        self.calendarId_vars = {}
        for calendar in self.calendar_list:
            if calendar['id'] in self.active_carendarIds:
                self.calendarId_vars[calendar['id']] = tkinter.BooleanVar(value=True)
            else:
                self.calendarId_vars[calendar['id']] = tkinter.BooleanVar(value=False)
            chk = tkinter.Checkbutton(frame1, text=calendar['summary'], variable=self.calendarId_vars[calendar['id']])
            chk.pack(anchor=tkinter.NW)

        frame2= lbl_entry_frame(self.main_frame.scrollable_frame, text='x', validate='key', textvariable=self.x, vfun=lambda e: e.isdecimal() or e == '')
        frame3 = lbl_entry_frame(self.main_frame.scrollable_frame, text='y', validate='key', textvariable=self.y, vfun=lambda e: e.isdecimal() or e == '')
        frame4 = lbl_entry_frame(self.main_frame.scrollable_frame, text='width', validate='key', textvariable=self.width, vfun=lambda e: e.isdecimal() or e == '')
        frame5 = lbl_entry_frame(self.main_frame.scrollable_frame, text='height', validate='key', textvariable=self.height, vfun=lambda e: e.isdecimal() or e == '')
        frame6 = lbl_entry_frame(self.main_frame.scrollable_frame, text='font', textvariable=self.font)
        frame7 = lbl_entry_frame(self.main_frame.scrollable_frame, text='fontsize', validate='key', textvariable=self.fontsize, vfun=lambda e: e.isdecimal() or e == '')
        frame8 = lbl_entry_frame(self.main_frame.scrollable_frame, text='fontcolor', textvariable=self.fontcolor)
        frame9 = lbl_entry_frame(self.main_frame.scrollable_frame, text='alpha', validate='key', textvariable=self.alpha, vfun=lambda e: e.isdecimal() or e == '')
        frame10 = lbl_entry_frame(self.main_frame.scrollable_frame, text='event_num', validate='key', textvariable=self.event_num, vfun=lambda e: e.isdecimal() or e == '')

        frame1.grid(row=0, column=0, columnspan=2)
        frame2.grid(row=1, column=0, padx=5)
        frame3.grid(row=1, column=1, padx=5)
        frame4.grid(row=2, column=0, padx=5)
        frame5.grid(row=2, column=1, padx=5)
        frame6.grid(row=3, column=0, padx=5)
        frame7.grid(row=3, column=1, padx=5)
        frame8.grid(row=4, column=0, padx=5)
        frame9.grid(row=4, column=1, padx=5)
        frame10.grid(row=4, column=0, padx=5)

    def save(self, event=None):
        self.active_carendarIds = []
        for calendarId, var in self.calendarId_vars.items():
            if var.get() == True:
                self.active_carendarIds.append(calendarId)
        return {'calendarIds': self.active_carendarIds,
        'x': self.x.get(),
        'y': self.y.get(),
        'width': self.width.get(),
        'height': self.height.get(),
        'font': self.font.get(),
        'fontsize': self.fontsize.get(),
        'fontcolor': self.fontcolor.get(),
        'alpha': self.alpha.get(),
        'event_num': self.event_num.get()
        }

class Weathersetting:
    def __init__(self, parent, config):
        weather_config = config.get('weather', None)
        if weather_config:
            self.office_name = tkinter.StringVar(value=weather_config.get('office', None))
            self.office_code = weather_config.get('office_code', None)
            self.area_name = tkinter.StringVar(value=weather_config.get('area', None))
            self.area_code = weather_config.get('area_code', None)
            self.x = tkinter.StringVar(value=weather_config.get('x', None))
            self.y = tkinter.StringVar(value=weather_config.get('y', None))
            self.height = tkinter.StringVar(value=weather_config.get('height', None))
            self.width = tkinter.StringVar(value=weather_config.get('width', None))
            self.font = tkinter.StringVar(value=weather_config.get('font', None))
            self.fontsize = tkinter.StringVar(value=weather_config.get('fontsize', None))
            self.fontcolor = tkinter.StringVar(value=weather_config.get('fontcolor', None))
            self.alpha = tkinter.StringVar(value=weather_config.get('alpha', None))
            self.icon_width = tkinter.StringVar(value=weather_config.get('icon_width', None))
            self.icon_height = tkinter.StringVar(value=weather_config.get('icon_height', None))
        else:
            self.office_name = tkinter.StringVar()
            self.office_code = None
            self.area_name = tkinter.StringVar()
            self.area_code = None
            self.x = tkinter.StringVar()
            self.y = tkinter.StringVar()
            self.height = tkinter.StringVar()
            self.width = tkinter.StringVar()
            self.font = tkinter.StringVar()
            self.fontsize = tkinter.StringVar()
            self.fontcolor = tkinter.StringVar()
            self.alpha = tkinter.StringVar()
            self.icon_width = tkinter.StringVar()
            self.icon_height = tkinter.StringVar()

        self.main_frame = ScrollableFrame(parent)
        url = 'https://www.jma.go.jp/bosai/common/const/area.json'
        request.urlretrieve(url, 'area.json')
        with open('area.json', 'r', encoding='UTF-8') as f:
            area_data = json.load(f)    
        self.offices = {}
        for i in area_data['offices']:
            self.offices[area_data['offices'][i]['name']] = i

        frame1 = tkinter.Frame(self.main_frame.scrollable_frame)
        lbl1 = tkinter.Label(frame1, text='select area')
        cmx1 = ttk.Combobox(frame1, textvariable=self.office_name, values=list(self.offices.keys()), state='readonly')
        cmx1.bind("<<ComboboxSelected>>", self.area_select)
        lbl1.pack()
        cmx1.pack()

        frame2 = tkinter.Frame(self.main_frame.scrollable_frame)
        lbl2 = tkinter.Label(frame2, text='detail')
        self.cmx2 = ttk.Combobox(frame2, textvariable=self.area_name)
        if self.office_name.get() == '':
            self.cmx2['state'] = 'disabled'
        else:
            self.cmx2['state'] = 'readonly'
        self.area_select()
        lbl2.pack()
        self.cmx2.pack()

        frame3 = lbl_entry_frame(self.main_frame.scrollable_frame, text='x', textvariable=self.x, validate='key', vfun=lambda e: e.isdecimal() or e == '')
        frame4 = lbl_entry_frame(self.main_frame.scrollable_frame, text='y', textvariable=self.y, validate='key', vfun=lambda e: e.isdecimal() or e == '')
        frame5 = lbl_entry_frame(self.main_frame.scrollable_frame, text='font', textvariable=self.font)
        frame6 = lbl_entry_frame(self.main_frame.scrollable_frame, text='fontsize', textvariable=self.fontsize, validate='key', vfun=lambda e: e.isdecimal() or e == '')
        frame7 = tkinter.Frame(self.main_frame.scrollable_frame)
        lbl7 = tkinter.Label(frame7, text='font color')
        cmx7 = ttk.Combobox(frame7, textvariable=self.fontcolor, values=['white', 'black', 'red', 'blue', 'yellow'])
        lbl7.pack()
        cmx7.pack()
        frame8 = lbl_entry_frame(self.main_frame.scrollable_frame, text='alpha', textvariable=self.alpha, validate='key', vfun=lambda e: e.isdecimal() or e == '')
        frame9 = lbl_entry_frame(self.main_frame.scrollable_frame, text='width', textvariable=self.width, validate='key', vfun=lambda e: e.isdecimal() or e == '')
        frame10 = lbl_entry_frame(self.main_frame.scrollable_frame, text='height', textvariable=self.height, validate='key', vfun=lambda e: e.isdecimal() or e == '')
        frame11 = lbl_entry_frame(self.main_frame.scrollable_frame, text='icon_width', textvariable=self.icon_width, validate='key', vfun=lambda e: e.isdecimal() or e == '')
        frame12 = lbl_entry_frame(self.main_frame.scrollable_frame, text='icon_height', textvariable=self.icon_height, validate='key', vfun=lambda e: e.isdecimal() or e == '')

        frame1.grid(row=0, column=0, padx=5)
        frame2.grid(row=0, column=1, padx=5)
        frame3.grid(row=1, column=0, padx=5)
        frame4.grid(row=1, column=1, padx=5)
        frame5.grid(row=2, column=0, padx=5)
        frame6.grid(row=2, column=1, padx=5)
        frame7.grid(row=3, column=0, padx=5)
        frame8.grid(row=3, column=1, padx=5)
        frame9.grid(row=4, column=0, padx=5)
        frame10.grid(row=4, column=1, padx=5)
        frame11.grid(row=5, column=0, padx=5)
        frame12.grid(row=5, column=1, padx=5)

    def area_select(self, event=None):
        self.office_code = self.offices[self.office_name.get()]
        url = 'https://www.jma.go.jp/bosai/forecast/data/forecast/' + self.office_code + '.json'
        request.urlretrieve(url, 'forecast.json') 
        with open('forecast.json', 'r', encoding="UTF-8") as f:
            forecast_data = json.load(f)    
        self.areas = {}
        for i in forecast_data[0]['timeSeries'][0]['areas']:
            self.areas[i['area']['name']] = i['area']['code']

        self.cmx2['values'] = list(self.areas.keys())

    def save(self, event=None):
        if hasattr(self, 'areas'):
            self.area_code = self.areas[self.area_name.get()]
        return {'office': self.office_name.get(), 
        'office_code': self.office_code, 
        'area': self.area_name.get(), 
        'area_code': self.area_code,
        'x': self.x.get(),
        'y': self.y.get(),
        'width': self.width.get(),
        'height': self.height.get(),
        'font': self.font.get(),
        'fontsize': self.fontsize.get(),
        'fontcolor': self.fontcolor.get(),
        'alpha': self.alpha.get(),
        'icon_width': self.icon_width.get(),
        'icon_height': self.icon_height.get()}

class Taskssetting:
    def __init__(self, parent, config, creds):
        tasks_config = config.get('tasks', None)
        if tasks_config:
            self.active_tasklistIds = tasks_config.get('tasklistIds', [])
            self.x = tkinter.StringVar(value=tasks_config.get('x', None))
            self.y = tkinter.StringVar(value=tasks_config.get('y', None))
            self.width = tkinter.StringVar(value=tasks_config.get('width', None))
            self.height = tkinter.StringVar(value=tasks_config.get('height', None))
            self.font = tkinter.StringVar(value=tasks_config.get('font', None))
            self.fontsize = tkinter.StringVar(value=tasks_config.get('fontsize', None))
            #self.fontcolor = tkinter.StringVar(value=tasks_config.get('fontcolor', None))
            self.alpha = tkinter.StringVar(value=tasks_config.get('alpha', None))
            self.max_tasks = tkinter.StringVar(value=tasks_config.get('max_tasks', None))
        else:
            self.active_tasklistIds = []
            self.x = tkinter.StringVar()
            self.y = tkinter.StringVar()
            self.width = tkinter.StringVar()
            self.height = tkinter.StringVar()
            self.font = tkinter.StringVar()
            self.fontsize = tkinter.StringVar()
            #self.fontcolor = tkinter.StringVar()
            self.alpha = tkinter.StringVar()
            self.max_tasks = tkinter.StringVar()

        self.tasks_service = build('tasks', 'v1', credentials=creds)
        self.tasklists = self.tasks_service.tasklists().list().execute()['items']
        self.tasks_dict = {}
        for i in self.tasklists:
            self.tasks_dict[i['title']] = i['id']

        self.main_frame = ScrollableFrame(parent)

        frame1 = tkinter.Frame(self.main_frame.scrollable_frame, bd=2, relief=tkinter.GROOVE)
        lbl1 = tkinter.Label(frame1, text='select tasklist')
        lbl1.pack()
        self.tasklistId_vars = {}
        for tasklist in self.tasklists:
            if tasklist['id'] in self.active_tasklistIds:
                self.tasklistId_vars[tasklist['id']] = tkinter.BooleanVar(value=True)
            else:
                self.tasklistId_vars[tasklist['id']] = tkinter.BooleanVar(value=False)
            chk = tkinter.Checkbutton(frame1, text=tasklist['title'], variable=self.tasklistId_vars[tasklist['id']])
            chk.pack(anchor=tkinter.NW)

        frame2= lbl_entry_frame(self.main_frame.scrollable_frame, text='x', validate='key', textvariable=self.x, vfun=lambda e: e.isdecimal() or e == '')
        frame3 = lbl_entry_frame(self.main_frame.scrollable_frame, text='y', validate='key', textvariable=self.y, vfun=lambda e: e.isdecimal() or e == '')
        frame4 = lbl_entry_frame(self.main_frame.scrollable_frame, text='width', validate='key', textvariable=self.width, vfun=lambda e: e.isdecimal() or e == '')
        frame5 = lbl_entry_frame(self.main_frame.scrollable_frame, text='height', validate='key', textvariable=self.height, vfun=lambda e: e.isdecimal() or e == '')
        frame6 = lbl_entry_frame(self.main_frame.scrollable_frame, text='font', textvariable=self.font)
        frame7 = lbl_entry_frame(self.main_frame.scrollable_frame, text='fontsize', validate='key', textvariable=self.fontsize, vfun=lambda e: e.isdecimal() or e == '')
        #frame8 = lbl_entry_frame(self.main_frame.scrollable_frame, text='fontcolor', textvariable=self.fontcolor)
        frame9 = lbl_entry_frame(self.main_frame.scrollable_frame, text='alpha', validate='key', textvariable=self.alpha, vfun=lambda e: e.isdecimal() or e == '')
        frame10 = lbl_entry_frame(self.main_frame.scrollable_frame, text='max_tasks', validate='key', textvariable=self.max_tasks, vfun=lambda e: e.isdecimal() or e == '')

        frame1.grid(row=0, column=0, columnspan=2)
        frame2.grid(row=1, column=0, padx=5)
        frame3.grid(row=1, column=1, padx=5)
        frame4.grid(row=2, column=0, padx=5)
        frame5.grid(row=2, column=1, padx=5)
        frame6.grid(row=3, column=0, padx=5)
        frame7.grid(row=3, column=1, padx=5)
        #frame8.grid(row=4, column=0, padx=5)
        frame9.grid(row=4, column=1, padx=5)
        frame10.grid(row=4, column=0, padx=5)

    def save(self, event=None):
        self.active_tasklistIds = []
        for calendarId, var in self.calendarId_vars.items():
            if var.get() == True:
                self.active_tasklistIds.append(calendarId)
        return {'calendarIds': self.active_tasklistIds,
        'x': self.x.get(),
        'y': self.y.get(),
        'width': self.width.get(),
        'height': self.height.get(),
        'font': self.font.get(),
        'fontsize': self.fontsize.get(),
        #'fontcolor': self.fontcolor.get(),
        'alpha': self.alpha.get(),
        'max_tasks': self.max_tasks.get()
        }
class Generalsetting:
    def __init__(self, parent, config, creds):
        self.creds = creds
        if config:
            general_config  = config.get('general', None)
            self.contents = general_config.get('contents', [])
            self.bg_fmt = tkinter.StringVar(value=general_config.get('bg_fmt', None))
            self.bg_color = tkinter.StringVar(value=general_config.get('bg_color', None))
            self.bg_src = tkinter.StringVar(value=general_config.get('bg_src', None))
            self.active_albumIds = general_config.get('albumIds', [])
            
        else:
            self.contents = []
            self.bg_fmt = tkinter.StringVar()
            self.bg_color = tkinter.StringVar()
            self.bg_src = tkinter.StringVar()
            self.active_albumIds = []

        self.main_frame = ScrollableFrame(parent)

        #frame4 = tkinter.Frame(self.main_frame.scrollable_frame)
        #lbl1 = tkinter.Label(frame4, text='select albums')
        #lbl1.pack()
        # Windowsではcache_discovery, Linuxではstatic_discovery
        #service = build('photoslibrary', 'v1', credentials=creds, cache_discovery=False)
        service = build('photoslibrary', 'v1', credentials=creds, static_discovery=False)
        self.album_list = service.albums().list().execute().get('albums', None)
        self.albumId_vars = {}
        for album in self.album_list:
            if album['id'] in self.active_albumIds:
                self.albumId_vars[album['id']] = tkinter.BooleanVar(value=True)
            else:
                self.albumId_vars[album['id']] = tkinter.BooleanVar(value=False)
            #chk = tkinter.Checkbutton(frame4, text=album['title'], variable=self.albumId_vars[album['id']])
            #chk.pack(anchor='nw')


        frame1 = tkinter.Frame(self.main_frame.scrollable_frame)
        lbl1 = tkinter.Label(frame1, text='background format')
        cmx1 = ttk.Combobox(frame1, textvariable=self.bg_fmt, values=['full_screen', 'whole_image'], state='readonly')
        lbl1.pack()
        cmx1.pack() 

        frame2 = tkinter.Frame(self.main_frame.scrollable_frame)
        lbl2 = tkinter.Label(frame2, text='background color')
        cmx2 = ttk.Combobox(frame2, textvariable=self.bg_color, values=['white', 'black', 'red', 'blue', 'yellow'])
        lbl2.pack()
        cmx2.pack()

        frame3 = tkinter.Frame(self.main_frame.scrollable_frame)
        lbl3 = tkinter.Label(frame3, text='background source')
        lbl3.pack()
        cmx3 = ttk.Combobox(frame3, textvariable=self.bg_src, values=['Google_Photo', ''], state='readonly')
        cmx3.bind("<<ComboboxSelected>>", self.change_btn)
        if self.bg_src.get() in ['Google_Photo']:
            self.btn = tkinter.Button(frame3, text='select album', command=self.select_album, state='normal')
        else:
            self.btn = tkinter.Button(frame3, text='select album', command=self.select_album, state='disabled')
        lbl3.pack()
        cmx3.pack()
        self.btn.pack()

        frame1.grid(row=0, column=0)
        frame2.grid(row=0, column=1)
        frame3.grid(row=1, column=0)

    def change_btn(self, event=None):
        if self.bg_src.get() in ['Google_Photo']:
            self.btn['state'] = 'normal'
            self.select_album()
        else:
            self.btn['state'] = 'disabled'

    def select_album(self):
        sub = tkinter.Toplevel()
        lbl = tkinter.Label(sub, text='select album')
        lbl.pack()
        for album in self.album_list:
            chk = tkinter.Checkbutton(sub, text=album['title'], variable=self.albumId_vars[album['id']])
            chk.pack()

    def save(self, event=None):
        self.active_albumIds = []
        for albumId, var in self.albumId_vars.items():
            if var.get() == True:
                self.active_albumIds.append(albumId)
        return {'bg_fmt': self.bg_fmt.get(),
        'bg_color': self.bg_color.get(),
        'bg_src': self.bg_src.get(),
        'albumIds': self.active_albumIds}

def run():
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly', 'https://www.googleapis.com/auth/photoslibrary.readonly', 'https://www.googleapis.com/auth/tasks.readonly']
    creds = get_creds(SCOPES)

    root = tkinter.Tk()
    root.title('setting')
    test = Setting(root, creds)

    bottom_frame = tkinter.Frame(root, relief=tkinter.GROOVE, bd=4)
    preview_btn = tkinter.Button(bottom_frame, text='preview', command=test.preview)
    save_btn = tkinter.Button(bottom_frame, text='save', command=test.save)

    preview_btn.pack(expand=True, fill=tkinter.X)
    save_btn.pack(expand=True, fill=tkinter.X)
    bottom_frame.grid(row=1, column=0, columnspan=2, sticky=tkinter.W+tkinter.E)

    root.mainloop()

if __name__ == '__main__':
    run()