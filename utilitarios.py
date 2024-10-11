from datetime import datetime

meses = ['JANEIRO', 'FEVEREIRO', 'MARÇO', 'ABRIL', 'MAIO', 'JUNHO', 'JULHO', 'AGOSTO', 'SETEMBRO', 'OUTUBRO', 'NOVEMBRO', 'DEZEMBRO']
series_fund = {9:'6º ano', 10:'7º ano', 11:'8º ano', 12:'9º ano'}

def converterLista(lista):
    texto = ""
    aux = 0
    on = False

    for item in lista:
        if (texto == ''):
            texto += str(item)
            aux = int(item)
        else:
            if (on):
                if (int(item) != (aux + 1)):
                    on = False
                    texto += str(aux) + "," + str(item)
            else:
                if (int(item) == (aux + 1)):
                    on = True
                    texto += "-"
                else:
                    texto += "," + str(item)

            aux = int(item)

    if (on):
        texto += str(aux)

    return texto

def getMes(mes):
    id = int(mes) - 1
    return meses[id]


def hojePorExtenso():
    hoje = datetime.today()

    return "%s de %s de %s" % (hoje.day, meses[hoje.month - 1].lower(), hoje.year)

def getAnoFund(serie):
    return series_fund[serie]