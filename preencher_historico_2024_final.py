from MySQL import db
from excel import xls

linhas_disc = {1100:22, 1400:25, 1813:23, 1900:24, 2100:31, 2200:32, 2300:33, 2400:27, 2600:28, 2700:26, 2800:29, 3100:30, 8427:38, 8441:35, 8465:43, 8466:36, 8467:25, 8566:37, 8567:39, 52000:40, 52001:41, 52002:42, 52005:39}
linhas_if = {50094:45, 50095:46, 50096:47, 50097:48, 50000:50, 50001:51, 50002:52, 50003:53, 50074:45, 50075:46, 50076:47, 50077:48, 50078:49, 50079:50, 50080:51, 50081:52, 50082:53, 50083:54}
carga_if = {50427:80, 50428:80, 50429:80, 50430:80, 50431:80, 50423:160, 50424:80, 50425:80, 50426:80}

planilha = xls() # formar conexão com a planilha
banco = db({'host':"localhost",    # your host, usually localhost
            'user':"root",         # your username
            'passwd':"admin",  # your password
            'db':"neosed"})

ra_aluno = planilha.getValCell("P15").split('-')[0].replace('.','').strip()

notas = banco.executarConsulta('select disciplina, media from conceito_final inner join turma on conceito_final.num_classe = turma.num_classe and turma.ano = 2024 where ra_aluno = %s order by disciplina' % ra_aluno)

for item in notas:
    planilha.setValCell('T'+str(linhas_disc[item['disciplina']]), item['media'])


notas_if = banco.executarConsulta('select disciplinas.descricao, disciplina, media from conceito_final inner join turma_if on conceito_final.num_classe = turma_if.num_classe and turma_if.ano = 2024 inner join disciplinas on disciplinas.codigo_disciplina = disciplina where ra_aluno = %s order by disciplina' % ra_aluno)

linha = 55

for item in notas_if:
    planilha.setValCell(f'H{linha}', item['descricao'])
    planilha.setValCell(f'T{linha}', item['media'])
    planilha.setValCell(f'U{linha}', carga_if[item['disciplina']])
    linha += 1