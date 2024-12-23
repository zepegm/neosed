from MySQL import db
from excel import xls

disciplinas = {1100:22, 1900:24, 2100:31, 2200:32, 2600:28, 2700:26, 8427:38, 8441:35, 52000:40, 52001:41, 52002:42, 52005:39}
disciplinas_if = {50423:55, 50424:56, 50425:57, 50426:58, 50427:55, 50428:56, 50429:57, 50430:58, 50431:59}

planilha = xls() # formar conexão com a planilha

banco = db({'host':"localhost",    # your host, usually localhost
            'user':"root",         # your username
            'passwd':"Yasmin",  # your password
            'db':"neosed"})

ra = planilha.getValCell("P15").replace('.', '')[0:9]

notas = banco.executarConsulta('select disciplina, media from conceito_final inner join turma on turma.ano = 2024 and turma.num_classe = conceito_final.num_classe and ra_aluno = %s' % ra)

for item in notas:
    linha = disciplinas[item['disciplina']]
    planilha.setValCell("T%s" % linha, item['media'])

notas_if = banco.executarConsulta('select disciplina, media from conceito_final inner join turma_if on turma_if.ano = 2024 and turma_if.num_classe = conceito_final.num_classe and ra_aluno = %s' % ra)

for item in notas_if:
    linha = disciplinas_if[item['disciplina']]
    planilha.setValCell("T%s" % linha, item['media'])