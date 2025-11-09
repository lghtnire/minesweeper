import tkinter as tk
from tkinter import messagebox
import random
import json
from PIL import Image,ImageTk
import sys
import os

def resource_path(relative_path):
    """获取资源文件的绝对路径，兼容PyInstaller打包后的路径"""
    try:
        # PyInstaller创建临时文件夹，将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class Minesweeper:
    def __init__(self, master, sizes=(8,8), mines=10,size=30):
        self.root = master
        self.rows = sizes[0]
        self.cols = sizes[1]
        self.mines = mines
        self.size=size
        # 画布与窗口之间的边距（像素）
        self.pad = 20
        # 顶部闪电与画布的间距
        self.top_margin = 4
        # 游戏是否已经结束（胜利或失败）
        self.finished = False
        self.mode="tradition"
        #录入图片
        imgs0 = [Image.open(resource_path(f'images/type{i}.jpg')).resize((self.size,self.size)) for i in range(9)]
        imgs1 = [Image.open(resource_path(f'images/mine{i}.jpg')).resize((self.size,self.size)) for i in range(4)]
        self.type_imgs = [ImageTk.PhotoImage(img) for img in imgs0]
        self.mine_imgs = [ImageTk.PhotoImage(img) for img in imgs1]
        # 载入重启按钮图标（闪电）及失败/成功图标，若加载失败则使用文本按钮作为回退
        def _load_icon(fname, scale=1.5):
            try:
                s = max(1, int(round(self.size * scale)))
                img = Image.open(resource_path(f'images/{fname}')).resize((s, s))
                return ImageTk.PhotoImage(img)
            except Exception:
                return None


        self.restart_img = _load_icon('闪电.jpg', scale=1.5)
        self.restart_img_press = _load_icon('闪电2.jpg', scale=1.5)
        self.restart_img_fail = _load_icon('闪电1.jpg', scale=1.5)
        self.restart_img_success = _load_icon('闪电3.jpg', scale=1.5)
        # 设置项变量：失败/胜利自动重开与R键重开
        self.auto_restart_on_fail_var = tk.BooleanVar(value=False)
        self.auto_restart_on_win_var = tk.BooleanVar(value=False)
        self.enable_r_restart_var = tk.BooleanVar(value=False)
        # 持久化配置文件路径
        self.settings_path = os.path.join(os.path.abspath('.'), 'minesweeper_settings.json')
        # 监听变量修改以自动保存并即时生效
        try:
            self.auto_restart_on_fail_var.trace_add('write', lambda *args: self.save_settings())
            self.auto_restart_on_win_var.trace_add('write', lambda *args: self.save_settings())
            self.enable_r_restart_var.trace_add('write', lambda *args: (self._toggle_r_bind(), self.save_settings()))
        except Exception:
            pass
        # 加载保存的设置（如果存在）
        try:
            self.load_settings()
        except Exception:
            pass
        self.menu()
        # 顶部工具栏（放置重启按钮）
        self.top_frame = tk.Frame(self.root)
        self.top_frame.pack(side='top', fill='x')
        # 如果图片加载成功，使用图片按钮；否则使用文字按钮
        if getattr(self, 'restart_img', None) is not None:
            self.restart_button = tk.Button(self.top_frame, image=self.restart_img, command=self.restart, bd=0)
        else:
            self.restart_button = tk.Button(self.top_frame, text='新游戏', command=self.restart)
        # 缩小闪电与游戏的像素间距
        self.restart_button.pack(pady=(4, 0))

        h=self.rows*self.size
        w=self.cols*self.size
        self.canvas=tk.Canvas(self.root,height=h,width=w)
        self.new_game((8,8),10)

    def reload_images(self):
        """根据当前 self.size (像素) 重新加载并缩放图片资源（若缺文件会抛异常）"""
        imgs0 = [Image.open(resource_path(f'images/type{i}.jpg')).resize((self.size, self.size)) for i in range(9)]
        imgs1 = [Image.open(resource_path(f'images/mine{i}.jpg')).resize((self.size, self.size)) for i in range(4)]
        self.type_imgs = [ImageTk.PhotoImage(img) for img in imgs0]
        self.mine_imgs = [ImageTk.PhotoImage(img) for img in imgs1]
        # 也尝试重载重启图标（如果存在）
        try:
            if getattr(self, 'restart_img', None) is not None:
                s = max(1, int(round(self.size * 1.5)))
                self.restart_img = ImageTk.PhotoImage(Image.open(resource_path('images/闪电.jpg')).resize((s, s)))
            if getattr(self, 'restart_img_press', None) is not None:
                s = max(1, int(round(self.size * 1.5)))
                self.restart_img_press = ImageTk.PhotoImage(Image.open(resource_path('images/闪电2.jpg')).resize((s, s)))
            if getattr(self, 'restart_img_fail', None) is not None:
                s = max(1, int(round(self.size * 1.5)))
                self.restart_img_fail = ImageTk.PhotoImage(Image.open(resource_path('images/闪电1.jpg')).resize((s, s)))
            if getattr(self, 'restart_img_success', None) is not None:
                s = max(1, int(round(self.size * 1.5)))
                self.restart_img_success = ImageTk.PhotoImage(Image.open(resource_path('images/闪电3.jpg')).resize((s, s)))
        except Exception:
            pass

    def set_restart_icon(self, state='normal'):
        """切换顶部重启按钮图标：state in ('normal','fail','success')"""
        if not hasattr(self, 'restart_button'):
            return
        if state == 'fail' and getattr(self, 'restart_img_fail', None) is not None:
            self.restart_button.config(image=self.restart_img_fail, text='')
        elif state == 'success' and getattr(self, 'restart_img_success', None) is not None:
            self.restart_button.config(image=self.restart_img_success, text='')
        elif state == 'press' and getattr(self, 'restart_img_press', None) is not None:
            self.restart_button.config(image=self.restart_img_press, text='')
        elif getattr(self, 'restart_img', None) is not None:
            self.restart_button.config(image=self.restart_img, text='')
        else:
            txt = '新游戏'
            if state == 'fail':
                txt = '失败'
            elif state == 'success':
                txt = '胜利'
            self.restart_button.config(image='', text=txt)

    def create_widgets(self):
        """创建游戏界面"""
        self.canvas.delete("all")
        h=self.rows*self.size
        w=self.cols*self.size
        self.canvas.config(height=h,width=w)
        # 临时按下状态跟踪（用于在按下时显示 type0 临时图标）
        self.pressed_cells = set()
        self.both_pressed = False
        self.last_press_center = None
        self.image_map = [[None]*self.cols for i in range(self.rows)]
        for row in range(self.rows): 
            for col in range(self.cols): 
                x = (col+1/2) * self.size  # 计算x坐标
                y = (row+1/2) * self.size  # 计算y坐标
                self.image_map[row][col]=self.canvas.create_image(x, y, image=self.mine_imgs[-1])
        
        # 绑定事件处理器
        self.left_pressed = False
        self.right_pressed = False
        # 记录右键按下时是否已执行标记，以避免 release 时重复
        self.right_did_mark_on_press = False
        self.right_marked_coord = None
        
        self.canvas.bind("<ButtonPress-1>", self.on_left_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_left_release)
        self.canvas.bind("<ButtonPress-3>", self.on_right_press)
        self.canvas.bind("<ButtonRelease-3>", self.on_right_release)
        self.canvas.bind("<ButtonPress-2>", self.on_middle_press)
        # 顶部与画布之间使用较小的上边距
        self.canvas.pack(padx=self.pad, pady=(self.top_margin, self.pad))
        
    def menu(self):
        # 主菜单
        self.menubar = tk.Menu(self.root)
        
        self.menubar.add_command(label="新游戏", command=self.restart)
        
        menu_new = tk.Menu(self.menubar, tearoff=False)
        grade = ('初级8x8','中级16x16','高级16x30','自定义')
        menu_new.add_command(label=grade[0], command=lambda *e: self.new_game((8,8),10))
        menu_new.add_command(label=grade[1], command=lambda *e: self.new_game((16,16),40))
        menu_new.add_command(label=grade[2], command=lambda *e: self.new_game((16,30),99))
        menu_new.add_command(label=grade[3], command= self.open_input_dialog)
        self.menubar.add_cascade(label="经典模式", menu=menu_new)
        
        menu1 = tk.Menu(self.menubar, tearoff=False)
        grade = ('找漏雷','直线判雷','定式判雷')
        menu1.add_command(label=grade[0], command=self.find_mine)
        menu1.add_command(label=grade[1], command=self.exercise1)
        menu1.add_command(label=grade[2], command=self.exercise2)
        self.menubar.add_cascade(label="训练模式", menu=menu1)
        
        # 设置菜单：允许修改格子像素大小和其他选项（并提供单独设置界面）
        menu_set = tk.Menu(self.menubar, tearoff=False)
        menu_set.add_command(label="格子大小...", command=self.open_size_dialog)
        # 新增可选设置：失败自动重开、胜利自动重开、R键重开
        try:
            menu_set.add_checkbutton(label="失败自动重开", variable=self.auto_restart_on_fail_var)
            menu_set.add_checkbutton(label="胜利自动重开", variable=self.auto_restart_on_win_var)
            menu_set.add_checkbutton(label="R键重开", variable=self.enable_r_restart_var, command=self._toggle_r_bind)
        except Exception:
            pass
        # 菜单中显示当前 R 键绑定状态（只读项），后续通过 _update_r_status_menu 更新显示
        menu_set.add_separator()
        menu_set.add_command(label="R键：未绑定", state='disabled')
        # 保存对 menu_set 的引用，用于更新状态文本
        self.menu_set = menu_set
        self.r_status_menu_index = menu_set.index('end')
        # 另外，提供一个完整的设置页入口
        menu_set.add_command(label="打开设置页面...", command=self.open_settings_window)
        self.menubar.add_cascade(label="设置", menu=menu_set)
        # 更新 R 状态显示以反映当前绑定
        try:
            self._update_r_status_menu()
        except Exception:
            pass

        self.root.config(menu=self.menubar)

    def open_input_dialog(self):
        """创建输入弹窗"""
        # 创建Toplevel弹窗
        dialog = tk.Toplevel(self.root)
        dialog.title("输入弹窗")
        dialog.geometry("300x150")
        
        # 输入框
        tk.Label(dialog, text="请输入行，列，雷数：").pack(pady=10)
        entry = tk.Entry(dialog, width=25)
        entry.pack(pady=5)
        entry.focus_set()  # 自动聚焦输入框
        
        # 确定按钮
        def on_confirm():
            input_text = entry.get()  # 获取输入内容
            input_list=list(input_text.split())
            sizes=(int(input_list[0]),int(input_list[1]))
            mines=int(input_list[2])
            self.new_game(sizes,mines)
            self.mode="tradition"
            dialog.destroy()  # 关闭弹窗
            
        tk.Button(
            dialog, 
            text="确定", 
            command=on_confirm
        ).pack(pady=10)

    def open_size_dialog(self):
        """创建输入弹窗，用于设置每个格子的像素大小（重新开始游戏）"""
        dialog = tk.Toplevel(self.root)
        dialog.title("设置格子大小")
        dialog.geometry("300x150")
        tk.Label(dialog, text="请输入格子像素大小（默认30）：").pack(pady=10)
        entry = tk.Entry(dialog, width=25)
        entry.pack(pady=5)
        entry.insert(0, str(self.size))
        entry.focus_set()

        def on_confirm_size():
            try:
                new_size = int(entry.get())
                if new_size <= 0:
                    raise ValueError
            except Exception:
                tk.messagebox.showerror("输入错误", "请输入一个正整数作为像素大小。")
                return
            # 更新尺寸，重载图片并重新开始游戏
            self.size = new_size
            try:
                self.reload_images()
            except Exception:
                tk.messagebox.showwarning("警告", "图片资源加载失败，保持旧大小。")
            # 重新配置 canvas 大小并确保窗口足够大
            h = self.rows * self.size
            w = self.cols * self.size
            try:
                self.canvas.config(width=w, height=h)
                # 调整主窗口最小尺寸，考虑画布边距
                try:
                    self.root.minsize(w + 2*self.pad, h + 2*self.pad)
                except Exception:
                    pass
            except Exception:
                # 如果 canvas 尚未创建或配置失败，忽略并让 new_game 重新创建
                pass
            # 重新开始当前模式（使用 new_game 保持传统模式）
            self.new_game((self.rows, self.cols), self.mines)
            dialog.destroy()

        tk.Button(dialog, text="确定", command=on_confirm_size).pack(pady=10)

    def open_settings_window(self):
        """打开单独的设置界面（Toplevel），以更直观地调整选项并保存"""
        # 防止同时打开多个设置窗口
        try:
            if getattr(self, '_settings_window', None) and tk.Toplevel.winfo_exists(self._settings_window):
                self._settings_window.lift()
                return
        except Exception:
            pass

        w = tk.Toplevel(self.root)
        w.title('设置')
        w.geometry('320x200')
        self._settings_window = w

        frm = tk.Frame(w)
        frm.pack(fill='both', expand=True, padx=12, pady=12)

        cb1 = tk.Checkbutton(frm, text='失败自动重开', variable=self.auto_restart_on_fail_var)
        cb1.pack(anchor='w', pady=4)
        cb2 = tk.Checkbutton(frm, text='胜利自动重开', variable=self.auto_restart_on_win_var)
        cb2.pack(anchor='w', pady=4)
        cb3 = tk.Checkbutton(frm, text='启用 R 键重开', variable=self.enable_r_restart_var, command=self._toggle_r_bind)
        cb3.pack(anchor='w', pady=4)

        # 显示 R 绑定当前状态
        lbl = tk.Label(frm, text='R键状态：已绑定' if (self.enable_r_restart_var.get()) else 'R键状态：未绑定')
        lbl.pack(anchor='w', pady=(8, 4))

        def on_close():
            try:
                # 保存设置并更新菜单状态
                self.save_settings()
                self._update_r_status_menu()
            except Exception:
                pass
            try:
                w.destroy()
            except Exception:
                pass

        tk.Button(frm, text='保存并关闭', command=on_close).pack(side='right', pady=8)

    def _toggle_r_bind(self):
        """绑定或解绑 R 键用于重开（由设置菜单中的复选框控制）"""
        try:
            if getattr(self, 'enable_r_restart_var', None) and self.enable_r_restart_var.get():
                # 绑定小写与大写 r
                self.root.bind('<r>', self._on_r_key)
                self.root.bind('<R>', self._on_r_key)
            else:
                try:
                    self.root.unbind('<r>')
                except Exception:
                    pass
                try:
                    self.root.unbind('<R>')
                except Exception:
                    pass
            # 更新菜单中的 R 键状态显示（如果存在）
            try:
                self._update_r_status_menu()
            except Exception:
                pass
        except Exception:
            pass

    def _on_r_key(self, event):
        """R 键按下事件处理器，触发重开"""
        try:
            self.restart()
        except Exception:
            pass

    def _update_r_status_menu(self):
        """更新菜单中显示的 R 键绑定状态（只读文本项）"""
        try:
            if not hasattr(self, 'menu_set') or not hasattr(self, 'r_status_menu_index'):
                return
            status = '已绑定' if (getattr(self, 'enable_r_restart_var', None) and self.enable_r_restart_var.get()) else '未绑定'
            label = f"R键：{status}"
            try:
                self.menu_set.entryconfig(self.r_status_menu_index, label=label)
            except Exception:
                # 备用方式，尝试按字符串索引更新
                try:
                    self.menu_set.entryconfig('end', label=label)
                except Exception:
                    pass
        except Exception:
            pass

    def save_settings(self):
        """将当前设置保存到磁盘（JSON）。"""
        try:
            data = {
                'auto_restart_on_fail': bool(self.auto_restart_on_fail_var.get()),
                'auto_restart_on_win': bool(self.auto_restart_on_win_var.get()),
                'enable_r_restart': bool(self.enable_r_restart_var.get())
            }
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load_settings(self):
        """从磁盘加载设置（如果存在），并应用到变量。"""
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                try:
                    self.auto_restart_on_fail_var.set(bool(data.get('auto_restart_on_fail', False)))
                except Exception:
                    pass
                try:
                    self.auto_restart_on_win_var.set(bool(data.get('auto_restart_on_win', False)))
                except Exception:
                    pass
                try:
                    self.enable_r_restart_var.set(bool(data.get('enable_r_restart', False)))
                except Exception:
                    pass
                # 根据加载的值更新 R 绑定状态
                try:
                    self._toggle_r_bind()
                except Exception:
                    pass
        except Exception:
            pass

    def restart(self):
        # 重置 finished 标志并恢复为普通新游戏图标
        try:
            self.finished = False
        except Exception:
            pass
        try:
            self.set_restart_icon('normal')
        except Exception:
            pass
        # 重置首次点击状态
        try:
            self.first_click = True
        except Exception:
            pass
        if self.mode=="tradition":
            self.create_widgets()
            self.mine_coords = set()
            self.revealed = set()
            self.marked = set()
            self.place_mines()
            self.calculate_numbers()
        elif self.mode=="find_mine":
            self.find_mine()
        elif self.mode=="exercise1":
            self.exercise1()
        elif self.mode=="exercise2":
            self.exercise2()
            
            


    def new_game(self,sizes,mines):
        self.rows=sizes[0]
        self.cols=sizes[1]
        self.mines=mines
        # 首次点击需保证开空
        self.first_click = True
        self.create_widgets()
        self.mine_coords = set()
        self.revealed = set()
        self.marked = set()
        self.place_mines()
        self.calculate_numbers()
        self.mode="tradition"
        
    def find_mine(self) :
        self.new_game((16,30),99)
        for r in range(16):
            for c in range(30):
                if self.numbers.get((r,c),None)==0:
                    self.reveal(r,c)
        optional_lst=[]
        for r in range(16):
            for c in range(30):
                if (r,c) in self.revealed or (r,c) in self.mine_coords:
                    continue
                else:
                    optional_lst.append((r,c))
        choice_coord=random.choice(optional_lst)
        optional_lst.remove(choice_coord)
        for coord in optional_lst:
            self.reveal(coord[0],coord[1])
        self.mode="find_mine"
    
    def exercise1(self):
        sizes=(4,30)
        self.rows=sizes[0]
        self.cols=sizes[1]
        self.create_widgets()
        self.mine_coords = set()
        self.revealed = set()
        self.marked = set()
        self.mines=0
        def generate_binary_list(k):
            lst = []
            # 第一位
            lst.append(random.choice([0,1]))            
            # 第二位
            lst.append(1 if lst[0] == 0 else random.choice([0,1]))            
            for _ in range(k):
                if len(lst) >= 2 and lst[-1] == 0 and lst[-2] == 0:
                    lst.append(1)                    
                else:
                    lst.append(random.choice([0,1]))
            return lst
        frmine_lst=generate_binary_list(30)
        for c in range(30):
            if frmine_lst[c]:
                self.mine_coords.add((0,c))
