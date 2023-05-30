
class Task():
    def __init__(self, obj, act, params, empty=False):
        self.aborted = False
        self.env = params.get("env") or "dev"

        if empty: return

        if obj.startswith("lm"):
            dbid = dima.lmobjs[obj]
            module_id = dima.lmobjs[dbid][1]

            try:
                getattr(dima.pools[dbid], act)(**params)
            except Exception as e:
                log(e, level=4, console=True)

        elif obj.startswith("utils"):
            getattr(getattr(utils, obj.split('.')[1]), act)(**params)
        elif obj == "dima":
            getattr(dima, act)(**params)

    def abort(self):
        self.aborted = True

task = Task("", "", {}, empty=True)

def authorize(func):
    if task.aborted:
        log("Task aborted!", level=3, console=True)
        raise Exception("Task aborted!")
    else:
        return func
