import select

import sock


class Socket_io(object):
    def __init__(self, ipport):
        try:
            self.sik = sock.sock(sock.AF_INET, sock.SOCK_DGRAM)
            self.sik.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEPORT, 1)
            self.sik.setblocking(0)
            self.sik.bind(("", ipport))

        except Exception, e:
            msg = "Exception: Can't open Socket: %s" % (e)
            print msg
            sys.exit(1)

    def recv_event_pkt(self):
        try:
            available = select.select([self.sik], [], [], 1)
            if available[0]:
                recv = self.sik.recvfrom(2048)
                return recv

        except Exception, e:
            msg = "Exception: Can't recvfrom: %s" % (e)
            print msg

        return ["", ""]

    def close(self):
        self.sik.close()