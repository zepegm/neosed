import win32com.client
import pythoncom
from MySQL import db

meses = {'01':'janeiro', '02':'fevereiro', '03':'março', '04':'abril', '05':'maio', '06':'junho', '07':'julho', '08':'agosto', '09':'setembro', '10':'outubro', '11':'novembro', '12':'dezembro'}

banco = db({'host':"localhost",    # your host, usually localhost
            'user':"root",         # your username
            'passwd':"Yasmin",  # your password
            'db':"neosed"})


alunos = banco.executarConsulta('select ra_aluno, rm, nome, sexo, nascimento, rg from vinculo_alunos_turmas inner join aluno on vinculo_alunos_turmas.ra_aluno = aluno.ra where num_classe = 277539060 and serie = 3 and situacao = 1 order by nome')
app = win32com.client.Dispatch("PowerPoint.Application", pythoncom.CoInitialize())

for aluno in alunos:
    nome_assinatura = aluno['nome'].title().replace('Da ', 'da ').replace('Do ', 'do ').replace('De ', 'de ').replace('Dos ', 'dos ')
    data_extensa = aluno['nascimento'].strftime("%d") + ' de ' + meses[aluno['nascimento'].strftime("%m")] + ' de ' + aluno['nascimento'].strftime('%Y')

    pronome = 'a'

    if aluno['sexo'] == 'M':
        pronome = 'o'

    # agora é a parte chata, preciso pegar a cidade
    print('----------------------------------')
    print('RM: %s' % aluno['rm'])
    print(aluno['nome'])
    cidade = input('Digite o nome da cidade: ')

    total = app.ActivePresentation.Slides.Count

    app.ActivePresentation.Slides(total).Duplicate()

    app.ActivePresentation.Slides(total).Shapes(12).TextFrame.TextRange.Characters(113).Text = cidade
    app.ActivePresentation.Slides(total).Shapes(12).TextFrame.TextRange.Characters(99).Text = data_extensa
    app.ActivePresentation.Slides(total).Shapes(12).TextFrame.TextRange.Characters(94).Text = pronome
    app.ActivePresentation.Slides(total).Shapes(12).TextFrame.TextRange.Characters(85).Text = aluno['nome']

    app.ActivePresentation.Slides(total).Shapes(23).TextFrame.TextRange.Characters(17).Text = aluno['rg']
    app.ActivePresentation.Slides(total).Shapes(23).TextFrame.TextRange.Characters(12).Text = nome_assinatura


#info = banco.executarConsulta('select nome, sexo, nascimento, rg from aluno where ra = %s' % ra)[0]
#info['nome_assinatura'] = info['nome'].title().replace('Da ', 'da ').replace('Do ', 'do ').replace('De ', 'de ').replace('Dos ', 'dos ')
#info['data_extensa'] = info['nascimento'].strftime("%d") + ' de ' + meses[info['nascimento'].strftime("%m")] + ' de ' + info['nascimento'].strftime('%Y')
#info['cidade'] = 'Cachoeira Paulista'

#if info['sexo'] == 'M':
    #info['pronome'] = 'o'
#else:
    #info['pronome'] = 'a'

#print(info)

# tentativa de acessar o PowerPoint





