def construct_yaml_map(self, node):
    data = []
    yield data
    for key_node, value_node in node.value:
        key = self.construct_object(key_node, deep=True)
        val = self.construct_object(value_node, deep=True)
        data.append((key, val))

class YML2HTML:
    html = ""

    def __init__(self, yml, default_lang, lang):
        self.default_lang = default_lang
        self.lang = lang

        yaml.constructor.SafeConstructor.add_constructor(u'tag:yaml.org,2002:map', construct_yaml_map)
        data = yaml.YAML(typ="safe").load(yml)
        self.html = self.solve_children(data)

    def solve_children(self, data):
        # Data is a list of HTML boxes
        html = ""

        for box in data:
            tag = box[0]
            properties = box[1]

            attrs = []
            box_html = ""
            text = ""

            if properties != None:
                for prop in properties:
                    if prop[0] == "children":
                        box_html = self.solve_children(prop[1])

                    # Placeholders
                    elif prop[0] == "global-text":
                        text = prop[1]

                    elif prop[0] == "text":
                        texts = dict(prop[1])
                        text = texts.get(self.lang, texts.get(self.default_lang))

                        if tag not in ("a", "i", "button", "span"):
                            text = utils.md2html(text)

                    else:
                        attrs.append(list(prop))

            attrs = dict(attrs)

            custom = attrs.pop("custom", "")
            tag_attrs = ' '.join([f"{k}='{v}'" for k, v in attrs.items()])

            if tag == "placeholder":
                open_tag = ""
                close_tag = ""
            else:
                open_tag = f"<{tag}{' ' if tag_attrs else ''}{tag_attrs}{' ' if custom else ''}{custom}>"

                if tag in ("meta", "link"):
                    open_tag = open_tag[:-1]
                    close_tag = " />"
                elif tag in ("base", "input", "br", "hr"):
                    close_tag = ""
                else:
                    close_tag = f"</{tag}>"

            html += open_tag + text + box_html + close_tag

        return html
