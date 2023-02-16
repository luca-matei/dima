import os, ast, logging, psycopg2, string, markdown

class lm:
    name = "hello-world.dev.lucamatei.ro"
    path = os.path.abspath(__file__)[:-len(os.path.basename(__file__))]

    def __init__(self):
        self.setup_logger('lm001', '../data/lm001.log', '%(levelname)s %(filename)s %(lineno)d %(funcName)s %(relativeCreated)dms  %(message)s')
        self.log = logging.getLogger('lm001')

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
        with open('db.ast', mode='r', encoding='utf-8') as f:
            self.config = ast.literal_eval(f.read())
        self.pgconnect()

        if self.pgconn:
            # 0 - name; 1 - ids
            lm.langs = [dict(self.pgexecute('select name, id from misc.lang;'))]
            lm.langs.append(lm.utils.invert_dict(lm.langs[0]))

            lm.components = dict(self.pgexecute('select id, name from resources.components;'))
            lm.sections = dict(self.pgexecute('select name, component from resources.sections;'))
            lm.resources = dict(self.pgexecute('select resource, id from resources.templates;'))
            lm.themes = dict(self.pgexecute('select id, name from misc.theme;'))

    def pgconnect(self):
        try:
            self.pgconn = psycopg2.connect(
                host = self.config['host'],
                port = self.config['port'],
                database = self.config['database'],
                user = self.config['user'],
                password = self.config['password'],
            )

        except:
            lm.log.exception("No connection to db!")

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
            lm.log.error("No cursor available!")
            return ()

        if log:
            lm.log.info(f"Query: {query}")
            lm.log.info(f"Params: {params}")

        try:
            cursor.execute(query, params)
            if query.startswith('select') or query.endswith('returning id;'):
                response = cursor.fetchall()
            # To add update case where it returns a confirmation response

        except (Exception, psycopg2.Error) as error:
            lm.log.error(f"Could't execute the query! {error}")
            return ()

        if log: lm.log.info(f"Response: {response}")

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
    """
        Here's where all the magic happens

        cache
        html5 {
            1 (42, "template")
            2 {
                1 (containers,)
                2 (containers,)
            3 {
                1 (title, desc)
                2 (title, desc)
    """
    cache = {}

    def __init__(self):
        # Cache app template
        self.set_template(1)
        for lang in lm.utils.get_keys(lm.langs[1]):
            self.set_content(lang, 1)

    def set_template(self, resource):
        query = "select cshow from resources.templates where id=%s;"
        params = resource,
        data = lm.db.pgexecute(query, params)

        if data:
            data = data[0][0]
            #lm.log.debug(data)
            self.check_cache(resource, 1)
            self.cache[resource][1] = data
        return data

    def set_content(self, lang, resource):
        query = "select cshow from resources.content where template=%s and lang=%s order by cnt_id;"
        params = resource, lang,
        data = lm.db.pgexecute(query, params)

        if data:
            data = [x[0] for x in data]
            #lm.log.debug(data)
            self.check_cache(resource, 2)
            self.cache[resource][2][lang] = data

        return data

    def set_meta(self, lang, resource):
        query = "select cnt from resources.meta where template=%s and lang=%s order by type;"
        params = resource, lang,
        data = lm.db.pgexecute(query, params)

        if data:
            data = [x[0] for x in data]
            #lm.log.debug(data)
            self.check_cache(resource, 3)
            self.cache[resource][3][lang] = data

        return data

    def check_cache(self, resource, opt=0):
        if self.cache.get(resource) is None:
            self.cache[resource] = {}

        if self.cache[resource].get(opt) is None and (opt == 2 or opt == 3):
            self.cache[resource][opt] = {}

    def get_cache(self, lang, section, res, method, opt):
        # opt: 1 = template; 2 = content; 3 = meta

        resource = lm.resources[f'{section}-{res}-{lm.http.methods[method]}']
        self.check_cache(resource, opt)

        data = self.cache[resource].get(opt)
        if not data:
            if opt == 1:
                return self.set_template(resource)
            elif opt == 2:
                return self.set_content(lang, resource)
            elif opt == 3:
                return self.set_meta(lang, resource)

        else:
            if opt != 1:
                data = data.get(lang)
                #lm.log.debug(data)
                if data is None:
                    if opt == 2:
                        return self.set_content(lang, resource)
                    elif opt == 3:
                        return self.set_meta(lang, resource)
            return data

    def wrap_app(self, lang, meta, body):
        html5 = lm.data.cache[1][1].format(*lm.data.cache[1][2][lang])

        if meta[2][0] == 'home':
            tmp_permalink = 'home'
        elif meta[2][1] == 'overview':
            tmp_permalink = meta[2][0]
        else:
            tmp_permalink = '/'.join(meta[2])

        tmp_lang = lm.langs[1][lang]
        tmp_multilingual = len(lm.langs[1]) > 1
        tmp_base = f'<base href="/{tmp_lang}/">' if tmp_multilingual else '/'

        if tmp_multilingual:
            tmp_alt = ''.join([f'<link rel="alternate" href="/{x}/{tmp_permalink}" hreflang="{x}" />' for x in lm.utils.get_keys(lm.langs[0]) if x != lm.langs[1][lang]])
        else:
            tmp_alt = ''

        html5 = html5.format(
            tmp_lang,
            lm.themes[1],   # To get from user - guest if no account,
            tmp_base,
            lm.name,
            meta[1],
            f'https://{lm.name}{"/" + tmp_lang if tmp_multilingual else ""}/{tmp_permalink}',
            meta[0],
            tmp_alt,
            body,
            tmp_permalink
        )

        return html5.encode('utf-8')
