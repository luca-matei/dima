class lmDynamic:
    def solve_placeholders(self, html):
        endpoint = '/'.join(lm.request.endpoint[1:])
        if lm.autho.has_session():
            user_drop = lm.static.fetch_fraction("user-drop")
        else:
            user_drop = utils.format_tpl(lm.static.fetch_fraction("guest-drop"), {
                "checked": "" if lm.request.lang == lm.default_lang else "checked",
                "endpoint": endpoint,
                })

        html = utils.format_tpl(html, {
            "user_drop": user_drop,
            "permalink": endpoint
            })

        return html

lm.dynamic = lmDynamic()
