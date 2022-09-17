class LogUtils:
    # Projects have a cron job to tell Hal to retrieve logs
    # To do: method to change log level
    log_file = utils.logs_dir + app.lmid + ".log"
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
            print(util.color(*self.levels[level]) + ": " + message)

        if level == 5: app.stop()

    def create_record(self, call_info, level, message):
        filename, lineno, function = call_info
        if function == "execute" and level == 2 and len(message) > 256:
            message = message[:253] + "..."

        record = f"{util.now()} {filename.split('/')[-1]} l{lineno} {function}() {self.levels[level][0]}: {message}\n"

        util.write(self.log_file, record, mode='a')

    def reset(self):
        # To do: save old log files
        util.write(self.log_file, "")

utils.logs = LogUtils()
