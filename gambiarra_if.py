from MySQL import db
from excel import xls

banco = db({'host':"localhost",    # your host, usually localhost
            'user':"root",         # your username
            'passwd':"admin",  # your password
            'db':"neosed"})

plan = xls('2B-IF.xlsx')
mapao = xls('MAPÃO.xls')

def segundo_bim(num_classe_serie, num_classe_if):
    print('teste')
    # vou percorrer a planilha
    for i in range(71, 127):
        numero = plan.getValCell('Itinerário Formativo', 'A' + str(i))
        # descobrir ra do aluno
        
        ra = banco.executarConsulta('select ra_aluno from vinculo_alunos_turmas where num_classe = %s and num_chamada = %s' % (num_classe_serie, numero))

        #print(ra)

        if (len(ra) > 0):
            ra = ra[0]['ra_aluno']
            # agora vou descobrir esse número na chamada
            num_chamada_if = banco.executarConsulta('select num_chamada from vinculo_alunos_if where num_classe_if = %s and ra_aluno = %s' % (num_classe_if, ra))
            print('select num_chamada from vinculo_alunos_if where num_classe_if = %s and ra_aluno = %s' % (num_classe_if, ra))
            
            print(num_chamada_if)

            if (len(num_chamada_if) > 0):
                num_chamada_if = num_chamada_if[0]['num_chamada']
                
                # agora preciso localizar o número na tabela
                linha = 16
                print(linha)
                lupa = False

                while (not lupa):
                    if num_chamada_if == mapao.getValCell('Mapão', 'B' + str(linha)):
                        lupa = True
                    else:
                        linha += 1

                # agora que tenho a linha campeã preciso passar o rodo nas notas
                col_original = 3
                col_destino = 2
                col_destino = 17

                for u in range(1, 6):
                    valor = mapao.getValCellNumbes('Mapão', 'A1', linha, col_original)
                    plan.setValCellNumbers('Itinerário Formativo', 'A1', valor, i, col_destino) 
                    col_original += 1
                    col_destino += 1

                    valor = mapao.getValCellNumbes('Mapão', 'A1', linha, col_original)

                    if (valor == "-"):
                        valor = '0'

                    plan.setValCellNumbers('Itinerário Formativo', 'A1', valor, i, col_destino) 
                    col_original += 1
                    col_destino += 1
                    valor = mapao.getValCellNumbes('Mapão', 'A1', linha, col_original)
                    plan.setValCellNumbers('Itinerário Formativo', 'A1', valor, i, col_destino) 

                    col_original += 3
                    col_destino += 1                
                
            

def quinto_conceito(num_classe_serie, num_classe_if):
    # vou percorrer a planilha
    for i in range(136, 191 ):
        numero = plan.getValCell('Itinerário Formativo', 'A' + str(i))
        # descobrir ra do aluno
        ra = banco.executarConsulta('select ra_aluno from vinculo_alunos_turmas where num_classe = %s and num_chamada = %s' % (num_classe_serie, numero))
        if (len(ra) > 0):
            ra = ra[0]['ra_aluno']
            # agora vou descobrir esse número na chamada
            num_chamada_if = banco.executarConsulta('select num_chamada from vinculo_alunos_if where num_classe_if = %s and ra_aluno = %s' % (num_classe_if, ra))
            
            if (len(num_chamada_if) > 0):
                num_chamada_if = num_chamada_if[0]['num_chamada']
                
                # agora preciso localizar o número na tabela
                linha = 16
                lupa = False

                while (not lupa):
                    if num_chamada_if == mapao.getValCell('Mapão', 'B' + str(linha)):
                        lupa = True
                    else:
                        linha += 1

                # agora que tenho a linha campeã preciso passar o rodo nas notas
                col_original = 3
                col_destino = 2
                col_destino = 17

                for u in range(1, 6):
                    valor = mapao.getValCellNumbes('Mapão', 'A1', linha, col_original)
                    plan.setValCellNumbers('Itinerário Formativo', 'A1', valor, i, col_destino) 
                    col_original += 3
                    col_destino += 3


print('afs')
#segundo_bim(271089518, 272705245)
quinto_conceito(271089518, 272705245)
