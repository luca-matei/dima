if __name__ != "__main__":
    from utils import utils

class LogUtils:
    # Projects have a cron job to tell Hal to retrieve logs
    # To do: method to change log level
    if __name__ != "__main__":
        log_file = utils.logs_dir + utils.get_src_dir().split('/')[-4] + ".log"
    else:
        log_file = utils.logs_dir + hal.lmid + ".log"

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

        if level == 5: app.stop()

    def create_record(self, call_info, level, message):
        filename, lineno, function = call_info
        if function == "execute" and level == 2 and len(message) > 256:
            message = message[:253] + "..."

        record = f"{utils.now()} {filename.split('/')[-1]} l{lineno} {function}() {self.levels[level][0]}: {message}\n"

        utils.write(self.log_file, record, mode='a')

    def reset(self):
        # To do: save old log files
        utils.write(self.log_file, "")

utils.logs = LogUtils()

def log(*args, **kwargs):
    a = inspect.currentframe()
    call_info = inspect.getframeinfo(a.f_back)[:3]
    utils.logs._log(call_info, *args, **kwargs)
