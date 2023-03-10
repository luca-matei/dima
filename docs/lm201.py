import os, ast, logging, psycopg2, string, markdown, re
from datetime import datetime

class lm:
    path = os.path.abspath(__file__)[:-len(os.path.basename(__file__))]

    def __init__(self):
        with open(f"{self.path}settings.ast", mode="r", encoding="utf-8") as f:
            self.settings = ast.literal_eval(f.read())

        self.id = self.settings['id']
        self.name = self.settings['name']
        self.pg = self.settings['pg']
        self.langs = dict([(c, i) for i, c in enumerate(self.settings['langs'], start=1)] + [(i, c) for i, c in enumerate(self.settings['langs'], start=1)])
        self.themes = self.settings['themes']
        self.app = self.settings['app']
        self.components = dict([(i, c) for i, c in enumerate(self.app, start=1)] + [(c, i) for i, c in enumerate(self.app, start=1)])
        self.sections = dict([(section, self.components[comp]) for comp in list(self.app.keys()) for section in list(self.app[comp].keys())])

        self.setup_logger(self.id, f'../data/{self.id}.log', '%(levelname)s %(filename)s %(lineno)d %(funcName)s %(relativeCreated)dms  %(message)s')
        self.logger = logging.getLogger(self.id)

    def log(self, msg, lvl="debug"):
        getattr(self.logger, lvl)(msg)

    def setup_logger(self, name, filename, formatter):
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        fileHandler = logging.FileHandler(filename=f'{self.path}{filename}', encoding='utf-8', mode='w')
        fileHandler.setFormatter(logging.Formatter(formatter))
        streamHandler = logging.StreamHandler()
        streamHandler.setFormatter(formatter)
        logger.addHandler(fileHandler)
        logger.addHandler(streamHandler)
lm = lm()

class lmUtils:
    def normalize(self, txt):
        txt = txt.lower()
        tmp = []
        for c in txt:
            d = lm.html.diacritics.get(c, '')
            if d:
                tmp.append(d)
                continue
            if c in lm.html.characters:
                tmp.append(c)

        return ''.join(tmp)

    def invert_dict(self, dict):
        return {v: k for k, v in dict.items()}

    def get_keys(self, d):
        return list(d.keys())

    def get_values(self, d):
        return list(d.values())
lm.utils = lmUtils()

class lmDb:
    def __init__(self):
        try:
            self.pgconn = psycopg2.connect(
                host = lm.pg['host'],
                port = lm.pg['port'],
                database = lm.id,
                user = lm.id,
                password = lm.pg['password'],
            )

        except:
            lm.log("No connection to db!", "error")

        # Templates
        query = "select name, id from app.templates;"
        lm.templates = dict(self.pgexecute(query))

        # Contents ID's
        query = "select name, lang, id from app.contents;"
        contents = self.pgexecute(query)
        lm.contents = {}

        for content in contents:
            if content[0] not in lm.utils.get_keys(lm.contents):
                lm.contents[content[0]] = {}
            lm.contents[content[0]][content[1]] = content[2]

        # Content Variables
        query = "select name, lang, value from app.content_variables;"
        variables = self.pgexecute(query)
        lm.variables = {}

        for var in variables:
            if var[0] not in lm.utils.get_keys(lm.variables):
                lm.variables[var[0]] = {}
            lm.variables[var[0]][var[1]] = var[2]

    def pgexecute(self, query, params=(), log=False):
        response = None
        cursor = None
        for tries in range(2):
            try:
                cursor = self.pgconn.cursor()
                break
            except:
                continue

        if cursor == None:
            lm.log("No cursor available!", "error")
            return ()

        if log:
            lm.log(f"Query: {query}")
            lm.log(f"Params: {params}")

        try:
            cursor.execute(query, params)
            if query.startswith('select') or query.endswith('returning id;'):
                response = cursor.fetchall()
            # To add update case where it returns a confirmation response

        except (Exception, psycopg2.Error) as error:
            lm.log(f"Could't execute the query! {error}", "error")
            return ()

        if log: lm.log(f"Response: {response}")

        self.pgconn.commit()
        cursor.close()
        if response != None:
            return response
lm.db = lmDb()

class lmHtml:
    characters = string.digits + string.ascii_lowercase + string.ascii_uppercase + '/.-'

    escapes = {
        '&': '&amp;',
        '"': '&quot;',
        "'": '&apos;',
        '>': '&gt;',
        '<': '&lt;',
        }
    diacritics = {
        'ă': 'a',
        'â': 'a',
        'î': 'i',
        'ș': 's',
        'ş': 's',
        'ț': 't',
        ' ': '-',
        '_': '-',
        }

    def md2html(self, md):
        return markdown.markdown(md)
lm.html = lmHtml()

