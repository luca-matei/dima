class YML2HTML:
    start_html = ""
    end_html = ""
    indent_width = 4
    box_indent = 0
    html = ""
    tags = "div", "a", "i", "span", "button", "noscript",
    attributes = "id", "class", "href",

    def __init__(self, yml, default_lang, lang):
        self.yml = yml.split('\n')
        self.default_lang = default_lang
        self.lang = lang

        self.lines = self.yml_lines()
        self.html = self.solve_box()
        #log(self.html)

    def yml_lines(self):
        line_index = 0
        while line_index < len(self.yml):
            line = self.yml[line_index]
            line_index += 1

            if not line or line.startswith("#"):
                continue
            else:
                yield line

    def solve_line(self, line):
        stripped_line = line.lstrip(' ')
        split_line = re.findall(r'(?:[^\s:"]|"(?:\\.|[^"])*")+', stripped_line)

        key = split_line[0]

        if len(split_line) == 2:
            value = split_line[1].strip()    # To do: Remove comments
        else:
            value = ""

        return int((len(line) - len(stripped_line)) / self.indent_width), key, value

    def create_tag(self, box):
        open_tag = "<"
        open_tag += box["tag"]

        for attr in self.attributes:
            if box.get(attr):
                open_tag += f' {attr}=' + box[attr]

        open_tag += ">"

        if box.get("text"):
            open_tag += box["text"]

        close_tag = f'</{box["tag"]}>'
        return open_tag, close_tag

    def solve_box(self, current_indent=None, key=None, value=None):
        box = {}
        html = ""
        stop = False
        children = False

        if not key:
            current_indent, key, value = self.solve_line(next(self.lines))

        self.box_indent = current_indent
        box["tag"] = key

        current_indent, key, value = self.solve_line(next(self.lines))
        while key not in self.tags and not stop:
            if key == "text":
                texts = {}
                while key not in self.attributes + self.tags:
                    try:
                        current_indent, key, value = self.solve_line(next(self.lines))
                    except StopIteration:
                        stop = True
                        break

                    texts[key] = value.strip('"')

                text = texts.get(self.lang, texts.get(self.default_lang))
                if box["tag"] in ("a", "button",):
                    box["text"] = text
                else:
                    box["text"] = MD2HTML(text).html

            elif key in self.attributes:
                box[key] = value

            elif key == "children":
                open_tag, close_tag = self.create_tag(box)
                html += open_tag + self.solve_box() + close_tag
                children = True

            if key not in self.tags and not stop:
                try:
                    current_indent, key, value = self.solve_line(next(self.lines))
                except StopIteration:
                    stop = True
                    break

        if not children:
            open_tag, close_tag = self.create_tag(box)
            html = open_tag + html + close_tag

        if current_indent == self.box_indent and not stop:
            html += self.solve_box(current_indent, key, value)

        return html
