def main():
    cl = sys.argv[1:]
    hal.start()

    if cl: cli.process(' '.join(cl))
    else: cli.start()

if __name__ == "__main__":
    main()
