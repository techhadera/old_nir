import json
import logging
import os.path
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backend_bases import key_press_handler
from matplotlib.dates import (YEARLY, DateFormatter, rrulewrapper, RRuleLocator, drange)
from datetime import datetime
import vk_api
import tkinter as tk
import tkinter.scrolledtext as ScrolledText
from tkinter import filedialog
from tkinter import Menu
from tkinter import messagebox
from tkinter import ttk
from collections import defaultdict


like_activity_per_day = []
comment_activity_per_day = []
reach_total_age_per_week = defaultdict()
reach_total_cities_per_week = defaultdict()
reach_sex_per_day = []
period_from = [];
period_to = [];

global load_flag
load_flag = False

# Класс логгера
class TextHandler(logging.Handler):
    def __init__(self, text):
        logging.Handler.__init__(self)
        self.text = text

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text.configure(state='normal')
            self.text.insert(tk.END, msg + '\n')
            self.text.configure(state='disabled')
            self.text.yview(tk.END)
        self.text.after(0, append)

def config_plot():
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.set(xlabel='x', ylabel='y', title='График')
    return (fig, ax)

# Класс переключателя графиков, графопостроитель
class matplotlibSwitchGraphs:
    def __init__(self, master):
        self.master = master
        self.frame = tk.Frame(self.master)
        self.fig, self.ax = config_plot()
        self.graphIndex = 0
        self.canvas = FigureCanvasTkAgg(self.fig, self.master)
        self.config_window()
        self.draw_graph()
        self.frame.pack(expand=tk.YES, fill=tk.BOTH)

    def config_window(self):
        self.canvas.mpl_connect("key_press_event", self.on_key_press)
        toolbar = NavigationToolbar2Tk(self.canvas, self.master)
        toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.button_switch = tk.Button(self.master, text="Switch Graphs", command=self.switch_graphs)
        self.button_switch.pack(side=tk.BOTTOM)

    def draw_graph(self, x=0, y=0, xlabel='x', ylabel='y', title='Статистика группы', type="None"):
        self.ax.clear()
        self.ax.xaxis.set_tick_params(rotation=0, labelsize=10)
        
        if type == "None":
            pass

        elif type == "like_graph":
            x = period_to[::-1]
            y = like_activity_per_day[::-1]
            self.ax.plot(x, y)
            self.ax.set(xlabel="день", ylabel="количество лайков", title=title)
            self.canvas.draw()

        elif type == "comment_graph":
            x = period_to[::-1]
            y = comment_activity_per_day[::-1]
            self.ax.plot(x, y)
            self.ax.set(xlabel="день", ylabel="количество комментариев", title=title)
            self.canvas.draw()

        elif type == "cities_graph":
            y = reach_total_cities_per_week
            self.ax.bar(y.keys(), y.values(), 1, color='g', edgecolor='#6bf442')
            self.ax.xaxis.set_tick_params(rotation=80, labelsize=6)
            self.ax.set(xlabel="город", ylabel="количество посетителей", title=title)
            self.canvas.draw()

        elif type == "ages_graph":
            y = reach_total_age_per_week
            self.ax.bar(y.keys(), y.values(), 1, color='#6018cc', edgecolor='#834dd6')
            self.ax.set(xlabel="возраст", ylabel="количество посетителей", title=title)
            self.canvas.draw()

        elif type == "sex_graph":
            y = reach_sex_per_day
            self.ax.bar("Females", y[0]["count"], 1, color='#dd0fc5', edgecolor='#db55cb')
            self.ax.bar("Males", y[1]["count"], 1, color='#0b37e5', edgecolor='#5775ed')
            self.ax.set(xlabel="пол", ylabel="количество посетителей", title=title)
            self.canvas.draw()


    def on_key_press(event):
        print("you pressed {}".format(event.key))
        key_press_handler(event, self.canvas, toolbar)

    def _quit(self):
        self.master.quit()

    def switch_graphs(self):
        if not load_flag:
            logging.info("Json file is not loaded")
            messagebox.showerror("Error", "Json file is not loaded")
            return 0

        self.graphIndex = (self.graphIndex + 1 ) % 5
        if self.graphIndex == 0:
            self.draw_graph(type="like_graph", title="Статистика лайков по дням")
        elif self.graphIndex == 1:
            self.draw_graph(type="comment_graph", title="Статистика комментариев по дням")
        elif self.graphIndex == 2:
            self.draw_graph(type="cities_graph", title="Статистика посетителей по городам за неделю")
        elif self.graphIndex == 3:
            self.draw_graph(type="ages_graph", title="Статистика посетителей по возрасту за неделю")
        elif self.graphIndex == 4:
            self.draw_graph(type="sex_graph", title="Статистика посетителей по полу за неделю")
     

# Функция для проверки того, введена ли группа
def click_analyze():
    if(vk_group_name.get()):
        logging.info("Entered valid name") 
        check_data_exists(vk_group_name.get())
    else:
        logging.info("Invalid name, input is empty") 
        messagebox.showerror("Error", "Group name field is empty")

# Функция проверяющая существование файла с данными о группе
def check_data_exists(vk_group_name):
    file_path = "groups\\" + vk_group_name + ".json"
    if(os.path.exists(file_path)):
        logging.info("Data for this group is already stored in " + file_path) 
        choice = messagebox.askyesno("Warning", "File is already exists, do you want to rewrite data?")
        if choice:
            check_group_exists(vk_group_name)
            logging.info("Data for this group has been rewrited")
    else:
        check_group_exists(vk_group_name)

