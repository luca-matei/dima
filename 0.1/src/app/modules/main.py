def main():
    cl = sys.argv[1:]
    app.start()

    if cl:
        print("No interface")
        #cli.process(' '.join(cl))
    else:
        print("CLI")
        #cli.start()

if __name__ == "__main__":
    main()
