class LogUtils:
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

    def _log(self, call_info, message, level=2):
        if level not in range(1, 6):
            self.create_record(call_info, 3, "Log level set incorrectly!")
            level = self.level

        if level >= self.level:
            self.create_record(call_info, level, message)

        if level == 5:
            # Go into critical mode
            print("Exiting ...")
            #sys.exit()

    def create_record(self, call_info, level, message):
        filename, lineno, function = call_info
        if function == "execute" and level == 2 and len(message) > 256:
            message = message[:253] + "..."

        record = f"{utils.now()} l{lineno} {function}() {self.levels[level][0]}: {message}\n"

        utils.write(self.log_file, record, mode='a')

    def reset(self):
        # To do: save old log files
        utils.write(self.log_file, "")

logs = LogUtils()


def log(*args, **kwargs):
    a = inspect.currentframe()
    call_info = list(inspect.getframeinfo(a.f_back)[:3])
    logs._log(call_info, *args, **kwargs)
