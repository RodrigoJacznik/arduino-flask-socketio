
from socket_wrapp import Socket
from protocol import (BaseClient, GET_OP_NORMAL, ALL_SOURCES, SUS_OP_CONS,
                      RESP_TIPO_OK, RESP_TIPO_FAIL, RESP_CODIGO_101,
                      RESP_CODIGO_104
                      )


class Consumidor(BaseClient):
    def __init__(self, sock=None):
        if sock is None:
            sock = Socket()
        BaseClient.__init__(self,sock)

    def request_sources(self):
        self.send_get(GET_OP_NORMAL, ALL_SOURCES)
        tipo, codigo, datos = self.recive_response()
        if (tipo != RESP_TIPO_FAIL):
            return datos.decode().strip().split(";")
        return []

    def select_source(self, idSource):
        self.send_sus(SUS_OP_CONS, idSource)
        tipo, codigo, datos = self.recive_response()
        if (tipo == RESP_TIPO_OK and codigo == RESP_CODIGO_101):
            self.id = int(datos)
            return True
        return False

    def start_stream(self, op, idSource, tm_inicio=0, tm_fin=0):
        self.send_get(op, idSource, tm_inicio, tm_fin)
        tipo, codigo, datos = self.recive_response()
        while (tipo == RESP_TIPO_OK and codigo == RESP_CODIGO_104):
            yield datos
            tipo, codigo, datos = self.recive_response()


if __name__ == '__main__':
    
    cons = Consumidor(Socket())
    cons.connect_server("127.0.0.1", 8888)
    datos = []

    sources = ['\t'.join(data.split(',')) for data in cons.request_sources()]

    print("\n".join(sources))
    selected_source = input(">> Select a source: ")
    if (cons.select_source(selected_source)):
        for dato in cons.start_stream(GET_OP_NORMAL, 1):
            datos.append(dato)
    print(datos)
