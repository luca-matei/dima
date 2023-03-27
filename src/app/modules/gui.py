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
        self.widgets = {}
        self.lmids = {}
        self.panel_acts = {}
        self.last_timer = None
        self.history_index = 0

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

        for p in ("host", "web"):
            self.lmids[p] = hal.db.execute(f"select lmid, alias from lmobjs where module=(select id from modules where name='{p.capitalize()}');")

            acts = hal.db.execute(f"select name, acts from command.objs where module=(select id from modules where name='{p.capitalize()}');")

            self.panel_acts[p] = self.panel_acts[p] = {x[0] if x[0] != None else '': [cli.acts[y] for y in x[1]] for x in acts}

        self.build_interface()
        self.set_dropdown(f"host_lmid_menu")
        self.set_dropdown(f"host_obj_menu")


    ## INTERFACE

    def create_notebook(self, frame, **kwargs):
        return ttk.Notebook(frame)

    def create_dropdown(self, frame, text_var=None, opts=[''], command=None, **kwargs):
        text_obj = self.widgets.get(text_var)
        menu = ttk.OptionMenu(frame, text_obj, opts[0], *opts, command = command)

        return menu

    def create_text_var(self, frame, name='', value='', **kwargs):
        string_var = tk.StringVar(frame)
        self.widgets[name] = string_var
        string_var.set(value)
        return string_var

    def create_label(self, frame, text="Label", text_var=None, font=(), **kwargs):
        text_obj = self.widgets.get(text_var)
        return ttk.Label(frame, text=text, textvariable=text_obj, font=font)

    def create_input(self, frame, text_var=None, **kwargs):
        text_obj = self.widgets.get(text_var)
        return ttk.Entry(frame, textvariable=text_obj)

    def create_button(self, frame, text="Button", command=None, **kwargs):
        return ttk.Button(frame, text=text, command=command)

    def create_frame(self, frame, bg=None, **kwargs):
        style = ttk.Style()
        style.configure(f"{bg}.TFrame", background = bg)
        return ttk.Frame(frame, style=f"{bg}.TFrame")

    def build_interface(self):
        widget_names = "notebook", "frame", "label", "button", "dropdown", "input",
        pack_properties = "padx", "pady", "ipadx", "ipady", "fill", "expand", "anchor", "side",

        gui_yml = yaml.YAML(typ="safe").load(utils.read(utils.src_dir + "app/gui.yml"))

        def solve_widget(parent_frame, data):
            w_type = data[0]
            obj = None
            pack = {}
            props = {}
            to_solve = []

            for prop in data[1]:
                if prop[0] in widget_names:
                    to_solve.append(prop)

                elif prop[0] in pack_properties:
                    value = prop[1]

                    if prop[0] in ("fill", "side", "anchor"): value = getattr(tk, prop[1].upper())

                    pack[prop[0]] = value

                elif prop[0] == "command":
                    props["command"] = getattr(self, prop[1])

                elif prop[0] == "text_var":
                    text_props = dict(prop[1])
                    props["text_var"] = text_props.get("id")
                    text_obj = getattr(self, "create_text_var")(
                        parent_frame,
                        name = text_props.get("id", ""),
                        value = text_props.get("value", "")
                        )

                    if text_props.get("trace"):
                        text_obj.trace("w", getattr(self, text_props["trace"]))

                else:
                    props[prop[0]] = prop[1]

            # Create Widget
            obj = getattr(self, "create_" + w_type)(parent_frame, **props)
            if props.get("id"): self.widgets[props["id"]] = obj

            # Display widget
            obj.pack(**pack)

            # Try because it can be root
            try:
                # Add page to screen
                if parent_frame.widgetName == "ttk::notebook":
                    parent_frame.add(obj, text=props["title"])

            except Exception as e:
                print(e)

            # Bind keypresses
            if props.get("bind"):
                for b in props["bind"]:
                    obj.bind(f"<{b[0]}>", getattr(self, b[1]))

            # Focus inputs
            if props.get("focus"):
                obj.focus()

            for w_data in to_solve:
                solve_widget(obj, w_data)

        for w_data in gui_yml:
            solve_widget(self.root, w_data)


    ## DASHBOARD

    def send_mcmd(self, *args):
        cli.process(self.widgets["mcmd_input_str"].get())
        self.widgets["mcmd_input_str"].set("")
        self.history_index = 0


    ## HOSTS

    def set_host_details(self, *args):
        lmid = self.widgets["host_lmid_str"].get()
        if lmid:
            pool = hal.pools[hal.lmobjs[lmid]]
        else:
            pool = hal.pools[hal.host_dbid]

        self.widgets["host_id_str"].set(pool.lmid)
        self.widgets["host_net_str"].set(hal.lmobjs[pool.net_id][0])
        self.widgets["host_mac_str"].set(pool.mac.upper())
        self.widgets["host_ip_str"].set(pool.ip)
        self.widgets["host_env_str"].set(pool.env)
        self.widgets["host_alias_str"].set(pool.alias if pool.alias else "NaN")
        self.widgets["host_ssh_str"].set(pool.ssh_port if pool.ssh_port != -1 else "NaN")
        self.widgets["host_pg_str"].set(pool.pg_port if pool.pg_port != -1 else "NaN")
        self.widgets["host_pm_str"].set(hal.lmobjs.get(pool.pm_id, ["NaN"])[0])

    def send_host_cmd(self, *args):
        name = self.widgets["host_lmid_str"].get()
        act = self.widgets["host_act_str"].get()
        obj = self.widgets["host_obj_str"].get()

        if obj:
            cli.process(' '.join([name, act, obj]))
        else:
            cli.process(' '.join([name, act]))

    # Dropdowns
    def set_dropdown(self, drop_name):
        self.widgets[drop_name]['menu'].delete(0, tk.END)

        if drop_name == "host_lmid_menu":
            opts = sorted([x[0] for x in self.lmids["host"]])
            #opts = sorted([x[0] + (f" ({x[1]})" if x[1] else '') for x in self.lmids["host"]])
        elif drop_name == "host_obj_menu":
            opts = sorted(utils.get_keys(self.panel_acts["host"]))
        elif drop_name == "host_act_menu":
            opts = sorted(
                self.panel_acts["host"][self.widgets["host_obj_str"].get()])

        drop_var = drop_name[:-4] + "str"
        self.widgets[drop_var].set(opts[0])

        for opt in opts:
            self.widgets[drop_name]["menu"].add_command(
                label = opt,
                command = tk._setit(self.widgets[drop_var], opt)
                )

        if len(opts) == 1:
            self.widgets[drop_name].configure(state="disabled")
        else:
            self.widgets[drop_name].configure(state="normal")

    def set_host_lmids(self, *args):
        self.set_dropdown("host_lmid_menu")

    def set_host_objs(self, *args):
        self.set_dropdown("host_obj_menu")

    def set_host_acts(self, *args):
        self.set_dropdown("host_act_menu")

    def set_host_args(self, *args):
        pass


    ## HISTORY

    def history_up(self, event):
        self.history_index -= 1
        if abs(self.history_index) <= len(cli.history):
            self.widgets["mcmd_input_str"].set(cli.history[self.history_index])
            self.widgets["mcmd_input"].icursor("end")
        else:
            self.history_index += 1

    def history_down(self, event):
        self.history_index += 1
        if self.history_index < 0:
            self.widgets["mcmd_input_str"].set(cli.history[self.history_index])
            self.widgets["mcmd_input"].icursor("end")
        elif self.history_index == 0:
            self.widgets["mcmd_input_str"].set("")
        else:
            self.history_index -= 1


    # STATUS

    def reset_status(self):
        if self.last_timer + timedelta(seconds=10) <= datetime.now():
            self.widgets["status_lvl_str"].set("")
            self.widgets["status_msg_str"].set("")

    def set_status(self, level, color, message):
        self.widgets["status_lvl_str"].set(level)
        self.widgets["status_lvl"].config(foreground = self.colors[color])
        self.widgets["status_msg_str"].set(message)

        if not message.endswith("..."):
            self.widgets["status_lvl"].after(10000, self.reset_status)
            self.last_timer = datetime.now()


    # MAIN

    def start(self):
        self.root.mainloop()

    def quit(self):
        self.root.destroy()

gui = None
