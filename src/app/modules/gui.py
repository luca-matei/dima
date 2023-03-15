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
        """
        root
            main
                body
                    command
                    hosts
                    webs
                status
        """
        self.create_obj("frame", "root", name="main", fill="both", expand=True, padx=16, pady=16)
        self.create_obj("frame", "main", name="body", fill="both", expand=True)
        self.create_obj("frame", "body", name="command", fill="x")
        self.create_obj("frame", "body", name="hosts", fill="x", pady=8)
        self.create_obj("frame", "main", name="status", fill="x")

        # Command input
        self.create_obj("label", "command", text="Command:", side="left", ipady=2)
        self.history_index = 0
        self.command = tk.StringVar()
        self.cmd_input = self.create_obj("input", "command", str_store=self.command, anchor="NW", side="left", padx=4, ipadx=8, ipady=2)
        self.cmd_input.bind('<Return>', self.send_command)
        self.cmd_input.bind('<Up>', self.history_up)
        self.cmd_input.bind('<Down>', self.history_down)
        self.cmd_input.focus()

        # Hosts panel
        self.create_obj("label", "hosts", text="Hosts", font=("Arial", 12), fill="x", pady=8)
        hosts = [x[0] for x in hal.db.execute("select lmid from lmobjs where module=(select id from modules where name='Host');")]

        self.host_acts = {
            "nginx": ("config", "reload", "start", "stop", "restart"),
            "hosts_file": ("update",),
        }
        xyz = hal.db.execute("select name, acts from command.objs where module=(select id from modules where name='Host');")
        print(xyz)
        self.host_acts = {x[0] if x[0] != None else '': [cli.acts[y] for y in x[1]] for x in xyz}
        print(self.host_acts)

        self.host_opt = tk.StringVar()
        self.obj_opt = tk.StringVar()
        self.act_opt = tk.StringVar()

        self.create_obj("option_menu", "hosts", str_store=self.host_opt, opts=hosts, side="left")
        self.create_obj("option_menu", "hosts", str_store=self.obj_opt,
            opts = sorted(utils.get_keys(self.host_acts)),
            command = self.change_acts,
            side = "left")

        self.acts_menu = self.create_obj("option_menu", "hosts", str_store=self.act_opt,
            opts = self.host_acts[sorted(utils.get_keys(self.host_acts))[0]],
            side = "left")

        self.create_obj("btn", "hosts", text="Process", command=self.send_host_cmd)

        # Status section
        self.create_obj("btn", "status", text="Quit", command=self.quit, anchor="SE")


    def history_up(self, event):
        self.history_index -= 1
        if abs(self.history_index) <= len(cli.history):
            self.command.set(cli.history[self.history_index])
            self.cmd_input.icursor("end")
        else:
            self.history_index += 1

    def history_down(self, event):
        self.history_index += 1
        if self.history_index < 0:
            self.command.set(cli.history[self.history_index])
            self.cmd_input.icursor("end")
        elif self.history_index == 0:
            self.command.set("")
        else:
            self.history_index -= 1

    def send_command(self, event):
        cli.process(self.command.get())
        self.command.set("")
        self.history_index = 0

    def send_host_cmd(self):
        print(self.host_opt.get() + " " + self.act_opt.get() + " " + self.obj_opt.get())

    ## WIDGET UTILS ##

    def create_obj(self, obj, frame, anchor=None, expand=False, fill=None, side=None, padx=0, pady=0, ipadx=0, ipady=0, **kwargs):
        if frame == "root": frame_obj = self.root
        else: frame_obj = self.frames[frame]

        obj = getattr(self, "create_" + obj)(frame_obj, **kwargs)

        if anchor: anchor = getattr(tk, anchor.upper())
        if side: side = getattr(tk, side.upper())
        if fill: fill = getattr(tk, fill.upper())

        obj.pack(anchor=anchor, expand=expand, fill=fill, side=side, padx=padx, pady=pady, ipadx=ipadx, ipady=ipady)

        return obj

    def change_acts(self, event):
        self.acts_menu['menu'].delete(0, tk.END)
        opts = sorted(self.host_acts[self.obj_opt.get()])
        self.act_opt.set(opts[0])
        for opt in opts:
            self.acts_menu['menu'].add_command(label=opt, command=tk._setit(self.act_opt, opt))


    ## WIDGETS ##

    def create_label(self, frame, text="Label", font=()):
        label = ttk.Label(frame, text=text, font=font)
        return label

    def create_input(self, frame, str_store=None):
        field = ttk.Entry(frame, textvariable=str_store)
        return field

    def create_btn(self, frame, text="Button", command=None):
        btn = ttk.Button(frame, text=text, command=command)
        return btn

    def create_option_menu(self, frame, str_store, opts, command=None):
        option_menu = ttk.OptionMenu(frame, str_store, opts[0], *opts, command=command)
        return option_menu

    ## FRAMES ##

    def create_frame(self, frame, name):
        self.frames[name] = ttk.Frame(frame)
        return self.frames[name]

    def start(self):
        self.root.mainloop()

    def quit(self):
        self.root.destroy()
