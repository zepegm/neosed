from MySQL import db
from excel import xls

ra_aluno = 110609949

estados = {'SP':'SÃO PAULO', 'RJ':'RIO DE JANEIRO'}

linhas_disc = {1100:22, 1400:25, 1813:23, 1900:24, 2100:31, 2200:32, 2300:33, 2400:27, 2600:28, 2700:26, 2800:29, 3100:30, 8427:38, 8441:35, 8465:43, 8466:36, 8467:25, 8566:37, 8567:39}
linhas_if = {50094:45, 50095:46, 50096:47, 50097:48, 50000:50, 50001:51, 50002:52, 50003:53, 50074:45, 50075:46, 50076:47, 50077:48, 50078:49, 50079:50, 50080:51, 50081:52, 50082:53, 50083:54}
carga_if = {50094:40, 50095:40, 50096:80, 50097:40, 50000:40, 50001:40, 50002:80, 50003:40, 50074:40, 50075:40, 50076:40, 50077:40, 50078:40, 50079:40, 50080:40, 50081:40, 50082:40, 50083:40}

planilha = xls() # formar conexão com a planilha

banco = db({'host':"localhost",    # your host, usually localhost
            'user':"root",         # your username
            'passwd':"Yasmin",  # your password
            'db':"neosed"})

# pegar notas de 2023
notas_bimestrais = banco.executarConsulta('select disciplina, media from conceito_final inner join turma on conceito_final.num_classe = turma.num_classe and turma.ano = 2023 where ra_aluno = %s order by disciplina' % ra_aluno)
notas_if = banco.executarConsulta('select disciplinas.descricao, disciplina, media from conceito_final inner join turma_if on conceito_final.num_classe = turma_if.num_classe and turma_if.ano = 2023 inner join disciplinas on disciplinas.codigo_disciplina = disciplina where ra_aluno = %s order by disciplina' % ra_aluno)

nome_ifs = banco.executarConsulta('select nome_turma from turma_if inner join vinculo_alunos_if on vinculo_alunos_if.num_classe_if = turma_if.num_classe and vinculo_alunos_if.ra_aluno = %s where ano = 2023 order by matricula' % ra_aluno)

nome_if_2024 = banco.executarConsulta('select nome_turma, num_classe, categoria_itinerario.descricao from turma_if inner join categoria_itinerario on categoria_itinerario.id = turma_if.categoria inner join vinculo_alunos_if on vinculo_alunos_if.num_classe_if = turma_if.num_classe and vinculo_alunos_if.ra_aluno = %s where ano = 2024 order by matricula' % ra_aluno)[0]

disc_ifs = banco.executarConsulta('select disciplina, disciplinas.descricao from notas inner join disciplinas on disciplinas.codigo_disciplina = notas.disciplina where ra_aluno = %s and num_classe = %s group by disciplina' % (ra_aluno, nome_if_2024['num_classe']))

planilha.setValCell('E55', nome_if_2024['descricao'])

for item in notas_bimestrais:
    linha = linhas_disc[item['disciplina']]

    planilha.setValCell('R%s' % linha, item['media'])

planilha.setValCell('E45', nome_ifs[0]['nome_turma'].replace('UC1 - Trad. H. Cult.', ' UC1 - Tradições e heranças culturais'))
planilha.setValCell('E50', nome_ifs[1]['nome_turma'].replace('Sust.', 'Sustentável').replace('UC2 - A Tecn. nas Narrat.', 'UC2 - A tecnologia nas narrativas das relações sociais'))


for item in notas_if:
    linha = linhas_if[item['disciplina']]

    planilha.setValCell('H%s' % linha, item['descricao'])
    planilha.setValCell('R%s' % linha, item['media'])
    planilha.setValCell('S%s' % linha, carga_if[item['disciplina']])


#pegar notas de 2022
notas_bimestrais = banco.executarConsulta('select disciplina, media from conceito_final inner join turma on conceito_final.num_classe = turma.num_classe and turma.ano = 2022 where ra_aluno = %s order by disciplina' % ra_aluno)
for item in notas_bimestrais:
    linha = linhas_disc[item['disciplina']]

    planilha.setValCell('P%s' % linha, item['media'])

# pegar dados do DB
dados = banco.executarConsulta(r"select nome, rg, DATE_FORMAT(nascimento, '%d/%m/%Y') AS nascimento, " + '''concat(LPAD(SUBSTR(ra, -9, 1), 1, 0), SUBSTR(ra, -8, 2), ".", substr(ra, -6, 3), ".", substr(ra, -3, 3), "-", digito_ra) as ra from aluno where ra = %s''' % ra_aluno)[0]
planilha.setValCell("E14", dados['nome'])
planilha.setValCell("E15", dados['rg'])
planilha.setValCell("P15", dados['ra'])
planilha.setValCell("G16", dados['nascimento'])


# escrever os nomes das disciplinas
linha = 55

for item in disc_ifs:
    planilha.setValCell('H%s' % linha, item['descricao'])

    if item['descricao'] == 'Tecnologia e Robótica':
        planilha.setValCell('U%s' % linha, 160)
    else:
        planilha.setValCell('U%s' % linha, 80)

    linha += 1