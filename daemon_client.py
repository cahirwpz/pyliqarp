def PoliqarpDaemonClientTest():
    """ Przykładowe użycie klasy PoliqarpDaemonClientTest. """
    if len(sys.argv) != 2:
        print "Usage:", sys.argv[0], "\"query\""
        sys.exit(0)

    corpus = PoliqarpDaemonClient()

    if not corpus.connect("localhost", 4567):
        sys.exit(0)

    corpus.session_begin()

    if corpus.session_configure("../frek/frek"):
        answers = corpus.query(sys.argv[1], 20000)

        print "Got %d answers for query \'%s\':\n" % (len(answers), sys.argv[1])

        for i in range(len(answers)):
            answer = answers[i]

            print "%d: \033[1;32m%s\033[0m %s \033[1;32m%s\033[0m\n" % (i + 1, join(answer.lctx), join([answer[j].pretty() for j in range(len(answer))]) , join(answer.rctx))

    corpus.close()


