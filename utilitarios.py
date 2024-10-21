from datetime import datetime

meses = ['JANEIRO', 'FEVEREIRO', 'MARÇO', 'ABRIL', 'MAIO', 'JUNHO', 'JULHO', 'AGOSTO', 'SETEMBRO', 'OUTUBRO', 'NOVEMBRO', 'DEZEMBRO']
series_fund = {9:'6º ano', 10:'7º ano', 11:'8º ano', 12:'9º ano'}
situacoes = {'ATIVO':1, 'BXTR':2, 'TRAN':2, 'REMA':3, 'NCFP':5, 'NCOM':5, 'CONCL':8, 'APROVADO':6, 'RETIDO FREQ.':10, 'RETIDO REND.':10, 'RECL':15, 'ENCERRADA':16}

def getSituacao(descricao):
    return situacoes[descricao]

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

def converterDataMySQL(data_original):
    return data_original[-4:] + '-' + data_original[3:5] + '-' +  data_original[:2]