class lmDynamic:
    def solve_placeholders(self, html):
        if lm.autho.has_session():
            user_drop = lm.static.fetch_fraction("user-drop")
        else:
            user_drop = utils.format_tpl(lm.static.fetch_fraction("guest-drop"), {
                "checked": "" if lm.request.lang == lm.default_lang else "checked",
                "endpoint": '/'.join(lm.request.endpoint[1:])
                })

        html = utils.format_tpl(html, {
            "user_drop": user_drop,
            })

        return html

lm.dynamic = lmDynamic()
