class WebUtils:
    methods = "get", "put", "post", "delete"
    modules = {}
    fields = {
        "id": {
            'type': 'hidden',
            'minlen': 1,
            'maxlen': 10,
            'pattern': r"""^[\d]{1,10}$""",
        },
        "cat": {
            'type': 'hidden',
            'minlen': 1,
            'maxlen': 10,
            'pattern': r"""^[1-9]\d{,10}$""",
        },
        "tags": {
            'type': 'hidden',
            'minlen': 1,
            'maxlen': 88,
            'pattern': r"""^([0-9]+(,[0-9]{1,10}){0,8}){0,1}$""",
        },
        "lang": {
            'type': 'hidden',
            'minlen': 1,
            'maxlen': 1,
            'pattern': r"""^[\d]{1}$""",
        },
        "theme": {
            'type': 'hidden',
            'minlen': 1,
            'maxlen': 1,
            'pattern': r"""^[\d]{1}$""",
        },
        "title": {
            'type': 'text',
            'minlen': 1,
            'maxlen': 128,
            'pattern': r"""^[\sa-zA-Z0-9ăĂâîÎşŞţŢ'".!+?-]{1,128}$""",
        },
        "user": {
            'type': 'text',
            'minlen': 1,
            'maxlen': 64,
            'pattern': r"""^(?=.{1,64}$)(([a-z0-9._-]+)|([a-z0-9._+-]+@[a-z0-9._-]+\.[a-z]+))$""",
        },
        "username": {
            'type': 'text',
            'minlen': 1,
            'maxlen': 64,
            'pattern': r"""^[a-z0-9._-]{1,64}$""",
        },
        "email": {
            'type': 'email',
            'minlen': 5,
            'maxlen': 64,
            'pattern': r"""^(?=.{5,64}$)[a-z0-9._+-]+@[a-z0-9._-]+\.[a-z]+$""",
        },
        "password": {
            'type': 'password',
            'minlen': 1,
            'maxlen': 128,
            'pattern': """^[\w\d~`,.!@#$%^&*()\-+=\[\]'"?<>|]{1,128}$""",
        },
        "name": {
            'type': 'text',
            'minlen': 2,
            'maxlen': 64,
            'pattern': r"""^[\sa-zA-ZăĂâîÎşŞţŢ-]{2,64}$""",
        },
        "subject": {
            'type': 'hidden',
            'minlen': 3,
            'maxlen': 32,
            'pattern': r"""^[\sa-zA-ZăĂâîÎşŞţŢ-]{3,32}$""",
        },
        "phone": {
            'type': 'tel',
            'minlen': 0,
            'maxlen': 16,
            'pattern': r"""^[\d\s+.-]{0,16}$""",
        },
        "msg": {
            'minlen': 4,
            'maxlen': 4096,
            'pattern': r"""^[\s\w\dăĂâîÎşŞţŢ~`,.!@#$%^&*()+='"?<>|:;-]{4,4096}$""",
        },
        "cedit": {
            'type': 'text',
            'minlen': 4,
            'maxlen': 16384,
            'pattern': r"""^[\s\w\dăĂâîÎşŞţŢ~`,.!@#$%^&*()+=_'"?<>|:;\/\[\]-]{4,16384}$""",
        },
        "summary": {
            'type': 'text',
            'minlen': 1,
            'maxlen': 256,
            'pattern': r"""^[\sa-zA-Z0-9ăĂâîÎşŞţŢ,.!+?-]{1,256}$""",
        },
        "img": {
            'type': 'hidden',
            'minlen': 0,
            'maxlen': 65000,
            'pattern': r"""^((data:image\/)(jpg|jpeg)(;base64){0,1},([a-zA-Z0-9\/=+|]{10,65000})){0,1}$""",
        },
        "color": {
            'type': 'color',
            'minlen': 4,
            'maxlen': 7,
            'pattern': r"""^#(?:[0-9a-fA-F]{3}){1,2}$""",
        },
    }

    def construct_yaml_map(self, self2, node):
        data = []
        yield data
        for key_node, value_node in node.value:
            key = self2.construct_object(key_node, deep=True)
            val = self2.construct_object(value_node, deep=True)
            data.append((key, val))

    def create_web(self, domain:'str', name:'str'="", description:'str'="", alias:'str'="", modules:'list'=(), langs:'list'=(), themes:'list'=(), default_lang:'str'="", default_theme:'str'="", has_animations=False):
        self.__doc__ = Host.create_web.__doc__
        # To do: choose a host and invoke create_web()
        host_dbid = hal.lmobjs["lm8"]

        hal.pools.get(host_dbid).create_host(env, alias, mem, cpus, disk)

utils.webs = WebUtils()
