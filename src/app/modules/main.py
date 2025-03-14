def main():
    global gui
    cl = sys.argv[1:]
    dima.start()

    cli.load_history()
    if cl:
        cli.process(' '.join(cl))
    else:
        gui = GUI()
        gui.start()

if __name__ == "__main__":
    lib_path = utils.projects_dir + "venv/lib/"
    packages_path = lib_path + os.listdir(lib_path)[0] + "/site-packages"
    sys.path.append(packages_path)

    import psycopg2, netifaces, requests, sass, markdown
    from ruamel import yaml

    yaml.constructor.SafeConstructor.add_constructor(u'tag:yaml.org,2002:map', utils.webs.construct_yaml_map)

    main()
