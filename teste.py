from excel import xls

estrutura = xls()

total = int(estrutura.getCountA("Lista Piloto", "J9:J1000")) + 9
lista = []

for i in range(9, total):

    try :
        ra = estrutura.getValCell("Lista Piloto", "J%i" % i)
        sexo = estrutura.getValCell("Lista Piloto", "F%i" % i)
        rm = int(estrutura.getValCell("Lista Piloto", "B%i" % i))
    except:
        ra = 0
        sexo = "-"
        rm = 0

    print(rm)

    if 'float' in str(type(ra)):
        ra = str(int(ra))[:-1]

    lista.append({'ra':ra, 'sexo':sexo, 'rm':rm})

print(lista)