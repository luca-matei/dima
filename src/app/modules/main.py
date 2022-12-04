def main():
    cl = sys.argv[1:]
    hal.start()

    if cl:
        print("No interface")
        hal.cli.process(' '.join(cl))
    else:
        print("CLI")
        hal.cli.start()

if __name__ == "__main__":
    main()
