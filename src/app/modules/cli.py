class CLI:
    receive_command = True
    acts = {}
    objs = {}
    skip = False

    def invalid(self, a=None, o=None, ao=None, p=None, pt=None):
        if a and o:
            log(f"Invalid action '{a}' on object '{o}'!", level=4, console=True)
        elif a:
            log(f"Invalid action '{a}'!", level=4, console=True)
        elif o:
            log(f"Invalid object '{o}'!", level=4, console=True)
        elif ao:
            log(f"Invalid action or object '{ao}'!", level=4, console=True)
        elif pt:
            self.skip = True
            if pt == "missing":
                log(f"Missing positional parameter '{p}'!", level=4, console=True)
            else:
                log(f"Invalid value for parameter '{p}'. Expected type '{pt}'!", level=4, console=True)
        elif p:
            self.skip = True
            log(f"Invalid parameter '{p}'!", level=4, console=True)
        return {}

    def validate(self, command):
        # To do: Validate command
        if '""' in command:
            log("Not a valid command format!", level=4, console=True)
            return 0
        return 1

    def process_args(self, module, act, obj, tmp_args):
        # Rules:
        # Put positional parameters from method header in alphabetical order

        ## Organize required parameters

        # Get method parameters
        if obj: method = getattr(module, act + '_' + obj)
        else: method = getattr(module, act)

        param_pos, params = utils.get_method_params(method)

        ## Organize given arguments

        args = {}
        skip = False  # For cases like --cpus=4
        pos_index = 0  # Index of current positional argument
        for i, a in enumerate(tmp_args):
            if skip or not a:
                skip = False
                continue

            # Of form --message="Zavalaidanga"
            if a.startswith('-') and a.endswith('='):
                skip = True
                a = a.strip('-').strip('=').replace('-', '_')
                args[a] = tmp_args[i+1]

            # Of form --cpus=4
            elif "=" in a:
                arg = a.split("=")
                arg[0] = arg[0].strip("-").replace('-', '_')
                args[arg[0]] = arg[1]

            # Of form --no-create-home
            elif a.startswith('-'):
                a = a.strip('-').replace('-', '_')
                args[a] = True

            # Positional parameter
            else:
                try:
                    args[param_pos[pos_index]] = a
                    pos_index += 1
                except IndexError:
                    return self.invalid(p=a)

        ## Validate arguments as parameters

        for a in utils.get_keys(args):
            # Check data types
            if params.get(a, False):
                arg_type = params[a][0]
                arg = args[a]
                if arg_type == 'int':
                    try: args[a] = int(arg)
                    except ValueError: return self.invalid(p=a, pt='int')

                elif arg_type == 'float':
                    try: args[a] = float(arg)
                    except ValueError: return self.invalid(p=a, pt='float')

                elif arg_type == 'bool':
                    if arg.lower() in ("1", "true", "yes", "y"):
                        args[a] = True
                    elif arg.lower() in ("0", "false", "no", "n"):
                        args[a] = False
                    else:
                        return self.invalid(p=a, pt='boolean')

                elif arg_type == "list":
                    args[a] = arg.split(',')
                
                elif arg_type == "env":
                    envs = utils.get_keys(utils.hosts.envs)
                    # dev, test, prod
                    if arg in envs:
                        args[a] = arg

                    # 1, 2, 3
                    elif arg.isdigit() and int(arg) in envs:
                        args[a] = utils.hosts.envs[int(arg)]

                    else:
                        return self.invalid(p=a, pt='env')

                elif arg_type == "web_state":
                    try: args[a] = int(arg)
                    except ValueError: return self.invalid(p=a, pt='int')

                    if args[a] not in range(1, len(utils.webs.states) + 1):
                        return self.invalid(p=a, pt="web_state")

                elif arg_type == "hidden":
                    continue

                # Remove extra quotes
                elif args[a].startswith("'"):
                    args[a] = args[a].strip("'")

                elif args[a].startswith('"'):
                    args[a] = args[a].strip('"')

            elif a == "help" and args[a] == True:
                self.skip = True
                doc = method.__doc__
                if doc: print(doc)
                else: log("No help available for this command!", level=4, console=True)
                return {}
            else:
                return self.invalid(p=a)

        # Check for missing positional parameters
        for p in param_pos:
            if not args.get(p):
                return self.invalid(p=p, pt='missing')

        return args

    def load_history(self):
        self.history = utils.read(utils.src_dir + "app/history.txt", lines=True)

    def append_history(self, command):
        if len(self.history) >= 300:
            self.history = self.history[-200:]
            utils.write(utils.src_dir + "app/history.txt", '\n'.join(self.history))

        if command not in self.history[-3:]:
            self.history.append(command)
            utils.write(utils.src_dir + "app/history.txt", command + "\n", mode="a")

    def process(self, command):
        global task
        log("Issued command: " + command)

        if not self.validate(command): return
        self.append_history(command)

        command = [p for p in re.split("( |\\\".*?\\\"|'.*?')", command) if p.strip()] + ['']    # Split by spaces unless surrounded by quotes

        lmobj_id = dima.lmobjs.get(command[0], 0)    # Try to get a lmobj

        if lmobj_id:
            # lmobj act obj    ===    lm1 restart nginx
            # lmobj act        ===    lm3 save

            lmobj, act, obj = command[:3]
            act_id = self.acts.get(act, 0)
            if obj.startswith("-"): obj = ''

            if not act_id:
                return self.invalid(a=act)

            # Find object id from particular command
            module_id = dima.lmobjs[lmobj_id][1]      # Get Host module id
            obj_id = self.objs[module_id].get(obj, 0)    # Get nginx object id

            if not obj_id:
                return self.invalid(o=obj)

            # Get command object details
            obj_data = self.objs[module_id][obj_id]

            # Check if action is valid
            if act_id not in obj_data[1]:
                return self.invalid(a=act, o=lmobj)

            # Solve arguments
            try: args = command[3:] if obj else command[2:]
            except: args = []

            params = self.process_args(dima.pools[lmobj_id], act, obj, args)
            if self.skip:
                self.skip = False
                return

            # Call the method
            if obj:
                act += "_" + obj

            task = Task(obj=lmobj, act=act, params=params)

        else:
            # act obj    ===    create net
            # obj        ===    status

            act, obj = command[:2]
            act_id = self.acts.get(act, 0)
            if obj.startswith("-"): obj = ''

            if not act_id:
                return self.invalid(ao=act)

            module_id = 0
            module_ids = [x for x in utils.get_keys(self.objs) if dima.modules[x][0].islower()]
            obj_id = 0

            # Find object id from global command
            for m_id in module_ids:
                obj_id = self.objs[m_id].get(obj, 0)
                if obj_id:
                    module_id = m_id
                    module = dima.modules[m_id]
                    break

            if not obj_id:
                return self.invalid(o=obj)

            # Get command object details
            obj_data = self.objs[module_id][obj_id]

            # Check if action is valid
            if act_id not in obj_data[1]:
                return self.invalid(a=act, o=obj)

            # Solve parameters
            try: args = command[3:] if obj else command[2:]
            except: args = []

            if obj == '':
                params = self.process_args(dima, act, obj, args)

            elif module.startswith("utils"):
                params = self.process_args(getattr(utils, module.split('.')[1]), act, obj, args)
            else:
                params = self.process_args(module, act, obj, args)

            # Invalid parameters
            if self.skip:
                self.skip = False
                return

            # Call the method
            if obj == '':
                module = "dima"
            else:
                act += "_" + obj

            task = Task(obj=module, act=act, params=params)

cli = CLI()