lm.data = lmData()


class lmHttp:
    origin = 'https://dev.lucamatei.ro/'
    methods = 'get', 'post', 'put', 'delete',
    packs = {
        'text/html': 'html',
        'text/plain': 'plain',
        }

    http_packs = {
        'html': 'text/html',
        'plain': 'text/plain',
        }

    resources = {
        'http': {
            'status': ('lm', ('get', 'post', 'put', 'delete'), ('html', 'plain')),
            },
        }
lm.http = lmHttp()


class lmStatic:
    resources = {
        'home': {
            'overview': ('lm', ('get', 'post', 'put', 'delete'), ('html', 'plain')),
            },
        }

    def dispatch(self, lang, section, res, data, edit, method, pack):
        self.status, self.headers = 200, []

        handler = self.resources[section][res][0]
        content = getattr(self, handler+method)(lang, section, res)

        if self.status == 200: body = getattr(self, f'{pack}{handler}pack')(lang, section, res, content)
        else: body = ''

        return self.status, self.headers, body

    def lmget(self, lang, section, res):
        return lm.data.get_cache(lang, section, res, 0, 2)

    def htmllmpack(self, lang, section, res, content):
        body = lm.data.get_cache(lang, section, res, 0, 1).format(*content)
        meta = lm.data.get_cache(lang, section, res, 0, 3) + [[section, res]]
        return lm.data.wrap_app(lang, meta, body)
lm.static = lmStatic()


class lmProcess:
    def request(self, url, method, pack):
        #lm.log.debug([url, method, pack])
        # URL
        url = lm.utils.normalize(url).strip('/').split('/')

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
            lang = lm.langs[0].get(st, 1)
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
                if rd in lm.utils.get_keys(getattr(lm, comp).resources[section]):
                    res = rd

                else:
                    comp = 'http'
                    section = 'http'
                    res = 'status'
                    data = 404
                    skip = True

        if res is None:
            res = lm.utils.get_keys(getattr(lm, comp).resources[section])[0]

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

        # To be separated

        # METHOD
        method = lm.utils.normalize(method)
        #lm.log.debug(method)
        if method not in getattr(lm, comp).resources[section][res][1]:
            comp = 'http'
            section = 'http'
            res = 'status'
            data = 405
            method = 'get'

        # PACK
        pack = lm.http.packs.get(lm.utils.normalize(pack))
        #lm.log.debug(pack)
        if pack not in getattr(lm, comp).resources[section][res][2]:
            comp = 'http'
            section = 'http'
            res = 'status'
            data = 406
            pack = 'plain'

        return comp, lang, section, res, data, edit, method, pack
lm.process = lmProcess()


def application(env, start_response):
    comp, lang, section, res, data, edit, method, pack = lm.process.request(env.get('PATH_INFO'), env.get('REQUEST_METHOD'), env.get('HTTP_ACCEPT').split(',')[0])

    #lm.log.debug('\n'.join([str(x) for x in [lang, comp, section, res, data, edit, method, pack]]))

    status, headers, body = getattr(lm, comp).dispatch(lang, section, res, data, edit, method, pack)
    if status not in (200, 303):
        status, headers, body = lm.http.dispatch(lang, 'http', 'status', status, False, method, pack)

    headers.append(('Content-Type', lm.http.http_packs.get(pack)))
    headers.append(('Content-Length', str(len(body))))

    start_response(str(status), headers)
    return [body]