# Функция проверяющая существование группы
def check_group_exists(vk_group_name):
    try:
        group_info = vk.groups.getById(group_id = vk_group_name)
        group_id = group_info[0].get("id")
        logging.info("Group exists, it's possible to gather data") 
        check_stats_method(group_id, vk_group_name);
    except vk_api.exceptions.ApiError:
        logging.info("Error, group " + vk_group_name + " does not exist or connection problem occurred") 
        messagebox.showerror("Error", vk_group_name + " doesn't exist or not reachable")
  
# Функция проверяет доступен ли stats.get метод
def check_stats_method(group_id, vk_group_name):
        try:
            group_stats = vk.stats.get(group_id = group_id, interval = "day", intervals_count = 1)
            logging.info("Stats method is available for " + vk_group_name + " ID:" + str(group_id)) 
            stats_method(group_id, vk_group_name)
        except vk_api.exceptions.ApiError:
            logging.info("Stats method is not available for " + vk_group_name)
            messagebox.showwarning("Warning", "Stats method is not available for this group, choose another one")
            #alternative method
            # ERROR?

# Функция сохраняет данные о группе в json файл в папку "groups"
def stats_method(group_id, vk_group_name):
    group_stats = vk.stats.get(group_id = group_id, interval = "day", intervals_count = 7)
    with open('groups/' + vk_group_name + '.json', 'w', encoding='utf8') as outfile:
        json.dump(group_stats, outfile,  ensure_ascii=False)
    logging.info("Data for last 7 days from " + vk_group_name + " has been gathered") 


# Выход из программы
def _quit():
    win.quit()
    win.destroy()
    exit()

# Загрузка json файла, содержащий информацию о группе и коипрование данных в соот-щие массивы
def _load():
    global like_activity_per_day
    like_activity_per_day = []
    global comment_activity_per_day
    comment_activity_per_day = []
    global reach_total_age_per_week
    reach_total_age_per_week = defaultdict()
    global reach_total_cities_per_week
    reach_total_cities_per_week = defaultdict()
    global reach_sex_per_day
    reach_sex_per_day = []
    global period_from;
    period_from = [];
    global period_to;
    period_to = [];

    win.file_name = filedialog.askopenfilename(filetypes = (("JSON data", ".json"), ("all", "*.*")))
    with open(win.file_name, 'r', encoding='utf8') as infile:
            datastore = json.load(infile)
    logging.info("file " + win.file_name + " is loaded") 
    
    global load_flag
    load_flag = True
    
    for elem in datastore:
        try:
            comment_activity_per_day.append(elem["activity"]["comments"])
        except:
            comment_activity_per_day.append(0)
        try:
            like_activity_per_day.append(elem["activity"]["likes"])
        except:
            like_activity_per_day.append(0)
        try:
            ts = int(elem["period_to"])
            date = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d')
            period_to.append(date)
        except:
            period_to.append(0)

    for i in elem["reach"]["age"]:
        if i["value"] in reach_total_age_per_week:
            reach_total_age_per_week[i["value"]] += i["count"]
        else:
            reach_total_age_per_week[i["value"]] = i["count"]

    for j in elem["reach"]["cities"]:
        if j["name"] in reach_total_cities_per_week:
            reach_total_cities_per_week[j["name"]] += j["count"]
        else:
            reach_total_cities_per_week[j["name"]] = j["count"]

    for k in elem["reach"]["sex"]:
        reach_sex_per_day.append(k)



def _info():
    messagebox.showinfo("Info", "Программа vkApplication предназначена для визуализации "
                                "данных о группах социальной сети ВКонтакте.")

#Ввести свои данные
vk_session = vk_api.VkApi('phone', 'enter_pass')
vk_session.auth()
vk = vk_session.get_api()
tools = vk_api.VkTools(vk_session)

# Инициализация окна интерфейса
win = tk.Tk()
win.resizable(0, 0)
win.iconbitmap(r'vk_icon.ico')
win.title("Vk application")

# Контейнер с вводом группы
container = ttk.LabelFrame(win)
container.grid(column=0, row=0)
# Контейнер с графиками
plots = ttk.LabelFrame(win)
plots.grid(column=0, row=1)
# Контейнер с логами
log_window = ttk.LabelFrame(win)
log_window.grid(column=0, row=2)

# Описание контейнера с вводом группы
entry_label = ttk.Label(container, text="Enter VK group name: ")
entry_label.grid(column=0, row=0, sticky=tk.N)
vk_group_name = tk.StringVar()
vk_group_name_entered = ttk.Entry(container, width=25, textvariable=vk_group_name)
vk_group_name_entered.grid(column=2, row=0)
vk_group_name_entered.focus() 
action = ttk.Button(container, text="Analyze", command=click_analyze)
action.grid(column=3, row=0)

# Создание свитчера
matplotlibSwitchGraphs(plots)

# Создание логгера
st = ScrolledText.ScrolledText(log_window, state='disabled', height=4)
st.configure(font='TkFixedFont')
st.pack(side=tk.BOTTOM)
text_handler = TextHandler(st)
logging.basicConfig(filename='test.log', level=logging.INFO)        
logger = logging.getLogger()        
logger.addHandler(text_handler)

# Создание меню
menu_bar = Menu(win)
win.config(menu=menu_bar)

options_menu = Menu(menu_bar,  tearoff=0)
menu_bar.add_cascade(label="Options", menu=options_menu)
options_menu.add_command(label="Load file", command=_load)

win.mainloop()

