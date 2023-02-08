class lmHttp:
    methods = {}
    packs = {
        'text/html': 'html',
        'text/plain': 'plain',
    }

    def __init__(self):
        self.packs.update(util.reverse_dict(self.packs))

lm.http = lmHttp()
