class GUI:
    def __init__(self):
        self.root = tk.Tk()
        self.style = ttk.Style(self.root)
        self.frames = {}

        # Window geometry
        self.w_width = 600
        self.w_height = 400

        self.screen_width = 1920    # w.winfo_screenwidth()
        self.screen_height = 1080    # w.winfo_screenheight()

        self.center_x = int(self.screen_width / 2 - self.w_width / 2)
        self.center_y = int(self.screen_height / 2 - self.w_height / 2)

        # Window properties
        self.root.title("DIMA")
        self.root.resizable(True, True)
        self.root.geometry(f'{self.w_width}x{self.w_height}+{self.center_x}+{self.center_y}')
        self.root.minsize(self.w_width, self.w_height)
        self.root.maxsize(self.screen_width, self.screen_height)
        # self.w.iconbitmap('./assets/favicon.ico')

        # Style
        self.style.theme_use("clam")

        # Structure
        self.create_page("main")
        self.create_frame("main", "body", expand=True)
        self.create_frame("main", "status")

        # Command input
        self.create_obj("label", "body", text="Command:", anchor="NW", side="left", ipady=2)
        self.history_index = 0
        self.command = tk.StringVar()
        cmd_input = self.create_obj("input", "body", value=self.command, anchor="NW", side="left", padx=4, ipadx=8, ipady=2)
        cmd_input.bind('<Return>', self.send_command)
        cmd_input.bind('<Up>', self.history_up)
        cmd_input.bind('<Down>', self.history_down)
        cmd_input.focus()

        # Status section
        self.create_obj("btn", "status", text="Quit", command=self.quit, anchor="SE")
        print(cli.history)


    def history_up(self, event):
        self.history_index -= 1
        if abs(self.history_index) <= len(cli.history):
            self.command.set(cli.history[self.history_index])
        else:
            self.history_index += 1

        print(self.history_index, cli.history[self.history_index])

    def history_down(self, event):
        self.history_index += 1
        if self.history_index < 0:
            self.command.set(cli.history(self.history_index))
        elif self.history_index == 0:
            self.command.set("")
        else:
            self.history_index -= 1

        print(self.history_index, cli.history[self.history_index])

    def send_command(self, event):
        cli.process(self.command.get())
        self.command.set("")
        self.history_index = 0

    ## WIDGET UTILS ##

    def pack(self, obj, anchor, expand, side, padx, pady, ipadx, ipady):
        if anchor: anchor = getattr(tk, anchor.upper())
        if side: side = getattr(tk, side.upper())
        obj.pack(anchor=anchor, expand=expand, side=side, padx=padx, pady=pady, ipadx=ipadx, ipady=ipady)

    def create_obj(self, obj, frame, anchor=None, expand=False, side=None, padx=0, pady=0, ipadx=0, ipady=0, **kwargs):
        obj = getattr(self, "create_" + obj)(self.frames[frame], **kwargs)
        self.pack(obj, anchor, expand, side, padx, pady, ipadx, ipady)
        return obj

    ## WIDGETS ##

    def create_label(self, frame, text="Label"):
        label = ttk.Label(frame, text=text)
        return label

    def create_input(self, frame, value=None):
        field = ttk.Entry(frame, textvariable=value)
        return field

    def create_btn(self, frame, text="Button", command=None):
        btn = ttk.Button(frame, text=text, command=command)
        return btn

    ## FRAMES ##

    def create_page(self, name):
        self.frames[name] = ttk.Frame(self.root, borderwidth=1)
        self.frames[name].pack(fill=tk.BOTH, padx=16, pady=16, expand=True)

    def create_frame(self, page, name, expand=False):
        self.frames[name] = ttk.Frame(self.frames[page], borderwidth=1)
        self.frames[name].pack(fill=tk.BOTH, expand=expand)

    def start(self):
        self.root.mainloop()

    def quit(self):
        self.root.destroy()
