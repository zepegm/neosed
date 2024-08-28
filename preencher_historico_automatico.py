from excel import xls
from MySQL import db

planilha = xls() # formar conexão com a planilha
banco = db({'host':"localhost",    # your host, usually localhost
            'user':"root",         # your username
            'passwd':"Yasmin",  # your password
            'db':"neosed"})

serie = planilha.getValCell("V19") # pegar série

t4em = {1100:22, 1400:23, 8467:23, 8567:23, 52005:23, 1813:24, 1900:25, 2700:26, 2800:27, 2600:28, 2400:29, 2200:30, 2100:31, 3100:32, 2300:33, 50428:39, 50429:40, 50430:41}

match serie:
    case '4º Termo':
        # pegar todas as séries dos alunos
        ra_aluno = int(planilha.getValCell('P15').replace('.', '')[:-2])
        notas = banco.executarConsulta('select disciplina, media, serie from conceito_final inner join vinculo_alunos_turmas on vinculo_alunos_turmas.ra_aluno = conceito_final.ra_aluno and conceito_final.num_classe = vinculo_alunos_turmas.num_classe where conceito_final.ra_aluno = %s order by serie, disciplina' % ra_aluno)
        
        for nota in notas:

            coluna = 'A'

            match nota['serie']:
                case 1:
                    coluna = 'P'
                case 2:
                    coluna = 'R'
                case 3:
                    coluna = 'T'
                case 4:
                    coluna = 'V'

            endereco = '%s%s' % (coluna, t4em[nota['disciplina']])
            planilha.setValCell(endereco, nota['media'])

            

