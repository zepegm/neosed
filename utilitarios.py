meses = ['JANEIRO', 'FEVEREIRO', 'MARÇO', 'ABRIL', 'MAIO', 'JUNHO', 'JULHO', 'AGOSTO', 'SETEMBRO', 'OUTUBRO', 'NOVEMBRO', 'DEZEMBRO']

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