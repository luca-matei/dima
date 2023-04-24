class Logs:
    # To do: method to change log level
    file_path = __file__.split('/')
    file_dir, file_name = '/'.join(file_path[:-1]) + '/', file_path[-1]

    if file_name == "install.py":
        log_file = file_dir + 'install.log'
    else:
        log_file = utils.logs_dir + utils.get_src_dir().split('/')[-3] + ".log"

    levels = {
        1: ("Debug", "blue"),
        2: ("Info", "green"),
        3: ("Warning", "yellow"),
        4: ("Error", "lred"),
        5: ("Critical", "red"),
        }
    level = 1
    quiet = False

    def _log(self, call_info, message, console=False, level=2):
        # Web apps have console = False

        if level not in range(1, 6):
            self.create_record(call_info, 3, "Log level set incorrectly!")
            level = self.level

        if level >= self.level:
            self.create_record(call_info, level, message)

        if console and not self.quiet:
            print(utils.color(*self.levels[level]) + ": " + message)

            if gui:
                gui.set_status(*self.levels[level], message)

        if level == 5:
            print("Exiting ...")
            sys.exit()

    def create_record(self, call_info, level, message):
        if type(call_info) == list and len(call_info) == 4: host = f" {call_info[3]}:"
        else: host = ""
        filename, lineno, function = call_info[:3]
        message = message.strip('\n')

        # function == "execute" and "Data" in message and
        if level == 2 and len(message) > 256:
            message = message[:253] + "..."

        record = f"{utils.now()} l{lineno} {function}(){host} {self.levels[level][0]}: {message}\n"

        utils.write(self.log_file, record, mode='a')

    def reset(self):
        # To do: save old log files
        utils.write(self.log_file, "")

logs = Logs()

def log(*args, **kwargs):
    a = inspect.currentframe()
    call_info = list(inspect.getframeinfo(a.f_back)[:3])
    logs._log(call_info, *args, **kwargs)
