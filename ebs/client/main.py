

from twisted.internet import reactor
from .core import ClientCore


def main():
    client = ClientCore()
    reactor.callWhenRunning(client.start)
    reactor.run()


if __name__ == '__main__':
    main()
