import os, ast, json, random, re, string, pprint, psycopg2, inspect, pprint
from datetime import datetime

class Utils:
    localhost = "127.0.0.1"
    abc = string.ascii_lowercase

    hal_dir = "/home/hal/"
    logs_dir = hal_dir + "logs/"
    projects_dir = hal_dir + "projects/"
    res_dir = hal_dir + "res/"
    tmp_dir = hal_dir + "tmp/"

    def __init__(self):
        self.src_dir = self.get_src_dir()

    def get_src_dir(self):
        file_path = os.path.dirname(os.path.abspath(__file__))
        return file_path.split('src')[0] + 'src/'

    def get_keys(self, d):
        return list(d.keys())

    def get_values(self, d):
        return list(d.values())

    def reverse_dict(self, d):
        return {y:x for x, y in d.items()}

    def now(self):
        return datetime.now().strftime("%d %b, %H:%M:%S")

    def read(self, path, lines=False):
        is_ast = path.endswith('.ast')
        is_json = path.endswith('.json')

        with open(path, mode='r', encoding='utf-8') as f:
            if is_ast:
                return ast.literal_eval(f.read())
            elif is_json:
                if f: return json.loads(f)
                else: return ""
            elif lines:
                return f.readlines()
            else:
                return f.read()

    def write(self, path, content, lines=False, mode='w', owner=""):
        with open(path, mode=mode, encoding='utf-8') as f:
            if lines:
                f.writelines(content)
            else:
                if path.endswith(".ast"):
                    pprint.pprint(content, stream=f)
                else:
                    f.write(content)

    def normalize_url(self, url):
        return url.lower()

utils = Utils()
