from MySQL import db
from excel import xls

linhas_disc = {1100:22, 1400:23, 8467:23, 1813:24, 1900:25, 2100:31, 2200:30, 2300:33, 2400:29, 2600:28, 2700:26, 2800:27, 3100:32, 50428:37, 50429:36, 50430:38}

planilha = xls() # formar conexão com a planilha
banco = db({'host':"localhost",    # your host, usually localhost
            'user':"root",         # your username
            'passwd':"Yasmin",  # your password
            'db':"neosed"})


print(planilha.getValCell('A1'))  # testar a conexão com a planilha

#ra_aluno = planilha.getValCell("P15").split('-')[0].replace('.','').strip()

#notas_1serie = banco.executarConsulta(f'''select disciplina, media from conceito_final inner join turma on conceito_final.num_classe = turma.num_classe and turma.ano = 2024 inner join vinculo_alunos_turmas on vinculo_alunos_turmas.num_classe = conceito_final.num_classe and vinculo_alunos_turmas.ra_aluno = conceito_final.ra_aluno and serie = 1 where conceito_final.ra_aluno = {ra_aluno} order by disciplina''')
#notas_2serie = banco.executarConsulta(f'''select disciplina, media from conceito_final inner join turma on conceito_final.num_classe = turma.num_classe and turma.ano = 2024 inner join vinculo_alunos_turmas on vinculo_alunos_turmas.num_classe = conceito_final.num_classe and vinculo_alunos_turmas.ra_aluno = conceito_final.ra_aluno and serie = 2 where conceito_final.ra_aluno = {ra_aluno} order by disciplina''')

#for item in notas_1serie:
    #planilha.setValCell('P'+str(linhas_disc[item['disciplina']]), item['media'])

#for item in notas_2serie:
    #planilha.setValCell('R'+str(linhas_disc[item['disciplina']]), item['media'])