class lmData:
    def __init__(self):
        self.maps()

    def maps(self):
        sitemap = ["""<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">"""]
        robots = ["User-agent: *"]
        langs = [x for x in lm.langs if isinstance(x, str)]
        sections = {}
        for section in lm.utils.get_values(lm.app):
            sections.update(section)

        for lang in langs:
            for section in lm.utils.get_keys(sections):
                for resource in lm.utils.get_keys(sections[section]):
                    if sections[section][resource][3]:
                        sitemap.append(f"""<url><loc>https://www.{lm.name}/{lang}/{section}/{resource + '/' if resource != section else ''}</loc><lastmod>{datetime.utcnow().strftime("%Y-%m-%dT%X+03:00")}</lastmod></url>""")
                        robots.append(f"Allow: /{lang}/{section}{'/' + resource if resource != section else ''}")

        sitemap.append("</urlset>")
        robots.append("Disallow: /")
        robots.append(f"Sitemap: https://www.{lm.name}/sitemap.xml")

        with open(f"{lm.path}../assets/sitemap.xml", mode="w", encoding="utf-8") as f:
            f.write(''.join(sitemap))

        with open(f"{lm.path}../assets/robots.txt", mode="w", encoding="utf-8") as f:
            f.write('\n'.join(robots))

    def retr(self, opt, section=None, res=None, method=None, lang=None):
        """
            opt: 1 = template; 2 = content; 12 = template + content
        """

        if section is None: section=lm.request.section
        if res is None: res=lm.request.res
        if method is None: method=lm.request.method
        if lang is None: lang=lm.request.lang

        if opt == 1:
            query = "select html5 from app.templates where id=%s;"
            params = lm.templates[f"{section}-{res}-{method}"],
            return lm.db.pgexecute(query, params)[0][0]

        elif opt == 2:
            query = "select text from app.content_records where content=%s order by id;"
            params = lm.contents[f"{section}-{res}-{method}"][lang],
            return [x[0] for x in lm.db.pgexecute(query, params)]

        elif opt == 3:
            return self.retr(2, section, res, "meta", lang)

        elif opt == 12:
            # Cache with Nginx for performance!
            template = self.retr(1, section, res, method, lang)
            vars = list(dict.fromkeys(re.findall(r'\$(.*?)%', template)))
            for var in vars:
                template = template.replace(f'${var}%', lm.variables.get(var, {}).get(lang))

            return template.format(*self.retr(2, section, res, method, lang))

    def wrap_app(self, meta, body):
        html5 = self.retr(12, 'html5', 'app', 'get')

        permalink = lm.request.section
        if lm.request.res != lm.request.section:
            permalink += '/' + lm.request.res

        if lm.request.data:
            permalink += '/' + str(lm.request.data)

        lang_name = lm.langs[lm.request.lang]
        other_lang = lm.langs[1] if lm.request.lang == 2 else lm.langs[2]

        if lm.autho.has_session():
            user_drop = self.retr(12, 'html5', 'user', 'get')
        else:
            user_drop = self.retr(12, 'html5', 'guest', 'get').format(
                "checked" if lm.request.lang == 2 else "",
                f"/{other_lang}/{permalink}",
                )

        html5 = html5.format(
            lang = lang_name,
            base = f"""<base href="/{lang_name}/">""",
            app_name = lm.name,
            desc = meta[1],
            url = f'https://{lm.name}/{lang_name}/{permalink}',
            title = meta[0],
            alt = f'<link rel="alternate" href="/{other_lang}/{permalink}" hreflang="{other_lang}" />',
            drop = user_drop,
            body = body,
            permalink = permalink,
        )

        return html5.encode('utf-8')
lm.data = lmData()

class lmHttp:
    methods = 'get', 'post', 'put', 'delete',
    statuses = 200,\
               303,\
               400, 401, 403, 404, 405, 406, 410,\
               500, 503
    packs = {
        'text/html': 'html',
        'text/plain': 'plain',
        }

    http_packs = {
        'html': 'text/html',
        'plain': 'text/plain',
        }

    def lmget(self):
        if lm.request.data not in self.statuses:
            status = 404
        else:
            status = lm.request.data
        return [str(status)[0]] + lm.data.retr(2, method=status)

    def lmpost(self):
        return self.lmget()

    def lmput(self):
        return self.lmget()

    def lmdelete(self):
        return self.lmget()

    def htmllm(self, content):
        meta = [content[1], content[2]]
        body = lm.data.retr(1).format(*content)
        return meta, body

    def plainlm(self):
        return
lm.http = lmHttp()

class lmAutho:
    def has_session(self):
        return False
lm.autho = lmAutho()

class lmAuthe:
    pass
lm.authe = lmAuthe()

class lmStatic:
    def lmget(self):
        return

    def htmllm(self, content):
        meta = lm.data.retr(3)
        body = lm.data.retr(12)
        return meta, body
