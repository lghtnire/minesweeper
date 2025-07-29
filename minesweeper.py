import tkinter as tk
from tkinter import messagebox
import random
from PIL import Image,ImageTk

class Minesweeper:
    def __init__(self, master, sizes=(8,8), mines=10,size=20):
        self.root = master
        self.rows = sizes[0]
        self.cols = sizes[1]
        self.mines = mines
        self.size=size
        self.mode="tradition"
        #录入图片
        imgs0 = [Image.open(f'images/type{i}.jpg').resize((self.size,self.size)) for i in range(9)]
        imgs1 = [Image.open(f'images/mine{i}.jpg').resize((self.size,self.size)) for i in range(4)]
        self.type_imgs = [ImageTk.PhotoImage(img) for img in imgs0]
        self.mine_imgs = [ImageTk.PhotoImage(img) for img in imgs1]
        
        # 初始化界面
        self.menu()
        h=self.rows*self.size
        w=self.cols*self.size
        self.canvas=tk.Canvas(self.root,height=h,width=w)
        self.new_game((8,8),10)

    def create_widgets(self):
        """创建游戏界面"""
        self.canvas.delete("all")
        h=self.rows*self.size
        w=self.cols*self.size
        self.canvas.config(height=h,width=w)
        self.image_map = [[None]*self.cols for i in range(self.rows)]
        for row in range(self.rows): 
            for col in range(self.cols): 
                x = (col+1/2) * self.size  # 计算x坐标
                y = (row+1/2) * self.size  # 计算y坐标
                self.image_map[row][col]=self.canvas.create_image(x, y, image=self.mine_imgs[-1])
        self.canvas.bind("<Button-1>", lambda e: self.reveal(e.y//self.size,e.x//self.size))
        self.canvas.bind("<Button-3>", lambda e: self.mark_mine(e.y//self.size,e.x//self.size))
        self.canvas.pack()
        
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

    def restart(self):
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
        
        if (r, c) in self.mine_coords:
            self.game_over()
            return
        
        if r>self.rows-1 or c>self.cols-1:
            return
        
        self.revealed.add((r, c))
        num = self.numbers.get((r, c), 0)
        self.canvas.delete(self.image_map[r][c])
        x1,y1=(c+0.5)*20,(r+0.5)*20
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

    def mark_mine(self,r,c):
        """右键标记地雷"""
        x1,y1=(c+0.5)*20,(r+0.5)*20
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

    
        

    def game_over(self):
        """游戏失败处理"""
        for r, c in self.mine_coords:
            self.canvas.delete(self.image_map[r][c])
            self.image_map[r][c]=self.canvas.create_image((c+0.5)*self.size, (r+0.5)*self.size, image=self.mine_imgs[1])
        tk.messagebox.showinfo("游戏结束", "你踩到地雷了！")
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<Button-3>")

    def check_win(self):
        """检查胜利条件"""
        # 所有非雷格子都被翻开
        if self.mode == "tradition" or "find_mine":
            non_mines = self.rows * self.cols - self.mines
            if len(self.revealed) == non_mines:
    #            tk.messagebox.showinfo("胜利", "恭喜你扫雷成功！")
                self.canvas.unbind("<Button-1>")
                self.canvas.unbind("<Button-3>")
                self.restart()
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


