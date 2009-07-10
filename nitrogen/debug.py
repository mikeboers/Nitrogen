def socket():
    import pdb
    import socket
    import sys
    import io
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 9000))
    stdin = io.open(sock.fileno(), 'rb')
    stdout = io.open(sock.fileno(), 'wb')
    pdb.Pdb(stdin=stdin, stdout=stdout).set_trace()