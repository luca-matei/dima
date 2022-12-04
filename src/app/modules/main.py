def main():
    cl = sys.argv[1:]
    hal.start()

    if cl: hal.cli.process(' '.join(cl))
    else: hal.cli.start()

if __name__ == "__main__":
    main()
