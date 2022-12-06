class CLI:
    receive_command = True
    acts = {}
    objs = {}
    args = {}

    def start(self):
        log("Starting CLI ...")

        command = ""
        while self.receive_command:
            command = input(" > ")

            if command in ("q", "exit"):
                self.stop()
            elif command == "":
                continue
            else:
                self.process(command)

    def stop(self):
        log("Stopping CLI ...")
        self.receive_command = False

    def invalid(self, a=None, o=None, ao=None):
        if a and o:
            log(f"Invalid action '{a}' on object '{o}'!", level=4, console=True)
        elif a:
            log(f"Invalid action '{a}'!", level=4, console=True)
        elif o:
            log(f"Invalid object '{o}'!", level=4, console=True)
        elif ao:
            log(f"Invalid action or object '{ao}'!", level=4, console=True)

    def validate(self, command):
        # To do: Validate command
        if '""' in command:
            log("Not a valid command format!", level=4, console=True)
            return 0
        return 1

    def process_params(self, params):
        return {}

    def process(self, command):
        log("Issued command: " + command)
        if not self.validate(command): return

        command = [p for p in re.split("( |\\\".*?\\\"|'.*?')", command) if p.strip()] + ['']    # Split by spaces unless surrounded by quotes

        lmobj_id = hal.lmobjs.get(command[0], 0)    # Try to get a lmobj
        if lmobj_id:
            # lmobj act obj    ===    lm1 restart nginx
            # lmobj act        ===    lm3 save

            lmobj, act, obj = command[:3]
            act_id = self.acts.get(act, 0)

            if not act_id:
                return self.invalid(a=act)

            # Find object id from particular command
            module_id = hal.lmobjs[lmobj_id][1]      # Get Host module id
            obj_id = self.objs[module_id].get(obj, 0)    # Get nginx object id

            if obj_id == 0:    # It can be ''
                return self.invalid(o=obj)

            # Get command object details
            obj_data = self.objs[module_id][obj_id]

            # Check if action is valid
            if act_id not in obj_data[2]:
                return self.invalid(a=act, o=lmobj)

            # Solve parameters
            try: params = command[2:]
            except: params = []

            params = self.process_params(params)

            # Call the method
            if obj == '':
                getattr(hal.pools[lmobj_id], act)(**params)
            else:
                getattr(hal.pools[lmobj_id], act + '_' + obj)(**params)

        else:
            # act obj    ===    create net
            # obj        ===    status

            act, obj = command[:2]
            act_id = self.acts.get(act, 0)

            if not act_id:
                return self.invalid(ao=act)

            module_id = 0
            module_ids = [x for x in utils.get_keys(self.objs) if hal.modules[x][0].islower()]
            obj_id = 0

            # Find object id from global command
            for m_id in module_ids:
                obj_id = self.objs[m_id].get(obj, 0)
                if obj_id:
                    module_id = m_id
                    break

            print(f"{act}:{act_id}, {obj}:{obj_id}, {params}")
            if not obj_id:
                return self.invalid(o=obj)

            # Get command object details
            obj_data = self.objs[module_id][obj_id]

            # Check if action is valid
            if act_id not in obj_data[2]:
                return self.invalid(a=act, o=lmobj)

            # Solve parameters
            try: params = command[2:]
            except: params = []

            params = self.process_params(params)

            # Call the method
            if obj == '':
                getattr(hal, act)(**params)
            else:
                getattr(getattr(globals(), module), act + '_' + obj)(**params)

cli = CLI()
