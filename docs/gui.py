class GUI:
    colors = {
        "blue": "#0000FF",
        "green": "#008000",
        "yellow": "#FFFF00",
        "lred": "#FF3333",
        "red": "#FF0000",
        }

    def __init__(self):
        self.root = tk.Tk()
        self.style = ttk.Style(self.root)
        self.frames = {}
        self.widgets = {}
        self.panel_acts = {}
        self.last_timer = None

        # Window geometry
        self.w_width = 800
        self.w_height = 600

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
        self.build_interface()

    def build_interface(self):
        def structure():
            """
            root
                main
                --- dashboard
                        command
                --- hosts
                        panel
                --- webs
                        panel
                status
            """
            self.create_obj("frame", "root",
                name = "main",
                notebook = True,
                fill="both", expand=True, padx=16, pady=16
                )

            self.create_obj("page", "main",
                name = "dashboard",
                title = "Dashboard",
                fill="both", expand=True
                )

            self.create_obj("page", "main",
                name = "hosts",
                title = "Hosts",
                fill="both", expand=True
                )

            self.create_obj("page", "main",
                name = "webs",
                title = "Webs",
                fill="both", expand=True
                )

            self.create_obj("page", "main",
                name = "console",
                title = "Console",
                fill="both", expand=True
                )

            self.create_obj("frame", "root",
                name="status",
                fill="x", pady=16, padx=16
                )

        def manual_cmd():
            self.history_index = 0
            self.create_obj("frame", "dashboard",
                name="manual_cmd",
                fill="x", pady=16)

            self.create_obj("label", "manual_cmd",
                text="Manual Command",
                fill="x", anchor="NW")

            self.widgets["cmd_str"] = tk.StringVar()
            self.widgets["cmd_input"] = self.create_obj("input", "manual_cmd",
                str_store = self.widgets["cmd_str"],
                anchor = "NW", side="left", pady=8, ipadx=8, ipady=2
                )

            self.widgets["cmd_input"].bind('<Return>', lambda event: self.send_command("manual"))
            self.widgets["cmd_input"].bind('<Up>', self.history_up)
            self.widgets["cmd_input"].bind('<Down>', self.history_down)
            self.widgets["cmd_input"].focus()

        def panel(name):
            self.create_obj("frame", name + "s",
                name = name + "_details",
                fill="both", pady=12
                )

            self.create_obj("frame", name + "s", name=name, fill="x", pady=12)
            self.create_obj("label", name,
                text="Command",
                fill="x", anchor="NW", pady=4)
            lmids = [x[0] for x in hal.db.execute(f"select lmid from lmobjs where module=(select id from modules where name='{name.capitalize()}');")]

            acts = hal.db.execute(f"select name, acts from command.objs where module=(select id from modules where name='{name.capitalize()}');")
            self.panel_acts[name] = {x[0] if x[0] != None else '': [cli.acts[y] for y in x[1]] for x in acts}

            self.widgets[f"{name}_lmid"] = tk.StringVar()
            self.widgets[f"{name}_obj"] = tk.StringVar()
            self.widgets[f"{name}_act"] = tk.StringVar()

            self.create_obj("option_menu", name,
                str_store = self.widgets[f"{name}_lmid"],
                opts = lmids,
                command = lambda event: self.set_details(name),
                side = "left", pady=4
                )

            self.create_obj("option_menu", name,
                str_store = self.widgets[f"{name}_obj"],
                opts = sorted(utils.get_keys(self.panel_acts[name])),
                command = lambda event: self.change_acts(name),
                side = "left", pady=4
                )

            self.widgets[f"{name}_acts"] = self.create_obj("option_menu", name,
                str_store = self.widgets[f"{name}_act"],
                opts = self.panel_acts[name][sorted(utils.get_keys(self.panel_acts[name]))[0]],
                side = "left", pady=4
                )

            self.create_obj("btn", name,
                text="Process",
                command = lambda: self.send_command(name),
                side = "left", padx=16, pady=4
                )

        def status():
            self.widgets["status_lvl_str"] = self.create_obj("str", "status")
            self.widgets["status_str"] = self.create_obj("str", "status")
            self.widgets["status_lvl"] = self.create_obj("label", "status",
                textvariable = self.widgets["status_lvl_str"],
                ipadx = 4, side = "left", anchor="SW"
                )
            self.create_obj("label", "status",
                textvariable=self.widgets["status_str"],
                ipadx = 4, side = "left", anchor="SW"
                )
            self.create_obj("btn", "status", text="Quit", command=self.quit, anchor="SE")

        structure()
        manual_cmd()
        for p in ("host", "web"):
            panel(p)
            self.set_details(p)
        status()


    ## HISTORY

    def history_up(self, event):
        self.history_index -= 1
        if abs(self.history_index) <= len(cli.history):
            self.widgets["cmd_str"].set(cli.history[self.history_index])
            self.widgets["cmd_input"].icursor("end")
        else:
            self.history_index += 1

    def history_down(self, event):
        self.history_index += 1
        if self.history_index < 0:
            self.widgets["cmd_str"].set(cli.history[self.history_index])
            self.widgets["cmd_input"].icursor("end")
        elif self.history_index == 0:
            self.widgets["cmd_str"].set("")
        else:
            self.history_index -= 1

    ## WIDGET UTILS ##

    def create_obj(self, obj_name, frame, anchor=None, expand=False, fill=None, side=None, padx=0, pady=0, ipadx=0, ipady=0, **kwargs):
        if frame == "root": frame_obj = self.root
        else: frame_obj = self.frames[frame]

        obj = getattr(self, "create_" + obj_name)(frame_obj, **kwargs)

        if obj_name not in ("str",):
            if anchor: anchor = getattr(tk, anchor.upper())
            if side: side = getattr(tk, side.upper())
            if fill: fill = getattr(tk, fill.upper())

            obj.pack(anchor=anchor, expand=expand, fill=fill, side=side, padx=padx, pady=pady, ipadx=ipadx, ipady=ipady)

            if obj_name == "page":
                frame_obj.add(self.frames[kwargs["name"] + "_page"], text=kwargs["title"])
                self.create_obj("frame", kwargs["name"] + "_page",
                    name = kwargs["name"],
                    fill = "both", expand=True, padx=16
                    )

        return obj

    def change_acts(self, t):
        self.widgets[t + "_acts"]['menu'].delete(0, tk.END)

        opts = sorted(self.panel_acts[t][self.widgets[t + "_obj"].get()])
        self.widgets[t + "_act"].set(opts[0])

        for opt in opts:
            self.widgets[t + "_acts"]['menu'].add_command(
                label = opt,
                command = tk._setit(self.widgets[t + "_act"], opt))

    def set_details(self, t):
        lmid = self.widgets[t + "_lmid"].get()
        pool = hal.pools[hal.lmobjs[lmid]]

        if t == "host":
            detail_titles = {
                "net_id": "Network",
                "mac": "MAC Address",
                "ip": "IP Address",
                "env": "Environment",
                "ssh_port": "SSH Port",
                "pg_port": "PostgreSQL Port",
                "pm_id": "Physical Machine"
                }

            self.create_obj("frame", t + "_details",
                name =  t+"_details_half1",
                fill = "both", expand = True
                )

            self.create_obj("frame", t + "_details",
                name =  t+"_details_half2",
                fill = "both", expand = True
                )

            for d in ("net_id", "mac", "ip", "env", "ssh_port", "pg_port", "pm_id"):
                detail_widget_name = "lm"+t+d
                detail_widget = self.create_obj("frame", t + "_details_half1",
                    name = detail_widget_name,
                    pady = 4, fill = "x", expand=True
                    )

                self.create_obj("label", detail_widget_name,
                    text = detail_titles[d],
                    fill = "both", side="left"
                    )

                self.create_obj("label", detail_widget_name,
                    text = hal.lmobjs.get(getattr(pool, d), [None])[0] if d in ("net_id", "pm_id") else getattr(pool, d),
                    side = "right"
                    )

        elif t == "web":
            pass

    def send_command(self, t):
        if t == "manual":
            cli.process(self.widgets["cmd_str"].get())
            self.widgets["cmd_str"].set("")
            self.history_index = 0

        elif t in ("host", "web"):
            name = self.widgets[t + "_lmid"].get()
            act = self.widgets[t + "_act"].get()
            obj = self.widgets[t + "_obj"].get()

            if obj:
                cli.process(' '.join([name, act, obj]))
            else:
                cli.process(' '.join([name, act]))

    def reset_status(self):
        if self.last_timer + timedelta(seconds=10) <= datetime.now():
            self.widgets["status_lvl_str"].set("")
            self.widgets["status_str"].set("")

    def set_status(self, level, color, message):
        self.widgets["status_lvl_str"].set(level)
        self.widgets["status_lvl"].config(foreground = self.colors[color])
        self.widgets["status_str"].set(message)

        if not message.endswith("..."):
            self.widgets["status_lvl"].after(10000, self.reset_status)
            self.last_timer = datetime.now()

    ## WIDGETS ##

    def create_str(self, frame):
        return tk.StringVar(frame)

    def create_label(self, frame, text="Label", textvariable=None, font=()):
        return ttk.Label(frame, text=text, textvariable=textvariable, font=font)

    def create_input(self, frame, str_store=None):
        return ttk.Entry(frame, textvariable=str_store)

    def create_btn(self, frame, text="Button", command=None):
        return ttk.Button(frame, text=text, command=command)

    def create_option_menu(self, frame, str_store, opts, command=None):
        return ttk.OptionMenu(frame, str_store, opts[0], *opts, command=command)

    ## FRAMES ##

    def create_page(self, frame, name, title):
        self.frames[name + "_page"] = ttk.Frame(self.frames["main"])
        return self.frames[name + "_page"]

    def create_frame(self, frame, name, notebook=False, width=None, height=None):
        if notebook:
            self.frames[name] = ttk.Notebook(frame)
        else:
            self.frames[name] = ttk.Frame(frame)
        return self.frames[name]

    def start(self):
        self.root.mainloop()

    def quit(self):
        self.root.destroy()

gui = None
