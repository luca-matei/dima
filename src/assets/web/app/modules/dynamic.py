class lmDynamic:
    def solve_placeholders(self, html):
        log(lm.request.endpoint)
        if lm.autho.has_session():
            user_drop = lm.static.fetch_fraction("user-drop")
        else:
            user_drop = utils.format_tpl(lm.static.fetch_fraction("guest-drop"), {
                "checked": "checked" if True else "",
                "endpoint": '/'.join(lm.request.endpoint[1:])
                })

        html = utils.format_tpl(html, {
            "user_drop": user_drop,
            })

        return html

lm.dynamic = lmDynamic()
