class lmProcess:
    def raw_request(self, env):
        lm.request = Request()

        lang = None
        lang_id = None

        section = None
        section_id = None

        page = None
        page_id = None

        module = None
        module_id = None

        method = env.get("REQUEST_METHOD").lower()
        method_id = lm.http.methods[method]

        browser = env.get("HTTP_USER_AGENT")
        endpoint = utils.normalize_url(env.get("PATH_INFO")).strip('/').split('/')
        lm.request.endpoint = list(endpoint)    # list is needed to create a new variable and drop the reference
        pack = env.get("HTTP_ACCEPT")

        log(pprint.pformat(env, indent=4))
        log(endpoint)

        # Perfect endpoint: /en/blog/cat/3255/edit/hello
        endpoint += ['' for i in range(5 - len(endpoint))]

        lang = endpoint[0]
        lang_id = lm.langs.get(lang)
        if lang_id:
            endpoint.pop(0)
        else:
            lang_id = 1
            lang = lm.langs[1]

        lm.request.lang = str(lang)
        lm.request.lang_id = int(lang_id)

        def find_end_section(parent_id):
            tmp_id = lm.sections[parent_id].get(endpoint[0], 0)
            if tmp_id:
                section = endpoint[0]
                endpoint.pop(0)
                section_id = tmp_id
                find_end_section(tmp_id)

        section = endpoint[0]
        section_id = lm.sections[0].get(section, 0)
        if section_id:
            endpoint.pop(0)
            find_end_section(section_id)
        else:
            section_id = lm.sections[0]["home"]
            section = "home"

        page = endpoint[0]
        page_data = lm.pages[section_id].get(page, 0)
        # Check for illegal page
        if page_data:
            endpoint.pop(0)
        else:
            page = lm.first_pages[section_id]
            page_data = lm.pages[section_id][page]

        # Check for illegal method
        page_id = page_data[lang_id][method_id][0]
        module_id = lm.pages[section_id][page][lang_id][method_id][1]
        module = lm.modules[module_id]

        if module == "static":
            body = lm.dynamic.solve_placeholders(getattr(lm, module).fetch_page(page_id))

        return Response(body)

lm.process = lmProcess()