lm.static = lmStatic()

class lmDocs:
    def lmget(self):
        return

    def htmllm(self, content):
        meta = lm.data.retr(3)
        body = lm.data.retr(12, "docs", "docs", "get").format(lm.data.retr(12))
        return meta, body
lm.docs = lmDocs()

class lmRequest:
    def __init__(self, env, comp, lang, section, res, data, edit, method, pack):
        self.env = env
        self.comp = comp
        self.lang = lang
        self.section = section
        self.res = res
        self.data = data
        self.edit = edit
        self.method = method
        self.pack = pack

        self.handler = lm.app[comp][section][res][0]

class lmResponse:
    def __init__(self):
        self.status = 200
        self.headers = []
        self.body = ""

    def add_header(self, name, body):
        self.headers.append((name, body))

class lmProcess:
    def request(self, env):
        url = lm.utils.normalize(env.get('PATH_INFO')).strip('/').split('/')
        method = env.get('REQUEST_METHOD')
        pack = env.get('HTTP_ACCEPT').split(',')[0]

        # /ro/blog/cat/47725/hello
        # lang, section, resource, data, edit
        # first, second, third, fourth, edit
        # st nd rd th, edit

        lang = None
        comp = None
        section = None
        res = None
        data = None
        edit = False
        skip = False
        index = 0

        # If first exists: /ro, /feig, /about
        try:
            st = url[index]
            # It can be empty
            if not st:
                raise IndexError
        except IndexError:
            lang = 1
            comp = 'static'
            section = 'home'
            res = None
            data = None
            skip = True
        else:
            # If lang exists: /ro, /en
            lang = lm.langs.get(st, 1)
            if lang:
                index += 1

        if not skip:
            # If second exists: /home, /feig, /about
            try:
                nd = url[index]
            except IndexError:
                comp = 'static'
                section = 'home'
                res = None
                data = None
                skip = True
            else:
                index += 1
                # If section exists: /home, /about
                comp_id = lm.sections.get(nd)
                if comp_id:
                    comp = lm.components.get(comp_id)
                    section = nd

                else:
                    comp = 'http'
                    section = 'http'
                    res = 'status'
                    data = 404
                    skip = True

        if not skip:
            # If third exists: /status, /feig, /cat
            try:
                rd = url[index]
            except IndexError:
                skip = True
            else:
                index += 1
                # If resource exists: /exp, /art
                if rd in lm.utils.get_keys(lm.app[comp][section]):
                    res = rd

                else:
                    comp = 'http'
                    section = 'http'
                    res = 'status'
                    data = 404
                    skip = True

        if res is None:
            res = lm.utils.get_keys(lm.app[comp][section])[0]

        if not skip:
            # If fourth exists: /5435, /feig
            try:
                th = url[index]
            except IndexError:
                skip = True
            else:
                index += 1
                # If data exists: /5435
                # Will have its own instance when there'd be ids of 'jXhO3m' form
                if comp != 'static' and th.isdigit():
                    data = int(th)
                else:
                    comp = 'http'
                    section = 'http'
                    res = 'status'
                    data = 404
                    skip = True

        if not skip:
            # If edit exists
            try:
                edit = url[index]
            except IndexError:
                pass
            else:
                index += 1
                # If edit exists: /edit
                if edit == 'edit':
                    edit = True

        # METHOD
        method = lm.utils.normalize(method)
        if method not in lm.app[comp][section][res][1]:
            comp = 'http'
            section = 'http'
            res = 'status'
            data = 405
            method = 'get'

        # PACK
        pack = lm.http.packs.get(lm.utils.normalize(pack))
        if pack not in lm.app[comp][section][res][2]:
            comp = 'http'
            section = 'http'
            res = 'status'
            data = 406
            pack = 'plain'

        lm.request = lmRequest(env, comp, lang, section, res, data, edit, method, pack)

    def response(self):
        lm.response = lmResponse()

        content = getattr(getattr(lm, lm.request.comp), lm.request.handler + lm.request.method)()
        body = getattr(getattr(lm, lm.request.comp), lm.request.pack + lm.request.handler)(content)

        if lm.request.pack == "html":
            body = lm.data.wrap_app(*body)
        elif lm.request.pack == "plain":
            body = json.dumps(body)

        lm.response.body = body

    def abort(self, status):
        lm.request.comp, lm.request.res, lm.request.data = 'http', 'status', status
        self.response()
lm.process = lmProcess()

def application(env, start_response):
    lm.process.request(env)
    lm.process.response()

    lm.response.add_header('Content-Type', lm.http.http_packs.get(lm.request.pack))
    lm.response.add_header('Content-Length', str(len(lm.response.body)))

    start_response(str(lm.response.status), lm.response.headers)
    return [lm.response.body]
