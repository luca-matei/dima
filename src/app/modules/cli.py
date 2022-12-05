class CLI:
    receive_command = True
    acts = {}
    objs = {}
    args = {}

    def start(self):
        log("Starting CLI ...")

        command = ""
        while self.receive_command:
            command = input(f" > ")

            if command in ("q", "exit"):
                self.stop()
            elif command == "":
                continue
            else:
                self.process(command)

    def stop(self):
        log("Stopping CLI ...")
        self.receive_command = False

    def invalid(self, a=None, o=None):
        if a and o:
            log(f"Invalid action '{a}' on object '{o}'!", level=4, console=True)
        elif a:
            log(f"Invalid action '{a}'!", level=4, console=True)
        elif o:
            log(f"Invalid object '{o}'!", level=4, console=True)

    def validate(self, command):
        # To do: Validate command
        if '""' in command:
            log("Not a valid command format!", level=4, console=True)
            return 0
        return 1

    def process(self, command):
        log("Issued command: " + command)
        if not self.validate(command): return

        command = [p for p in re.split("( |\\\".*?\\\"|'.*?')", command) if p.strip()] + ['']    # Split by spaces unless surrounded by quotes

        act_id = self.command['acts'].get(command[0], 0)

        if act_id:
            obj = command[1]

            # Code's a bit redundant, but it's more organised than doing both
            if obj:
                # Check if it's a lm object (lm1, lmg2 etc.)
                if obj.startswith("lm"):
                    obj_id = app.lmobjs.get(obj, 0)    # This is lm1's id
                    if obj_id:
                        lmobj_id = obj_id
                        # Get module name based on its id found in lmobjs dict, match case from database and get the command object id
                        obj_id = self.command['objs'][app.modules[app.lmobjs[lmobj_id][1]]]     # This is 'lmapp' id
                        obj_data = self.command['objs'][obj_id]                                 # module, name, acts, args, help
                    else:
                        return self.invalid(o=obj)

                    # Check if action exists for object
                    if act_id not in obj_data[2]:
                        return self.invalid(a=act, o=obj)

                    # To do: Check params
                    try: params = command[2:]
                    except: params = []

                    # Call the method
                    getattr(app.pools[lmobj_id], act)(*params)

                # Check if it's a global object
                else:
                    obj_id = self.command['objs'].get(obj, 0)
                    if obj_id:
                        obj_data = self.command['objs'][obj_id]
                    else:
                        return self.invalid(o=obj)

                    # Check if action exists
                    if act_id in obj_data[2]:
                        module_id = obj_data[0]
                        module = app.modules[module_id]
                    else:
                        return self.invalid(a=act, o=obj)

                    # To do: Check params
                    try: params = command[2:]
                    except: params = []

                    # Call the method
                    getattr(getattr(app, module), act + '_' + obj)(*params)

        # Command like 'hal init', no positional parameters
        elif act_id in self.command['objs']['hal']:
            getattr(hal, act)()

        # Action to 'hal' isn't defined.
        else:
            return self.invalid(a=act)

cli = CLI()
