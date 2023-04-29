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
        self.cmd_args = {}
        self.arg_widgets = {}
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
            self.lmids[p] = dima.db.execute(f"select lmid, alias from lmobjs where module=(select id from modules where name='{p.capitalize()}');")

            acts = dima.db.execute(f"select name, acts from command.objs where module=(select id from modules where name='{p.capitalize()}');")

            self.panel_acts[p] = self.panel_acts[p] = {x[0] if x[0] != None else '': [cli.acts[y] for y in x[1]] for x in acts}

        self.build_interface()
        for m in ("host", "web"):
            self.set_dropdown(f"{m}_lmid_menu")
            self.set_dropdown(f"{m}_obj_menu")


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

    def set_dropdown(self, drop_name):
        self.widgets[drop_name]['menu'].delete(0, tk.END)
        module = drop_name.split("_")[0]

        if "lmid" in drop_name:
            opts = [x[0] for x in self.lmids[module]]
            #opts = [x[0] + (f" ({x[1]})" if x[1] else '') for x in self.lmids["host"]]
        elif "obj" in drop_name:
            opts = utils.get_keys(self.panel_acts[module])
        elif "act" in drop_name:
            opts = self.panel_acts[module][self.widgets[module + "_obj_str"].get()]

        opts = sorted(opts)

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

    def set_args(self, module):
        self.cmd_args = {}
        lmid = self.widgets[module + "_lmid_str"].get()
        obj = self.widgets[module + "_obj_str"].get()
        act = self.widgets[module + "_act_str"].get()

        if obj: method = getattr(dima.pools[dima.lmobjs[lmid]], act + '_' + obj)
        else: method = getattr(dima.pools[dima.lmobjs[lmid]], act)

        param_pos, params = utils.get_method_params(method)
        frame = module + "_args_panel_tmp"

        self.widgets[frame].destroy()
        self.widgets[frame] = self.create_frame(self.widgets[module + "_args_panel"])
        self.widgets[frame].pack(fill=tk.X, expand=True)

        frame = self.widgets[frame]

        widgets = {}
        for p, v in params.items():
            self.cmd_args[p] = "NaN"
            text = p.capitalize().replace("_", " ") + (" *" if p in param_pos else "")

            for x in ("html", "css", "php"):
                if x in text:
                    text = text.replace(x, x.upper())

            label = self.create_label(frame, text=text)
            label.pack(side=tk.LEFT, padx=[0, 4])

            if v[0] == "str":
                widgets[p + "_var"] = tk.StringVar(frame)
                widgets[p] = ttk.Entry(frame, textvariable = widgets[p + "_var"])

                if v[1] and v[1] != inspect._empty:
                    widgets[p + "_var"].set(v[1])

            elif v[0] == "bool":
                widgets[p + "_var"] = tk.IntVar(frame)
                widgets[p] = ttk.Checkbutton(frame, variable=widgets[p + "_var"])

            elif v[0] == "env":
                widgets[p + "_var"] = tk.StringVar(frame)
                opts = [k for k, v in utils.hosts.envs.items() if isinstance(k, str)]
                widgets[p] = ttk.OptionMenu(frame, widgets[p + "_var"], v[1], *opts)

            elif v[0] == "web_state":
                widgets[p + "_var"] = tk.StringVar(frame)
                opts = [s[1] for s in sorted(utils.webs.states.items(), key = lambda e: e[0])]
                current_state = utils.webs.states.get(dima.pools.get(dima.lmobjs.get(lmid)).prod_state)
                widgets[p] = ttk.OptionMenu(frame, widgets[p + "_var"], current_state, *opts)

            widgets[p].pack(side=tk.LEFT, padx=[0, 8])

        self.arg_widgets = widgets

    def send_cmd(self, module):
        name = self.widgets[f"{module}_lmid_str"].get()
        act = self.widgets[f"{module}_act_str"].get()
        obj = self.widgets[f"{module}_obj_str"].get()
        args = []

        for arg in self.cmd_args:
            value = self.arg_widgets[arg + "_var"].get()
            if value:
                if " " in str(value): value = '"' + value + '"'
                if arg == "new_state" and module == "web":
                    args.append(f"--new_state={utils.reverse_dict(utils.webs.states)[value]}")
                else:
                    args.append(f"--{arg}={value}")
            else:
                print(value)

        args = ' '.join(args)

        if obj:
            command = ' '.join([name, act, obj, args])
            cli.process(command)
        else:
            command = ' '.join([name, act, args])
            cli.process(command)

        print(command)

    ## HOSTS

    def set_host_details(self, *args):
        lmid = self.widgets["host_lmid_str"].get()
        if lmid:
            pool = dima.pools[dima.lmobjs[lmid]]
        else:
            pool = dima.pools[dima.host_dbid]

        self.widgets["host_id_str"].set(pool.lmid)
        self.widgets["host_net_str"].set(dima.lmobjs.get(pool.net_id, ["NaN"])[0])
        self.widgets["host_mac_str"].set(pool.mac.upper())
        self.widgets["host_ip_str"].set(pool.ip)
        self.widgets["host_env_str"].set(pool.env)

        self.widgets["host_alias_str"].set(pool.alias if pool.alias else "NaN")
        self.widgets["host_ssh_str"].set(pool.ssh_port if pool.ssh_port != -1 else "NaN")
        self.widgets["host_pg_str"].set(pool.pg_port if pool.pg_port != -1 else "NaN")
        self.widgets["host_pm_str"].set(dima.lmobjs.get(pool.pm_id, ["NaN"])[0])

    def send_host_cmd(self, *args):
        self.send_cmd("host")

    # Dropdowns
    def set_host_lmids(self, *args):
        self.set_dropdown("host_lmid_menu")

    def set_host_objs(self, *args):
        self.set_dropdown("host_obj_menu")

    def set_host_acts(self, *args):
        self.set_dropdown("host_act_menu")

    def set_host_args(self, *args):
        self.set_args("host")


    ## WEBS

    def set_web_details(self, *args):
        lmid = self.widgets["web_lmid_str"].get()
        pool = dima.pools[dima.lmobjs[lmid]]

        try: dssl_date = utils.format_date(pool.dev_ssl_due, "%d %b %Y")
        except: dssl_date = "NaN"

        try: pssl_date = utils.format_date(pool.prod_ssl_due, "%d %b %Y")
        except: pssl_date = "NaN"

        self.widgets["web_id_str"].set(pool.lmid)
        self.widgets["web_ddomain_str"].set(f"{pool.dev_domain}:{pool.dev_port}")
        self.widgets["web_pdomain_str"].set(f"{pool.prod_domain}:{pool.prod_port}")
        self.widgets["web_dlang_str"].set(pool.default_lang)
        self.widgets["web_dtheme_str"].set(pool.default_theme)

        self.widgets["web_alias_str"].set(pool.alias)
        self.widgets["web_dssl_str"].set(dssl_date)
        self.widgets["web_pssl_str"].set(pssl_date)
        self.widgets["web_langs_str"].set(', '.join([utils.projects.langs[l] for l in pool.lang_ids]))
        self.widgets["web_themes_str"].set(', '.join(pool.themes))

    def send_web_cmd(self, *args):
        self.send_cmd("web")

    # Dropdowns
    def set_web_lmids(self, *args):
        self.set_dropdown("web_lmid_menu")

    def set_web_objs(self, *args):
        self.set_dropdown("web_obj_menu")

    def set_web_acts(self, *args):
        self.set_dropdown("web_act_menu")

    def set_web_args(self, *args):
        self.set_args("web")

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
