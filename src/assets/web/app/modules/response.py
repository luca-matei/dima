class Response:
    status = None
    headers = []
    body = None

    def __init__(self, body, status=200, headers=[]):
        self.body = body.encode('utf-8')

        self.status = status

        self.headers.append(('Content-Type', "text/html"))
        self.headers.append(('Content-Length', str(len(body))))