#         while len(self.mine_coords) < self.mines-10: #特殊布雷
#             r = random.randint(0, 1)
#             c = random.randint(0, self.cols-1)
#             if r==0:
#                 self.mine_coords.add((0, c))
#             else:
#                 self.mine_coords.add((2, c))
        srmine_lst = random.sample([i for i in range(30)], k=15)
        for c in srmine_lst:            
            self.mine_coords.add((2,c))
        for _ in range(10):
            self.mine_coords.add((3,3*_+1))
        self.mine_coords.add((2,0))
        self.mine_coords.add((2,1))
        self.calculate_numbers()
        for c in range(self.cols):
            self.reveal(1,c)
            if (0,c) in self.mine_coords:
                self.mark_mine(0,c)
            else:
                self.reveal(0,c)
        self.mode="exercise1"    
        
    def exercise2(self):
        self.mines=0
        sizes=(5,6)
        self.rows=sizes[0]
        self.cols=sizes[1]
        self.create_widgets()
        self.mine_coords = set()
        self.revealed = set()
        self.marked = set()
        def generate_binary_list(k):
            lst = []
            # 第一位
            lst.append(random.choice([0,1]))            
            # 第二位
            lst.append(1 if lst[0] == 0 else random.choice([0,1]))            
            for _ in range(k):
                if len(lst) >= 2 and lst[-1] == 0 and lst[-2] == 0:
                    lst.append(1)                    
                else:
                    lst.append(random.choice([0,1]))
            return lst
        srmine_lst=generate_binary_list(4)
        for c in range(4):
            if not srmine_lst[c]:
                self.mine_coords.add((1,c))
        mine_lsts=[[0,1],[0,2],[1,2],[1]]
        mine_lst=random.choice(mine_lsts)
        for c in mine_lst:
            self.mine_coords.add((3,c))
        self.mine_coords.add((4,4))
        self.mine_coords.add((2,3))
        self.calculate_numbers()
        for c in range(self.cols):
            self.reveal(0,c)
            if (1,c) in self.mine_coords:
                self.mark_mine(1,c)
            else:
                self.reveal(1,c)
             
            if (2,c) in self.mine_coords:
                self.mark_mine(2,c)
            else:
                self.reveal(2,c)
        self.reveal(3,3)
        self.mode="exercise2" 
    
    
    def reveal(self,r,c):
        """翻开格子"""
        if (r, c) in self.marked or (r, c) in self.revealed:
            return

        # 在传统模式下，首次点击应保证开空（数字0）——在 reveal 开始时调整雷位
        try:
            if getattr(self, 'mode', None) == 'tradition' and getattr(self, 'first_click', True):
                # 如果总格子数过小或雷太多，跳过保证开空以避免无限重排
                total = self.rows * self.cols
                if self.mines <= max(0, total - 9):
                    try:
                        self._ensure_first_click_empty(r, c)
                    except Exception:
                        pass
                self.first_click = False
        except Exception:
            pass

        if (r, c) in self.mine_coords:
            self.game_over()
            return
        
        if r>self.rows-1 or c>self.cols-1:
            return
        
        self.revealed.add((r, c))
        num = self.numbers.get((r, c), 0)
        self.canvas.delete(self.image_map[r][c])
        x1,y1=(c+0.5)*self.size,(r+0.5)*self.size
        self.image_map[r][c]=self.canvas.create_image(x1, y1, image=self.type_imgs[num])
        
        if num == 0:
            # 自动翻开周围格子
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        self.reveal(nr, nc)
                        self.revealed.add((nr, nc))
        
        self.check_win()
        
    def on_left_press(self, event):
        """左键按下"""
        self.left_pressed = True
        r = event.y//self.size
        c = event.x//self.size
        # 按下时切换重启图标为按下状态（闪电2.jpg）
        try:
            if not getattr(self, 'finished', False):
                self.set_restart_icon('press')
        except Exception:
            pass
        if self.right_pressed:
            # 同时按下左右键，显示中心及周围临时 type0 图标，延迟实际 double_click 到释放时
            self.both_pressed = True
            self.last_press_center = (r, c)
            # 显示临时图标
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        if (nr, nc) in self.revealed or (nr, nc) in self.marked:
                            continue
                        try:
                            self.canvas.delete(self.image_map[nr][nc])
                        except Exception:
                            pass
                        x = (nc+0.5) * self.size
                        y = (nr+0.5) * self.size
                        self.image_map[nr][nc] = self.canvas.create_image(x, y, image=self.type_imgs[0])
                        self.pressed_cells.add((nr, nc))
        else:
            # 单纯左键按下，仅把该格变为 type0（临时）
            if 0 <= r < self.rows and 0 <= c < self.cols and (r, c) not in self.revealed and (r, c) not in self.marked:
                try:
                    self.canvas.delete(self.image_map[r][c])
                except Exception:
                    pass
                x = (c+0.5) * self.size
                y = (r+0.5) * self.size
                self.image_map[r][c] = self.canvas.create_image(x, y, image=self.type_imgs[0])
                self.pressed_cells.add((r, c))
    
    def on_left_release(self, event):
        """左键释放"""
        r = event.y//self.size
        c = event.x//self.size
        # 先记录当前双键状态，然后标记左键已释放
        was_both = self.both_pressed
        self.left_pressed = False

        if was_both:
            # 在双键按下场景，只需任意一个键松开即可执行 double_click
            center = self.last_press_center or (r, c)
            before = set(self.revealed)
            self.double_click(center[0], center[1])
            after = set(self.revealed)
            # 如果 double_click 没有实际翻开任何新格，则需要把临时显示的格恢复为覆盖态
            if after == before:
                for (nr, nc) in list(self.pressed_cells):
                    if (nr, nc) not in self.revealed and (nr, nc) not in self.marked:
                        try:
                            self.canvas.delete(self.image_map[nr][nc])
                        except Exception:
                            pass
                        x = (nc+0.5) * self.size
                        y = (nr+0.5) * self.size
                        self.image_map[nr][nc] = self.canvas.create_image(x, y, image=self.mine_imgs[-1])
            # 清理状态
            self.pressed_cells.clear()
            self.both_pressed = False
            self.last_press_center = None
        else:
            # 单次左键释放且右键未按下 -> 翻开
            if not self.right_pressed:
                self.reveal(r, c)
                self.pressed_cells.clear()

        # 释放后恢复重启图标为普通状态（若游戏未结束）
        try:
            if not getattr(self, 'finished', False):
                self.set_restart_icon('normal')
        except Exception:
            pass
    
    def on_right_press(self, event):
        """右键按下"""
        self.right_pressed = True
        r = event.y//self.size
        c = event.x//self.size
        # 右键按下不改变闪电图标（只在左键按下时切换）
        if self.left_pressed:
            # 同时按下左右键，显示中心及周围临时 type0 图标，延迟实际 double_click 到释放时
            self.both_pressed = True
            self.last_press_center = (r, c)
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        if (nr, nc) in self.revealed or (nr, nc) in self.marked:
                            continue
                        try:
                            self.canvas.delete(self.image_map[nr][nc])
                        except Exception:
                            pass
                        x = (nc+0.5) * self.size
                        y = (nr+0.5) * self.size
                        self.image_map[nr][nc] = self.canvas.create_image(x, y, image=self.type_imgs[0])
                        self.pressed_cells.add((nr, nc))
        else:
            # 若未同时按下左键，则在按下时立即执行标记操作（按下即布雷）
            try:
                self.mark_mine(r, c)
                # 记录此坐标以在 release 时避免重复标记
                self.right_did_mark_on_press = True
                self.right_marked_coord = (r, c)
            except Exception:
                # 忽略任何标记时的异常，保证按下不会中断流程
                self.right_did_mark_on_press = False
                self.right_marked_coord = None
    
    def on_right_release(self, event):
        """右键释放"""
        r = event.y//self.size
        c = event.x//self.size
        was_both = self.both_pressed
        # 标记右键已释放
        self.right_pressed = False

        if was_both:
            # 在双键按下场景，只需任意一个键松开即可执行 double_click
            center = self.last_press_center or (r, c)
            before = set(self.revealed)
            self.double_click(center[0], center[1])
            after = set(self.revealed)
            if after == before:
                for (nr, nc) in list(self.pressed_cells):
                    if (nr, nc) not in self.revealed and (nr, nc) not in self.marked:
                        try:
                            self.canvas.delete(self.image_map[nr][nc])
                        except Exception:
                            pass
                        x = (nc+0.5) * self.size
                        y = (nr+0.5) * self.size
                        self.image_map[nr][nc] = self.canvas.create_image(x, y, image=self.mine_imgs[-1])
            self.pressed_cells.clear()
            self.both_pressed = False
            self.last_press_center = None
        else:
            # 单独右键释放，且左键未按下 -> 若按下时未已执行标记，则在释放时执行标记
            if not self.left_pressed:
                if not (self.right_did_mark_on_press and self.right_marked_coord == (r, c)):
                    # 只有在按下时未标记过同一格时，才在释放时执行标记
                    self.mark_mine(r, c)

        # 无论如何，清理按下时记录的标记状态（避免长期保留）
        self.right_did_mark_on_press = False
        self.right_marked_coord = None

        # 右键释放不改变闪电图标（闪电由左键按下/释放控制）
    
    def on_middle_press(self, event):
        """中键按下，重新开始游戏"""
        self.restart()
        
    def double_click(self, r, c):
        """双击翻开周围格子"""
        if (r, c) not in self.revealed or (r, c) in self.marked:
            return
        
        num = self.numbers.get((r, c), 0)
        if num == 0:
            return
        
        # 检查周围是否有标记的地雷
        marked_count = sum((r+dr, c+dc) in self.marked for dr in [-1, 0, 1] for dc in [-1, 0, 1])
        
        if marked_count == num:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        self.reveal(nr, nc)

    def mark_mine(self,r,c):
        """右键标记地雷"""
        x1,y1=(c+0.5)*self.size,(r+0.5)*self.size
        if (r, c) in self.revealed:
            return
        
        if r>self.rows-1 or c>self.cols-1:
            return
        
        if (r, c) in self.marked:
            self.marked.remove((r, c))
            self.canvas.delete(self.image_map[r][c])
            self.image_map[r][c]=self.canvas.create_image(x1, y1, image=self.mine_imgs[-1])
        else:
            self.marked.add((r, c))
            self.canvas.delete(self.image_map[r][c])
            self.image_map[r][c]=self.canvas.create_image(x1, y1, image=self.mine_imgs[-2])


    def place_mines(self):
        """随机布置地雷"""
        while len(self.mine_coords) < self.mines:
            r = random.randint(0, self.rows-1)
            c = random.randint(0, self.cols-1)
            self.mine_coords.add((r, c))

    def calculate_numbers(self):
        """计算每个格子的数字"""
        self.numbers = {}
        for r in range(self.rows):
            for c in range(self.cols):
                if (r, c) in self.mine_coords:
                    continue
                count = 0
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if (r+dr, c+dc) in self.mine_coords:
                            count += 1
                self.numbers[(r, c)] = count

    def _ensure_first_click_empty(self, r, c):
        """确保在第一次点击 (r,c) 时该格及其 8 个邻格没有地雷。
        通过从这些格子中移除地雷并在其他合法格子补回相同数量的雷来保持总雷数不变。
        在极端情况下（雷过多）此函数会跳过修改。
        """
        # 确定禁止放雷的格子（中心及其周围 3x3）
        forbidden = set()
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    forbidden.add((nr, nc))

        # 移除 forbidden 区域内的雷并记录被移除的数量
        removed = 0
        for coord in list(self.mine_coords):
            if coord in forbidden:
                self.mine_coords.remove(coord)
                removed += 1

        # 将移除的雷在其他可用格子中随机补回，避免放到 forbidden 或已存在雷的格子
        available = [ (rr,cc) for rr in range(self.rows) for cc in range(self.cols)
                      if (rr,cc) not in self.mine_coords and (rr,cc) not in forbidden ]
        # 如果可用格子不足，退回：把移除的雷放回并放弃确保
        if len(available) < removed:
            # 回填回原始（把刚刚移除的坐标重新加入）
            for coord in list(forbidden):
                if coord not in self.mine_coords and len(self.mine_coords) < self.mines:
                    self.mine_coords.add(coord)
            return

        # 随机选择位置补雷
        if removed > 0:
            new_positions = random.sample(available, removed)
            for pos in new_positions:
                self.mine_coords.add(pos)

        # 重新计算数字字典
        self.calculate_numbers()

    
        

    def game_over(self):
        """游戏失败处理"""
        for r, c in self.mine_coords:
            self.canvas.delete(self.image_map[r][c])
            self.image_map[r][c]=self.canvas.create_image((c+0.5)*self.size, (r+0.5)*self.size, image=self.mine_imgs[1])
        # 不弹窗也不自动重置，直接切换重启图标为失败并禁用操作
        try:
            self.set_restart_icon('fail')
        except Exception:
            pass
        # 标记游戏已结束，禁用后续切换到普通图标
        self.finished = True
        self.canvas.unbind("<ButtonPress-1>")
        self.canvas.unbind("<ButtonRelease-1>")
        self.canvas.unbind("<ButtonPress-3>")
        self.canvas.unbind("<ButtonRelease-3>")
        # 若设置了失败自动重开，则在短延迟后重开（800ms），以便玩家看到失败反馈
        try:
            if getattr(self, 'auto_restart_on_fail_var', None) and self.auto_restart_on_fail_var.get():
                try:
                    self.root.after(800, self.restart)
                except Exception:
                    # 回退到立即重开
                    self.restart()
        except Exception:
            pass

    def check_win(self):
        """检查胜利条件"""
        # 所有非雷格子都被翻开
        if self.mode in ("tradition", "find_mine"):
            non_mines = self.rows * self.cols - self.mines
            if len(self.revealed) == non_mines:
                # 胜利：切换重启图标为 success，禁用输入，不自动重启
                try:
                    self.set_restart_icon('success')
                except Exception:
                    pass
                # 标记游戏已结束
                self.finished = True
                self.canvas.unbind("<ButtonPress-1>")
                self.canvas.unbind("<ButtonRelease-1>")
                self.canvas.unbind("<ButtonPress-3>")
                self.canvas.unbind("<ButtonRelease-3>")
                # 若设置了胜利自动重开，则在短延迟后重开（800ms），以便玩家看到胜利反馈
                try:
                    if getattr(self, 'auto_restart_on_win_var', None) and self.auto_restart_on_win_var.get():
                        try:
                            self.root.after(800, self.restart)
                        except Exception:
                            self.restart()
                except Exception:
                    pass
        if self.mode =='exercise1':
            finish=True
            for c in range(30):
                if (2,c) in self.revealed:
                    pass
                elif (2,c) in self.mine_coords:
                    pass
                else:
                    finish=False
                    break
            if finish:
                self.restart()
        if self.mode =='exercise2':
            finish=True
            for c in range(3):
                if (3,c) in self.revealed:
                    pass
                elif (3,c) in self.mine_coords:
                    pass
                else:
                    finish=False
                    break
            if finish:
                self.restart()

        
    

if __name__ == "__main__":
    root = tk.Tk()
    root.title("简易扫雷")
    game = Minesweeper(master=root)
    root.mainloop()
    
# 


