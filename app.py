#import locale
from MySQL import db
from getInfoSED import buscarCPF
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, Response
from waitress import serve
from datetime import datetime
from werkzeug.utils import secure_filename
from excel import xls, open_xls
from utilitarios import converterLista
import pandas as pd
import os
import csv
import json
from pyppeteer import launch
import locale
import math
import calendar

locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')

UPLOAD_FOLDER = os.path.join('staticFiles', 'uploads')

# vou ver se consigo abrir certinho
app=Flask(__name__)
app.secret_key = "abc123"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'justasecretkeythatishouldputhere'


#locale.setlocale(locale.LC_ALL, "")

banco = db({'host':"localhost",    # your host, usually localhost
            'user':"root",         # your username
            'passwd':"Yasmin",  # your password
            'db':"neosed"})


home_directory = os.path.expanduser( '~' )
aux_info = None

@app.route('/', methods=['GET', 'POST'])
def index():

    msg = ""
    ano = datetime.now().year
    #ano = 2023

    if request.method == 'POST':

        if 'cbAno' in request.form:
            ano = int(request.form['cbAno'])

        if 'txtnumeroclasse_if_edit' in request.form:
            turma_if = {'num_classe':request.form['txtnumeroclasse_if_edit']}
            turma_if['nome_turma'] = "'" + request.form['txtnometurma_if_edit'] + "'"
            turma_if['duracao'] = request.form['cbduracao_if_edit']
            turma_if['tipo_ensino'] = request.form['cbtipoensino_if_edit']
            turma_if['categoria'] = request.form['cbcategoria_if_edit']
            turma_if['periodo'] = request.form['cbperiodo_if_edit']

            vinculos = request.form.getlist('turmas_vinculo_if_edit')
            #print(vinculos)

            banco.alterarTurmaIf(turma_if, vinculos)

        if 'txtnumeroclasse_if' in request.form:

            turma_if = {'num_classe':request.form['txtnumeroclasse_if']}
            turma_if['nome_turma'] = "'" + request.form['txtnometurma_if'] + "'"
            turma_if['duracao'] = request.form['cbduracao_if']
            turma_if['tipo_ensino'] = request.form['cbtipoensino_if']
            turma_if['categoria'] = request.form['cbcategoria_if']
            turma_if['periodo'] = request.form['cbperiodo_if']
            turma_if['ano'] = ano

            vinculos = request.form.getlist('turmas_vinculo_if')

            if banco.inserirNovaTurmaIf(turma_if, vinculos):
                msg = '<div class="alert alert-success alert-dismissible fade show" role="alert">' \
                        '<strong>Operação bem-sucedida!</strong> Turma IF <strong>' + request.form['txtnometurma_if'] + '</strong> inserida com sucesso!' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'  
            else:
                msg = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' \
                        '<strong>Atenção!</strong> Erro ao tentar inserir turma, verifique se já não existe uma turma com o número de classe nº "<strong>' + turma_if['num_classe'] + '"</strong>.' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'       

        #print('yes')
        if 'txtnumeroclasse' in request.form:

            classe = {'num_classe':request.form['txtnumeroclasse'], 'nome_turma':"'" + request.form['txtnometurma'] + "'", 'duracao':request.form['cbduracao'], 'tipo_ensino':request.form['cbtipoensino'], 'periodo':request.form['cbperiodo'], 'ano':ano}
            
            if banco.inserirNovaTurma(classe):
                msg = '<div class="alert alert-success alert-dismissible fade show" role="alert">' \
                        '<strong>Operação bem-sucedida!</strong> Turma <strong>' + request.form['txtnometurma'] + '</strong> inserida com sucesso!' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'
            else:
                msg = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' \
                        '<strong>Atenção!</strong> Erro ao tentar inserir turma, verifique se já não existe uma turma com o número de classe nº "<strong>' + classe['num_classe'] + '"</strong>.' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'


        if 'txtnumeroclasse_edit' in request.form:
            classe = {'num_classe':request.form['txtnumeroclasse_edit'], 'nome_turma':"'" + request.form['txtnometurma_edit'] + "'", 'duracao':request.form['cbduracao_edit'], 'tipo_ensino':request.form['cbtipoensino_edit'], 'periodo':request.form['cbperiodo_edit']}
            
            if banco.alterarTurma(classe):
                msg = '<div class="alert alert-success alert-dismissible fade show" role="alert">' \
                        '<strong>Operação bem-sucedida!</strong> Dados da Turma <strong>' + request.form['txtnometurma_edit'] + '</strong> alterados com sucesso!' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'
            else:
                msg = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' \
                        '<strong>Atenção!</strong> Erro ao tentar alterar dados de turma, verifique se foi tudo digitado corretamente.' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'

    calendario = banco.executarConsulta(r"select DATE_FORMAT(1bim_inicio,'%d/%m/%Y') as 1sem_inicio, DATE_FORMAT(2bim_fim,'%d/%m/%Y') as 1sem_fim, DATE_FORMAT(3bim_inicio,'%d/%m/%Y') as 2sem_inicio, DATE_FORMAT(4bim_fim,'%d/%m/%Y') as 2sem_fim from calendario id where ano = " + str(ano))
    duracao = banco.executarConsulta('select * from duracao order by id')
    tipo_ensino = banco.executarConsulta('select * from tipo_ensino where id <> 2 and id <> 5 order by id')
    tipo_ensino_itinerario = banco.executarConsulta('select * from tipo_ensino where id = 2 or id = 5 order by id')
    periodo = banco.executarConsulta('select * from periodo order by id')
    listaTipos = banco.executarConsulta('select tipo_ensino.id, tipo_ensino.descricao as tipo_ensino, if (count(turma.tipo_ensino) > 0, count(turma.tipo_ensino), count(turma_if.tipo_ensino)) as total from tipo_ensino LEFT JOIN turma ON turma.tipo_ensino = tipo_ensino.id LEFT JOIN turma_if ON turma_if.tipo_ensino = tipo_ensino.id where turma.ano = %s or turma_if.ano = %s GROUP BY id order by id' % (ano, ano))
    cat_itinerario = banco.executarConsulta('select * from categoria_itinerario')

    anos = banco.executarConsulta('select ano from calendario order by ano desc')
    aux = []
    for y in anos:
        if int(y['ano']) == ano:
            aux.append({'ano':y['ano'], 'selected':'selected'})
        else:
            aux.append({'ano':y['ano'], 'selected':''})

    anos = aux

    listaTurmas = []
    print(listaTipos)
    for item in listaTipos:
        
        if item['total'] > 0:

            color = 'table-dark'

            if item['id'] != 2 and item['id'] != 5:
                turmas = banco.executarConsulta('select num_classe, nome_turma, duracao.descricao as duracao, turma.duracao as id_duracao, turma.tipo_ensino as id_ensino, periodo.descricao as periodo, turma.periodo as id_periodo from turma INNER JOIN duracao ON duracao.id = turma.duracao INNER JOIN periodo ON periodo.id = turma.periodo where tipo_ensino = %s and ano = %s order by duracao, nome_turma' % (item['id'], ano))
            else:
                turmas = banco.executarConsulta('select num_classe, nome_turma, duracao.descricao as duracao, turma_if.duracao as id_duracao, turma_if.tipo_ensino as id_ensino, periodo.descricao as periodo, turma_if.periodo as id_periodo, turma_if.categoria as categoria from turma_if INNER JOIN duracao ON duracao.id = turma_if.duracao INNER JOIN periodo ON periodo.id = turma_if.periodo where tipo_ensino = %s and ano = %s order by duracao, nome_turma' % (item['id'], ano))
                print('select num_classe, nome_turma, duracao.descricao as duracao, turma_if.duracao as id_duracao, turma_if.tipo_ensino as id_ensino, periodo.descricao as periodo, turma_if.periodo as id_periodo, turma_if.categoria as categoria from turma_if INNER JOIN duracao ON duracao.id = turma_if.duracao INNER JOIN periodo ON periodo.id = turma_if.periodo where tipo_ensino = %s and ano = %s order by duracao, nome_turma' % (item['id'], ano))
                color = 'table-primary'
                
            listaTurmas.append({'tipo_ensino':item, 'lista':turmas, 'color':color})



    return render_template('home.jinja', tipo_ensino=tipo_ensino, calendario=calendario[0], duracao=duracao, periodo=periodo, msg=msg, listaTurmas=listaTurmas, tipo_ensino_itinerario=tipo_ensino_itinerario, cat_itinerario=cat_itinerario, anos=anos)


@app.route('/render_conselho_bimestre_all',  methods=['GET', 'POST'])
def render_conselho_bimestre_all():
    if request.method == 'GET':
        bimestre = request.args.getlist('bimestre')[0]
        ano = request.args.getlist('ano')[0]
        dificuldades = banco.executarConsulta("select * from dificuldades")

        final = 'and (duracao = 1 or duracao = 2)'

        if int(bimestre) > 2:
            final = 'and (duracao = 1 or duracao = 3)'

        # pegar todas as turmas
        sql = "select num_classe, nome_turma, duracao.descricao as desc_duracao, periodo.descricao as periodo, tipo_ensino.descricao as tipo_ensino_desc, turma.ano, " + \
             r"CASE WHEN turma.duracao < 3 THEN DATE_FORMAT(1bim_inicio,'%d/%m/%Y') " + \
             r"ELSE DATE_FORMAT(3bim_inicio,'%d/%m/%Y') END as inicio, " + \
             r"CASE WHEN turma.duracao = 1 OR turma.duracao = 3 THEN DATE_FORMAT(4bim_fim,'%d/%m/%Y') " + \
             r"ELSE DATE_FORMAT(2bim_fim,'%d/%m/%Y') END as fim " + \
              "from turma " + \
              "inner join periodo on periodo.id = turma.periodo " + \
              "inner join calendario on turma.ano = calendario.ano " + \
              "inner join duracao on turma.duracao = duracao.id " + \
              "inner join tipo_ensino on tipo_ensino.id = turma.tipo_ensino " + \
              "where turma.ano = %s %s order by tipo_ensino, nome_turma" % (ano, final)
        print(sql)
        
        turmas = banco.executarConsulta(sql)

        inicio = str(banco.executarConsultaVetor('select %sbim_inicio from calendario where ano = (select ano from turma where num_classe = 280612383)' % bimestre)[0])
        fim = str(banco.executarConsultaVetor('select %sbim_fim from calendario where ano = (select ano from turma where num_classe = 280612383)' % bimestre)[0])

        top = 2278
        limite = 1124

        # listar turma por turma
        for turma in turmas:
            # pegar os alunos da turma
            sql = 'SELECT ' + \
                "num_chamada as num, ifnull(aluno.rm, '-') as rm, serie, aluno.nome, " + \
                'concat(LPAD(SUBSTR(ra_aluno, -9, 1), 1, 0), SUBSTR(ra_aluno, -8, 2), ".", substr(ra_aluno, -6, 3), ".", substr(ra_aluno, -3, 3), "-", aluno.digito_ra) as ra, ' + \
                "ra_aluno as ra_bruto, " + \
                "if(fim_mat <= '" + fim  + "', situacao.abv1, if(matricula > '" + inicio  + r"', DATE_FORMAT(matricula,'%d/%m/%Y'), '')) as mat, " + \
                "if(fim_mat <= '" + fim  + r"', DATE_FORMAT(fim_mat,'%d/%m/%Y'), '') as fim_mat, " + \
                "ifnull((SELECT group_concat(dificuldade) from alunos_dificuldades where num_classe = %s and bimestre = %s and ra = aluno.ra), '') as dificuldade, " % (turma['num_classe'], bimestre) + \
                '(select sum(falta) from notas where ra_aluno = ra_bruto and bimestre = %s and num_classe = %s) as total_faltas, ' % (bimestre, turma['num_classe']) + \
                'round(100 - ((select sum(falta) from notas where ra_aluno = ra_bruto and bimestre = %s and num_classe = %s) * 100 / (select sum(aulas_dadas) from  vinculo_prof_disc where bimestre = %s and num_classe = %s)), 0) as freq, ' % (bimestre, turma['num_classe'], bimestre, turma['num_classe']) + \
                '(select sum(ac) from notas where ra_aluno = ra_bruto and bimestre = %s and num_classe = %s) as ac ' % (bimestre, turma['num_classe']) + \
                "from vinculo_alunos_turmas " + \
                'inner join aluno ON aluno.ra = vinculo_alunos_turmas.ra_aluno ' + \
                'inner join situacao ON vinculo_alunos_turmas.situacao = situacao.id ' + \
                "where num_classe = %s and matricula <= '%s' order by num_chamada" % (turma['num_classe'], fim)
            
            turma['alunos'] = banco.executarConsulta(sql)

            total = {}
            ativos = 0
            maximo = 0

            for aluno in turma['alunos']:
                aluno['nome'] = aluno['nome'].title().replace('Da ', 'da ').replace("De ", "de ").replace("Do ", 'do ').replace("Dos ", 'dos ') 

                if aluno['fim_mat'] == '':
                    ativos += 1
                maximo += 1
                if (aluno['dificuldade'] != ''):
                    lista = aluno['dificuldade'].split(',')
                    aluno['dificuldade'] = converterLista(lista)
                    
                    #print(aluno)

            total['total_ativos'] = ativos
            total['total'] = maximo

            turma['total'] = total

            # pegar as notas da turma
            disciplinas = banco.executarConsulta('select professor.nome_ata, disciplina, disciplinas.abv as desc_disc, disciplinas.descricao as completo, aulas_dadas from vinculo_prof_disc inner join professor on professor.rg = vinculo_prof_disc.rg_prof inner join disciplinas ON disciplinas.codigo_disciplina = vinculo_prof_disc.disciplina  where bimestre = %s and num_classe = %s order by disciplina' % (bimestre, turma['num_classe']))

            for item in disciplinas:
                sql = 'select ' + \
                        "vinculo_alunos_turmas.ra_aluno, vinculo_alunos_turmas.num_chamada as num, nota, falta, if(ac!=0, ac, '-') as ac " + \
                        'from notas ' + \
                        'inner join vinculo_alunos_turmas on vinculo_alunos_turmas.ra_aluno = notas.ra_aluno and vinculo_alunos_turmas.num_classe = notas.num_classe ' + \
                        "where disciplina = %s and notas.num_classe = %s and bimestre = %s order by num_chamada" % (item['disciplina'], turma['num_classe'], bimestre)
            
                lista = {}
                notas = banco.executarConsulta(sql)

                for aluno in notas:
                    lista[aluno['ra_aluno']] = aluno

                item['notas'] = lista

            turma['disciplinas'] = disciplinas

            # pegar a data final da ata
            sql = 'select %sbim_fim as fim from calendario where ano = (select ano from turma where num_classe = %s)' % (bimestre, turma['num_classe'])
            try:
                fim_bimestre = banco.executarConsulta(sql)[0]['fim']
            except:
                sql = 'select %sbim_fim as fim from calendario where ano = (select ano from turma_if where num_classe = %s)' % (bimestre, turma['num_classe'])
                fim_bimestre = banco.executarConsulta(sql)[0]['fim']

            turma['fim_bimestre'] = fim_bimestre
            turma['top'] = top
            top += limite
            turma['top_mapao'] = top
            top += limite
            turma['top_verso'] = top
            top += limite
            turma['top_blank'] = top
            top += limite

            # verificar se existe IF nessa turma
            turmas_if = []
            colspan_if = 0

            turmas_if = banco.executarConsulta('select num_classe_if from vinculo_if where num_classe_em = %s' % turma['num_classe'])
            
            if len(turmas_if) > 0: # implica que existe Itinerário

                turma['top_mapao_if'] = top
                top += limite
                turma['top_verso_if'] = top
                top += limite
                
                turmas_if_concat = banco.executarConsulta("select group_concat(num_classe_if SEPARATOR ', ') as classes_if from vinculo_if where num_classe_em = %s" % turma['num_classe'])[0]['classes_if']
                
                for aluno in turma['alunos']: # buscar pela nota IF individual de cada aluno
                    notas_if = {}

                    for itf in turmas_if:
                        notas = banco.executarConsulta('select * from notas where ra_aluno = %s and num_classe = %s and bimestre = %s' % (aluno['ra_bruto'], itf['num_classe_if'], bimestre))
                        
                        for n in notas:
                            notas_if[n['disciplina']] = {'nota':n['nota'], 'falta':n['falta'], 'ac':n['ac']}

                    aluno['if'] = notas_if

                    sql = 'select ' + \
	                      'sum(falta) as total_faltas_if, ' + \
                          'sum(ac) as total_ac_if, ' + \
                          'round(100 - ((select sum(falta) from notas where ra_aluno = ' + str(aluno['ra_bruto']) + ' and bimestre = ' + str(bimestre) + ' and num_classe in (' + turmas_if_concat + ')) * 100 / (select sum(aulas_dadas) from vinculo_prof_disc where bimestre = ' + str(bimestre) + ' and num_classe =  (select num_classe from notas where ra_aluno = ' + str(aluno['ra_bruto']) + ' and bimestre = ' + str(bimestre) + ' and num_classe in (' + turmas_if_concat + ') group by(num_classe)))), 0) as freq_if ' + \
                          'from notas ' + \
                          'where num_classe in (' + turmas_if_concat + ') and bimestre = ' + str(bimestre) + ' and ra_aluno = ' + str(aluno['ra_bruto'])

                    freq_if = banco.executarConsulta(sql)[0]
                    
                    aluno['freq_if'] = freq_if

                for item in turmas_if:
                    item['nome'] = banco.executarConsultaVetor('select nome_turma from turma_if where num_classe = %s' % item['num_classe_if'])[0]

                    sql = 'select ' + \
                        'notas.disciplina, ' + \
                        'disciplinas.descricao, ' + \
                        'disciplinas.abv, ' + \
                        '(select aulas_dadas from vinculo_prof_disc where bimestre = notas.bimestre and disciplina = notas.disciplina and num_classe = notas.num_classe) as aulas_dadas, ' + \
                        '(select nome_ata from professor where rg = (select rg_prof from vinculo_prof_disc where bimestre = notas.bimestre and disciplina = notas.disciplina and num_classe = notas.num_classe )) as professor ' + \
                        'from notas ' + \
                        'inner join disciplinas on disciplinas.codigo_disciplina = disciplina ' + \
                        'where notas.bimestre = %s and notas.num_classe = %s ' % (bimestre, item['num_classe_if']) + \
                        'group by disciplina '

                    item['disciplinas'] = banco.executarConsulta(sql)
                    colspan_if += len(item['disciplinas'])   

            turma['turmas_if'] = turmas_if
            turma['colspan_if'] = colspan_if

        return render_template('render_pdf/render_conselho_bimestre_all.jinja', turmas=turmas, dificuldades=dificuldades, bimestre=bimestre, ano=ano)

@app.route('/render_conselho_bimestre',  methods=['GET', 'POST'])
def render_conselho_bimestre():
    if request.method == 'GET':
        bimestre = request.args.getlist('bimestre')[0]
        num_classe = request.args.getlist('num_classe')[0]
        tipo = 'padrao'

        inicio = str(banco.executarConsultaVetor('select %sbim_inicio from calendario where ano = (select ano from turma where num_classe = 280612383)' % bimestre)[0])
        fim = str(banco.executarConsultaVetor('select %sbim_fim from calendario where ano = (select ano from turma where num_classe = 280612383)' % bimestre)[0])

        sql = 'SELECT ' + \
                "num_chamada as num, ifnull(aluno.rm, '-') as rm, serie, aluno.nome, " + \
                'concat(LPAD(SUBSTR(ra_aluno, -9, 1), 1, 0), SUBSTR(ra_aluno, -8, 2), ".", substr(ra_aluno, -6, 3), ".", substr(ra_aluno, -3, 3), "-", aluno.digito_ra) as ra, ' + \
                "ra_aluno as ra_bruto, " + \
                "if(fim_mat <= '" + fim  + "', situacao.abv1, if(matricula > '" + inicio  + r"', DATE_FORMAT(matricula,'%d/%m/%Y'), '')) as mat, " + \
                "if(fim_mat <= '" + fim  + r"', DATE_FORMAT(fim_mat,'%d/%m/%Y'), '') as fim_mat, " + \
                "ifnull((SELECT group_concat(dificuldade) from alunos_dificuldades where num_classe = " + num_classe + " and bimestre = " + bimestre + " and ra = aluno.ra), '') as dificuldade, " + \
                '(select sum(falta) from notas where ra_aluno = ra_bruto and bimestre = ' + bimestre + ' and num_classe = ' + num_classe + ') as total_faltas, ' + \
                'round(100 - ((select sum(falta) from notas where ra_aluno = ra_bruto and bimestre = ' + bimestre + ' and num_classe = ' + num_classe + ') * 100 / (select sum(aulas_dadas) from  vinculo_prof_disc where bimestre = ' + bimestre + ' and num_classe = ' + num_classe + ')), 0) as freq, ' + \
                '(select sum(ac) from notas where ra_aluno = ra_bruto and bimestre = ' + bimestre + ' and num_classe = ' + num_classe + ') as ac ' + \
                "from vinculo_alunos_turmas " + \
                'inner join aluno ON aluno.ra = vinculo_alunos_turmas.ra_aluno ' + \
                'inner join situacao ON vinculo_alunos_turmas.situacao = situacao.id ' + \
                "where num_classe = " + num_classe  + " and matricula <= '" + fim  + "' order by num_chamada"

        alunos = banco.executarConsulta(sql)
        #print(alunos)

        if (len(alunos) < 1):
            sql = 'SELECT ' + \
                "num_chamada as num, ifnull(aluno.rm, '-') as rm, aluno.nome, " + \
                'concat(LPAD(SUBSTR(ra_aluno, -9, 1), 1, 0), SUBSTR(ra_aluno, -8, 2), ".", substr(ra_aluno, -6, 3), ".", substr(ra_aluno, -3, 3), "-", aluno.digito_ra) as ra, ' + \
                "ra_aluno as ra_bruto, " + \
                "if(fim_mat < '" + fim  + "', situacao.abv1, if(matricula > '" + inicio  + r"', DATE_FORMAT(matricula,'%d/%m/%Y'), '')) as mat, " + \
                "if(fim_mat < '" + fim  + r"', DATE_FORMAT(fim_mat,'%d/%m/%Y'), '') as fim_mat, " + \
                "ifnull((SELECT group_concat(dificuldade) from alunos_dificuldades where num_classe_if = " + num_classe + " and bimestre = " + bimestre + " and ra = aluno.ra), '') as dificuldade, " + \
                '(select sum(falta) from notas where ra_aluno = ra_bruto and bimestre = ' + bimestre + ' and num_classe = ' + num_classe + ') as total_faltas, ' + \
                'round(100 - ((select sum(falta) from notas where ra_aluno = ra_bruto and bimestre = ' + bimestre + ' and num_classe = ' + num_classe + ') * 100 / (select sum(aulas_dadas) from  vinculo_prof_disc where bimestre = ' + bimestre + ' and num_classe = ' + num_classe + ')), 0) as freq, ' + \
                '(select sum(ac) from notas where ra_aluno = ra_bruto and bimestre = ' + bimestre + ' and num_classe = ' + num_classe + ') as ac ' + \
                "from vinculo_alunos_if " + \
                'inner join aluno ON aluno.ra = vinculo_alunos_if.ra_aluno ' + \
                'inner join situacao ON vinculo_alunos_if.situacao = situacao.id ' + \
                "where num_classe_if = " + num_classe  + " and matricula <= '" + fim  + "' order by num_chamada"

            #print(sql)
            alunos = banco.executarConsulta(sql)
            tipo = 'if'

        for item in alunos:
            item['nome'] = item['nome'].title().replace('Da ', 'da ').replace("De ", "de ").replace("Do ", 'do ').replace("Dos ", 'dos ')            

        total = {}
        ativos = 0
        maximo = 0
        for aluno in alunos:
            if aluno['fim_mat'] == '':
                ativos += 1
            maximo += 1
            if (aluno['dificuldade'] != ''):
                lista = aluno['dificuldade'].split(',')
                aluno['dificuldade'] = converterLista(lista)
                
                #print(aluno)

        total['total_ativos'] = ativos
        total['total'] = maximo

        print(total)

        sql = 'SELECT ' + \
                'num_classe, nome_turma, duracao.descricao as desc_duracao, periodo.descricao as periodo, tipo_ensino.descricao as tipo_ensino, turma.ano, ' + \
                r"CASE WHEN turma.duracao < 3 THEN DATE_FORMAT(1bim_inicio,'%d/%m/%Y')" + \
                r"ELSE DATE_FORMAT(3bim_inicio,'%d/%m/%Y') END as inicio, " + \
                r"CASE WHEN turma.duracao = 1 OR turma.duracao = 3 THEN DATE_FORMAT(4bim_fim,'%d/%m/%Y')" + \
                r"ELSE DATE_FORMAT(2bim_fim,'%d/%m/%Y') END as fim " + \
                "from turma " + \
                "inner join periodo on periodo.id = turma.periodo " + \
                "inner join calendario on turma.ano = calendario.ano " + \
                "inner join duracao on turma.duracao = duracao.id " + \
                "inner join tipo_ensino on tipo_ensino.id = turma.tipo_ensino " + \
                  "where num_classe = " + num_classe
            
        turma = banco.executarConsulta(sql)

        if (len(turma) < 1):
            sql = 'SELECT ' + \
                'num_classe, nome_turma, duracao.descricao as desc_duracao, periodo.descricao as periodo, tipo_ensino.descricao as tipo_ensino, turma_if.ano, ' + \
                r"CASE WHEN turma_if.duracao < 3 THEN DATE_FORMAT(1bim_inicio,'%d/%m/%Y')" + \
                r"ELSE DATE_FORMAT(3bim_inicio,'%d/%m/%Y') END as inicio, " + \
                r"CASE WHEN turma_if.duracao = 1 OR turma_if.duracao = 3 THEN DATE_FORMAT(4bim_fim,'%d/%m/%Y')" + \
                r"ELSE DATE_FORMAT(2bim_fim,'%d/%m/%Y') END as fim " + \
                "from turma_if " + \
                "inner join periodo on periodo.id = turma_if.periodo " + \
                "inner join calendario on turma_if.ano = calendario.ano " + \
                "inner join duracao on turma_if.duracao = duracao.id " + \
                "inner join tipo_ensino on tipo_ensino.id = turma_if.tipo_ensino " + \
                "where num_classe = " + num_classe
                
            turma = banco.executarConsulta(sql)  

        turma = turma[0]              

        disciplinas = banco.executarConsulta('select professor.nome_ata, disciplina, disciplinas.abv as desc_disc, disciplinas.descricao as completo, aulas_dadas from vinculo_prof_disc inner join professor on professor.rg = vinculo_prof_disc.rg_prof inner join disciplinas ON disciplinas.codigo_disciplina = vinculo_prof_disc.disciplina  where bimestre = %s and num_classe = %s order by disciplina' % (bimestre, num_classe))

        for item in disciplinas:
            sql = 'select ' + \
                    "vinculo_alunos_turmas.ra_aluno, vinculo_alunos_turmas.num_chamada as num, nota, falta, if(ac!=0, ac, '-') as ac " + \
                    'from notas ' + \
                    'inner join vinculo_alunos_turmas on vinculo_alunos_turmas.ra_aluno = notas.ra_aluno and vinculo_alunos_turmas.num_classe = notas.num_classe ' + \
                    "where disciplina = %s and notas.num_classe = %s and bimestre = %s order by num_chamada" % (item['disciplina'], num_classe, bimestre)
            
            lista = {}
            notas = banco.executarConsulta(sql)


            if (len(notas) < 1):
                sql = 'select ' + \
                    "vinculo_alunos_if.ra_aluno, vinculo_alunos_if.num_chamada as num, nota, falta, if(ac!=0, ac, '-') as ac " + \
                    'from notas ' + \
                    'inner join vinculo_alunos_if on vinculo_alunos_if.ra_aluno = notas.ra_aluno and vinculo_alunos_if.num_classe_if = notas.num_classe ' + \
                    "where disciplina = %s and notas.num_classe = %s and bimestre = %s order by num_chamada" % (item['disciplina'], num_classe, bimestre)
                                                                                                                
                notas = banco.executarConsulta(sql)

            for aluno in notas:
                lista[aluno['ra_aluno']] = aluno

            item['notas'] = lista

            sql = 'select ' + \
                    'ra_aluno, sum(falta) as total_faltas, ' + \
                    'sum(ac) as ac, ' + \
                    'round(100 - (sum(falta) / (select sum(aulas_dadas) from vinculo_prof_disc where bimestre = %s and num_classe = %s) * 100)) as freq ' % (bimestre, num_classe) + \
                    'from notas where num_classe = %s and bimestre = %s group by ra_aluno' % (num_classe, bimestre)




        lista_freq = {}
        freq = banco.executarConsulta(sql)
        for aluno in freq:
            lista_freq[aluno['ra_aluno']] = aluno

        #print(disciplinas)
        #print(alunos)
        #print(turma)
        #print(disciplinas)
        #print(freq)

        sql = 'select %sbim_fim as fim from calendario where ano = (select ano from turma where num_classe = %s)' % (bimestre, num_classe)
        try:
            fim_bimestre = banco.executarConsulta(sql)[0]['fim']
        except:
            sql = 'select %sbim_fim as fim from calendario where ano = (select ano from turma_if where num_classe = %s)' % (bimestre, num_classe)
            fim_bimestre = banco.executarConsulta(sql)[0]['fim']

        dificuldades = banco.executarConsulta("select * from dificuldades")

        # verificar se existe itinerário formativo e se existir puxar as notas dele

        turmas_if = []
        colspan_if = 0

        if tipo == 'padrao':
            turmas_if = banco.executarConsulta('select num_classe_if from vinculo_if where num_classe_em = %s' % num_classe)
            
            if len(turmas_if) > 0: # implica que existe Itinerário
                
                turmas_if_concat = banco.executarConsulta("select group_concat(num_classe_if SEPARATOR ', ') as classes_if from vinculo_if where num_classe_em = %s" % num_classe)[0]['classes_if']
                
                for aluno in alunos: # buscar pela nota IF individual de cada aluno
                    notas_if = {}

                    for itf in turmas_if:
                        notas = banco.executarConsulta('select * from notas where ra_aluno = %s and num_classe = %s and bimestre = %s' % (aluno['ra_bruto'], itf['num_classe_if'], bimestre))
                        
                        for n in notas:
                            notas_if[n['disciplina']] = {'nota':n['nota'], 'falta':n['falta'], 'ac':n['ac']}

                    aluno['if'] = notas_if

                    sql = 'select ' + \
	                      'sum(falta) as total_faltas_if, ' + \
                          'sum(ac) as total_ac_if, ' + \
                          'round(100 - ((select sum(falta) from notas where ra_aluno = ' + str(aluno['ra_bruto']) + ' and bimestre = ' + str(bimestre) + ' and num_classe in (' + turmas_if_concat + ')) * 100 / (select sum(aulas_dadas) from vinculo_prof_disc where bimestre = ' + str(bimestre) + ' and num_classe =  (select num_classe from notas where ra_aluno = ' + str(aluno['ra_bruto']) + ' and bimestre = ' + str(bimestre) + ' and num_classe in (' + turmas_if_concat + ') group by(num_classe)))), 0) as freq_if ' + \
                          'from notas ' + \
                          'where num_classe in (' + turmas_if_concat + ') and bimestre = ' + str(bimestre) + ' and ra_aluno = ' + str(aluno['ra_bruto'])
                    print(sql)

                    freq_if = banco.executarConsulta(sql)[0]
                    
                    aluno['freq_if'] = freq_if

            for item in turmas_if:
                item['nome'] = banco.executarConsultaVetor('select nome_turma from turma_if where num_classe = %s' % item['num_classe_if'])[0]

                sql = 'select ' + \
	                  'notas.disciplina, ' + \
                      'disciplinas.descricao, ' + \
                      'disciplinas.abv, ' + \
	                  '(select aulas_dadas from vinculo_prof_disc where bimestre = notas.bimestre and disciplina = notas.disciplina and num_classe = notas.num_classe) as aulas_dadas, ' + \
                      '(select nome_ata from professor where rg = (select rg_prof from vinculo_prof_disc where bimestre = notas.bimestre and disciplina = notas.disciplina and num_classe = notas.num_classe )) as professor ' + \
                      'from notas ' + \
                      'inner join disciplinas on disciplinas.codigo_disciplina = disciplina ' + \
                       'where notas.bimestre = %s and notas.num_classe = %s ' % (bimestre, item['num_classe_if']) + \
                       'group by disciplina '

                item['disciplinas'] = banco.executarConsulta(sql)
                colspan_if += len(item['disciplinas'])

        return render_template('render_pdf/render_conselho_bimestre.jinja', alunos=alunos, turma=turma, disciplinas=disciplinas, freq=freq, total=total, bimestre=bimestre, fim_bimestre=fim_bimestre, dificuldades=dificuldades, turmas_if=turmas_if, colspan_if=colspan_if)

@app.route('/render_lista', methods=['GET', 'POST'])
def render_lista():

    if request.method == 'GET':
        tipo = request.args.getlist('tipo')[0]
        num_classe = request.args.getlist('num_classe')[0]
        
        if tipo == 'turma':
            head = banco.executarConsulta('select ' + \
	                                      'num_classe, nome_turma, periodo.descricao as periodo, tipo_ensino.descricao as tipo_ensino, duracao.descricao as duracao, ' + \
                                          'CASE ' + \
                                          r"WHEN duracao = 1 THEN concat((select DATE_FORMAT(`1bim_inicio`, '%d/%m/%Y') from calendario where ano = turma.ano), ' até ', (select DATE_FORMAT(`4bim_fim`, '%d/%m/%Y') from calendario where ano = turma.ano)) " + \
                                          r"WHEN duracao = 2 THEN concat((select DATE_FORMAT(`1bim_inicio`, '%d/%m/%Y') from calendario where ano = turma.ano), ' até ', (select DATE_FORMAT(`2bim_fim`, '%d/%m/%Y') from calendario where ano = turma.ano)) " + \
                                          r"WHEN duracao = 3 THEN concat((select DATE_FORMAT(`3bim_inicio`, '%d/%m/%Y') from calendario where ano = turma.ano), ' até ', (select DATE_FORMAT(`4bim_fim`, '%d/%m/%Y') from calendario where ano = turma.ano)) " + \
	                                      "END as duracao_tempo, " + \
                                          r"DATE_FORMAT(now(), '%d/%m/%Y') as hoje, " + \
                                          "CASE " + \
                                          r"WHEN duracao = 1 THEN IF((select `4bim_fim` from calendario where ano = turma.ano) > now(), 'andamento', 'encerrado')" + \
                                          r"WHEN duracao = 2 THEN IF((select `2bim_fim` from calendario where ano = turma.ano) > now(), 'andamento', 'encerrado')" + \
                                          r"WHEN duracao = 3 THEN IF((select `4bim_fim` from calendario where ano = turma.ano) > now(), 'andamento', 'encerrado')" + \
	                                      "END as status from turma " + \
                                          "inner join periodo on periodo.id = turma.periodo " + \
                                          "inner join tipo_ensino on tipo_ensino.id = turma.tipo_ensino " + \
                                          "inner join duracao on duracao.id = turma.duracao " + \
                                          "where num_classe = %s" % num_classe)[0]

    
            # pegar total
            if head['status'] == 'andamento':
                total = banco.executarConsulta('select (select count(*) from vinculo_alunos_turmas where num_classe = %s) as total, (select count(*) from vinculo_alunos_turmas where num_classe = %s and situacao = 1) as total_ativos' % (num_classe, num_classe))[0]
                desc_total = 'ativos'
            else:
                total = banco.executarConsulta('select (select count(*) from vinculo_alunos_turmas where num_classe = %s) as total, (select count(*) from vinculo_alunos_turmas where num_classe = %s and situacao = 6) as total_ativos' % (num_classe, num_classe))[0]
                desc_total = 'aprovados'

            info = banco.executarConsulta('select ' + \
                                        'CASE ' + \
                                        r"WHEN duracao = 3 THEN (select DATE_FORMAT(`3bim_inicio`, '%Y-%m-%d') from calendario where ano = turma.ano) " + \
                                        r"ELSE (select DATE_FORMAT(`1bim_inicio`, '%Y-%m-%d') from calendario where ano = turma.ano) " + \
                                        'END as inicio, ' + \
                                        'CASE ' + \
                                        r"WHEN duracao = 2 THEN (select DATE_FORMAT(`2bim_fim`, '%Y-%m-%d') from calendario where ano = turma.ano) " + \
                                        r"ELSE (select DATE_FORMAT(`4bim_fim`, '%Y-%m-%d') from calendario where ano = turma.ano) " + \
                                        'END as fim ' + \
                                        'from turma where num_classe = %s' % num_classe)[0]

            alunos =  banco.executarConsulta('SELECT ' + \
                            "num_chamada as num, ifnull(aluno.rm, '-') as rm, aluno.nome, vinculo_alunos_turmas.serie, " + \
                            'concat(LPAD(SUBSTR(ra_aluno, -9, 1), 1, 0), SUBSTR(ra_aluno, -8, 2), ".", substr(ra_aluno, -6, 3), ".", substr(ra_aluno, -3, 3), "-", aluno.digito_ra) as ra, ' + \
                            "if(fim_mat < '" + info['fim']  + "', situacao.abv1, if(matricula > '" + info['inicio']  + r"', DATE_FORMAT(matricula,'%d/%m/%Y'), '')) as mat, " + \
                            "if(fim_mat < '" + info['fim']  + r"', DATE_FORMAT(fim_mat,'%d/%m/%Y'), '') as fim_mat, " + \
                            "DATE_FORMAT(nascimento, '%d/%m/%Y') as nascimento, aluno.sexo, ifnull(rg, '-') as rg, ifnull(concat(LPAD(SUBSTR(cpf, -11, 1), 1, 0), SUBSTR(cpf, -10, 2), '.', substr(cpf, -8, 3), '.', substr(cpf, -5, 3), '-', substr(cpf, -2, 2)), '-') as cpf " + \
                            "from vinculo_alunos_turmas " + \
                            'inner join aluno ON aluno.ra = vinculo_alunos_turmas.ra_aluno ' + \
                            'inner join situacao ON vinculo_alunos_turmas.situacao = situacao.id ' + \
                            "where num_classe = " + num_classe  + " order by num_chamada")

            for item in alunos:
                item['nome'] = item['nome'].title().replace('Da ', 'da ').replace("De ", "de ").replace("Do ", 'do ').replace("Dos ", 'dos ')

            return render_template('render_pdf/render_lista.jinja', head=head, total=total, desc_total=desc_total, alunos=alunos)
        
        elif tipo == 'turma_if':

            # eu estou com o numero do if, precisa pegar todas as classes comuns vinculadas a este if
            classes_regulares = banco.executarConsulta('SELECT num_classe_em, turma.nome_turma FROM vinculo_if INNER JOIN turma ON turma.num_classe = num_classe_em where num_classe_if =  %s' % num_classe)
            classes_if = banco.executarConsulta('select num_classe_if, turma_if.nome_turma from vinculo_if inner join turma_if on turma_if.num_classe = num_classe_if where num_classe_em = %s' % classes_regulares[0]['num_classe_em'])

            class_color = {}
            cont = 1
            for item in classes_regulares:
                class_color[item['nome_turma']] = 'classe_%s' % cont
                cont += 1

            lista = []
            total = []
            lista_final = []
            for classe in classes_if:
                alunos = banco.executarConsulta('select num_chamada, aluno.nome, (select turma.nome_turma from vinculo_alunos_turmas inner join turma on vinculo_alunos_turmas.num_classe = turma.num_classe where ra_aluno = vinculo_alunos_if.ra_aluno and (situacao = 1 or situacao = 6) order by fim_mat desc limit 1) as serie from vinculo_alunos_if inner join aluno on aluno.ra = ra_aluno where num_classe_if = %s and situacao = 1 order by num_chamada' % classe['num_classe_if'])
                
                total.append(len(alunos))

                for aluno in alunos:
                    aluno['nome'] = aluno['nome'].title().replace('Da ', 'da ').replace("De ", "de ").replace("Do ", 'do ').replace("Dos ", 'dos ')

                lista.append(alunos)
                

            for i in range(0, max(total)):
                aux_vec = []
                for item in lista:
                    try:
                        aux_vec.append(item[i])
                    except:
                        aux_vec.append('')

                lista_final.append(aux_vec)

            serie = classes_regulares[0]['nome_turma'].replace(" A", "").replace(" B", '')

            return render_template('render_pdf/render_lista_if.jinja', classes_if=classes_if, serie=serie, lista_final=lista_final, class_color=class_color, classes_regulares=classes_regulares)


        elif tipo == 'declaracao':
            global aux_info
            
            pronome = 'o'
            if aux_info['genero'] == 'f':
                pronome = 'a'

            texto = 'Declaro para os devidos fins que <b>' + aux_info['nome'] + '</b>, RG: ' + aux_info['rg']

            if aux_info['tipo'] == '0':
                titulo = 'DECLARAÇÃO DE ESCOLARIDADE'

                if aux_info['ensino'] == 'Ensino Médio Regular' or aux_info['ensino'] == 'Ensino Fundamental EJA - Multisseriada':
                    pronome_serie = 'na'
                else:
                    pronome_serie = 'no'

                texto += ' foi alun%s regularmente matriculad%s %s <b>%s do %s</b>, no ano letivo de %s, tendo sido considerad%s <b>APROVAD%s.</b>' % (pronome, pronome, pronome_serie, aux_info['serie'], aux_info['ensino'].replace(' Regular', '').replace(' - Multisseriada', '').replace(' - Padrão Antigo', ''), aux_info['ano'], pronome, pronome.upper())
            elif aux_info['tipo'] == '1' or aux_info['tipo'] == '2':

                if aux_info['ensino'] == 'Ensino Médio Regular':
                    fim = 'na <b>%s do Ensino Médio.</b>' % aux_info['serie']
                elif aux_info['ensino'] == 'Ensino Fundamental Regular':
                    fim = 'no <b>%s do Ensino Fundamental.</b>' % aux_info['serie']
                elif aux_info['ensino'] == 'Ensino Médio EJA':
                    fim = 'na <b>%sª série do Ensino Médio.</b>' % aux_info['serie'][0:1]
                    if aux_info['serie'] == '4º Termo':
                        fim = 'no <b>4º Termo (EJA) do Ensino Médio.</b>'
                elif aux_info['ensino'] == 'Ensino Fundamental EJA - Multisseriada':
                    try:
                        fim = 'no <b>%s (%sª série) do Ensino Fundamental.</b>' % (aux_info['serie'][29:35], int(aux_info['serie'][29:30]) - 1)
                    except:
                        fim = 'no <b>%s (%sª série) do Ensino Fundamental.</b>' % (aux_info['serie'][28:34], int(aux_info['serie'][28:29]) - 1)
                elif aux_info['ensino'] == 'Ensino Fundamental EJA - Padrão Antigo':
                    fim = 'no <b>%s (%sª série) do Ensino Fundamental.</b>' % (aux_info['serie'][28:34], int(aux_info['serie'][28:29]) - 1) 

                if aux_info['tipo'] == '1':
                    titulo = 'DECLARAÇÃO DE TRANSFERÊNCIA'
                    texto += ' solicitou transferência com direito a matricular-se %s' % fim
                else:
                    titulo = 'DECLARAÇÃO DE VAGA'
                    texto += ' solicitou vaga %s' % fim

                
            data_atual = datetime.now()
            data_formatada = data_atual.strftime("%d de %B de %Y")

            return render_template('render_pdf/render_declaracao.jinja', texto=texto, titulo=titulo, data=data_formatada, cor=num_classe)

@app.route('/gerar_pdf', methods=['GET', 'POST'])
async def gerar_pdf():
    info = request.json

    if info['destino'] == 1:
        pdf_path = 'static/docs/lista.pdf'

        browser = await launch(
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False
        )

        page = await browser.newPage()
        await page.goto('http://localhost/render_lista?tipo=%s&num_classe=%s' % (info['tipo'], info['turma']), {'waitUntil':'networkidle2'})
        await page.pdf({'path': pdf_path, 'format':'A4', 'scale':1, 'printBackground':True})
        await browser.close()

        return jsonify(pdf_path)       

    elif info['destino'] == 2:
        print(info)
        pdf_path = 'static/docs/lista.pdf'

        browser = await launch(
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False
        )

        page = await browser.newPage()
        await page.goto('http://localhost/render_lista?tipo=%s&num_classe=%s' % (info['tipo'], info['turma']), {'waitUntil':'networkidle2'})
        await page.pdf({'path': pdf_path, 'format':'A4', 'scale':1, 'printBackground':True})
        await browser.close()

        return jsonify(pdf_path)  

    elif info['destino'] == 3:
        global aux_info
        aux_info = info

        return jsonify(True)

    elif info['destino'] == 4:

        pdf_path = 'static/docs/declaracao.pdf'

        browser = await launch(
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False
        )

        page = await browser.newPage()
        await page.goto('http://localhost/render_lista?tipo=declaracao&num_classe=white')
        await page.pdf({'path': pdf_path, 'format':'A4', 'scale':1, 'printBackground':True})
        await browser.close()

        return jsonify(pdf_path) 
    
    elif info['destino'] == 5: # conselho bimestral
        pdf_path = 'static/docs/conselho.pdf'

        print(info)

        browser = await launch(
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False
        )

        page = await browser.newPage()
        await page.goto('http://localhost/render_conselho_bimestre?bimestre=%s&num_classe=%s' % (info['bimestre'], info['num_classe']), {'waitUntil':'networkidle2'})
        await page.pdf({'path': pdf_path, 'format':'A4', 'scale':1, 'printBackground':True})
        await browser.close()

        return jsonify(pdf_path)  

    elif info['destino'] == 6: # conselho bimestral completo
        pdf_path = 'static/docs/conselho.pdf'

        browser = await launch(
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False
        )

        page = await browser.newPage()
        await page.goto('http://localhost/render_conselho_bimestre_all?bimestre=%s&ano=%s' % (info['bimestre'], info['ano']), {'waitUntil':'networkidle2'})
        await page.pdf({'path': pdf_path, 'format':'A4', 'scale':1, 'printBackground':True})
        await browser.close()

        return jsonify(pdf_path)          


@app.route('/save_dificuldades', methods=['GET', 'POST'])
def save_dificuldades():
    if request.method == "POST":
        if request.is_json:    
            lista = request.json
            
            if len(lista) > 0:
                return jsonify(banco.salvarDificuldades(lista))

@app.route('/getPDFConselhoFinal', methods=['GET', 'POST'])
def getPDFConselhoFinal():
    if request.method == "POST":
        if request.is_json:    
            info = request.json
            #print(info)

            sql = 'SELECT ' + \
                  "num_chamada as num, ifnull(aluno.rm, '-') as rm, serie, aluno.nome, " + \
                  'concat(LPAD(SUBSTR(ra_aluno, -9, 1), 1, 0), SUBSTR(ra_aluno, -8, 2), ".", substr(ra_aluno, -6, 3), ".", substr(ra_aluno, -3, 3), "-", aluno.digito_ra) as ra, ' + \
                  "if(sexo='M', situacao.descricao, situacao.desc_fem) as situacao, situacao.abv1 " + \
                  "from vinculo_alunos_turmas " + \
                  'inner join aluno ON aluno.ra = vinculo_alunos_turmas.ra_aluno ' + \
                  'inner join situacao ON vinculo_alunos_turmas.situacao = situacao.id ' + \
                  "where num_classe = " + info['num_classe']  + " order by num_chamada"

            alunos = banco.executarConsulta(sql)
            #print(alunos)
            #print('------------------')

            if (len(alunos) < 1):
                sql = 'SELECT ' + \
                    "num_chamada as num, ifnull(aluno.rm, '-') as rm, aluno.nome, " + \
                    'concat(LPAD(SUBSTR(ra_aluno, -9, 1), 1, 0), SUBSTR(ra_aluno, -8, 2), ".", substr(ra_aluno, -6, 3), ".", substr(ra_aluno, -3, 3), "-", aluno.digito_ra) as ra, ' + \
                    "if(sexo='M', situacao.descricao, situacao.desc_fem) as situacao, situacao.abv1 " + \
                    "from vinculo_alunos_if " + \
                    'inner join aluno ON aluno.ra = vinculo_alunos_if.ra_aluno ' + \
                    'inner join situacao ON vinculo_alunos_if.situacao = situacao.id ' + \
                    "where num_classe_if = " + info['num_classe']  + " order by num_chamada"

                alunos = banco.executarConsulta(sql)                

            sql = 'SELECT ' + \
	              'num_classe, nome_turma, duracao.descricao as desc_duracao, periodo.descricao as periodo, tipo_ensino.descricao as tipo_ensino, turma.ano, ' + \
                  r"CASE WHEN turma.duracao < 3 THEN DATE_FORMAT(1bim_inicio,'%d/%m/%Y')" + \
                  r"ELSE DATE_FORMAT(3bim_inicio,'%d/%m/%Y') END as inicio, " + \
	              r"CASE WHEN turma.duracao = 1 OR turma.duracao = 3 THEN DATE_FORMAT(4bim_fim,'%d/%m/%Y')" + \
                  r"ELSE DATE_FORMAT(2bim_fim,'%d/%m/%Y') END as fim " + \
                  "from turma " + \
                  "inner join periodo on periodo.id = turma.periodo " + \
                  "inner join calendario on turma.ano = calendario.ano " + \
                  "inner join duracao on turma.duracao = duracao.id " + \
                  "inner join tipo_ensino on tipo_ensino.id = turma.tipo_ensino " + \
                  "where num_classe = " + info['num_classe']
            
            turma = banco.executarConsulta(sql)

            if (len(turma) < 1):
                sql = 'SELECT ' + \
                    'num_classe, nome_turma, duracao.descricao as desc_duracao, periodo.descricao as periodo, tipo_ensino.descricao as tipo_ensino, turma_if.ano, ' + \
                    r"CASE WHEN turma_if.duracao < 3 THEN DATE_FORMAT(1bim_inicio,'%d/%m/%Y')" + \
                    r"ELSE DATE_FORMAT(3bim_inicio,'%d/%m/%Y') END as inicio, " + \
                    r"CASE WHEN turma_if.duracao = 1 OR turma_if.duracao = 3 THEN DATE_FORMAT(4bim_fim,'%d/%m/%Y')" + \
                    r"ELSE DATE_FORMAT(2bim_fim,'%d/%m/%Y') END as fim " + \
                    "from turma_if " + \
                    "inner join periodo on periodo.id = turma_if.periodo " + \
                    "inner join calendario on turma_if.ano = calendario.ano " + \
                    "inner join duracao on turma_if.duracao = duracao.id " + \
                    "inner join tipo_ensino on tipo_ensino.id = turma_if.tipo_ensino " + \
                    "where num_classe = " + info['num_classe']
                
                turma = banco.executarConsulta(sql)                
            #print(turma)
            #print('------------------')

            turma = turma[0]

            disciplinas = banco.executarConsulta('select professor.nome_ata, disciplina, disciplinas.abv as desc_disc, disciplinas.descricao as completo from vinculo_prof_disc inner join professor on professor.rg = vinculo_prof_disc.rg_prof inner join disciplinas ON disciplinas.codigo_disciplina = vinculo_prof_disc.disciplina  where bimestre = %s and num_classe = %s order by disciplina' % (info['bimestre'], info['num_classe']))

            #print(disciplinas)

            # parei aqui
            for item in disciplinas:
                sql = 'select ' + \
	                  "vinculo_alunos_turmas.ra_aluno, vinculo_alunos_turmas.num_chamada as num, media " + \
                      'from conceito_final ' + \
                      'inner join vinculo_alunos_turmas on vinculo_alunos_turmas.ra_aluno = conceito_final.ra_aluno and vinculo_alunos_turmas.num_classe = conceito_final.num_classe ' + \
                      "where disciplina = %s and conceito_final.num_classe = %s order by num_chamada" % (item['disciplina'], info['num_classe'])
                
                notas = banco.executarConsulta(sql)

                if (len(notas) < 1):
                    sql = 'select ' + \
                        "vinculo_alunos_if.ra_aluno, vinculo_alunos_if.num_chamada as num, media " + \
                        'from conceito_final ' + \
                        'inner join vinculo_alunos_if on vinculo_alunos_if.ra_aluno = conceito_final.ra_aluno and vinculo_alunos_if.num_classe_if = conceito_final.num_classe ' + \
                        "where disciplina = %s and conceito_final.num_classe = %s order by num_chamada" % (item['disciplina'], info['num_classe'])
                    
                    notas = banco.executarConsulta(sql)                    

                lista = {}
                for aluno in notas:
                    lista[aluno['ra_aluno']] = aluno

                item['notas'] = lista

                sql = 'select ' + \
	                  'ra_aluno, sum(falta) as total_faltas, ' + \
                      'sum(ac) as ac, ' + \
                      'round(100 - ((sum(falta) - sum(ac)) / (select sum(aulas_dadas) from vinculo_prof_disc where num_classe = %s) * 100)) as freq ' % (info['num_classe']) + \
                      'from notas where num_classe = %s group by ra_aluno' % (info['num_classe'])

                #print(sql)


            lista_freq = {}
            freq = banco.executarConsulta(sql)
            for aluno in freq:
                lista_freq[aluno['ra_aluno']] = aluno

            #print(disciplinas)
            return jsonify({'alunos':alunos, 'turma':turma, 'disciplinas':disciplinas, 'freq':lista_freq})


@app.route('/declaracoes', methods=['GET', 'POST'])
def declaracoes():

    return render_template('declaracoes.jinja')

@app.route('/getPDFListConselho', methods=['GET', 'POST'])
def getPDFListConselho():
    if request.method == "POST":
        if request.is_json:    
            info = request.json
            #print(info)

            sql = 'SELECT ' + \
                  "num_chamada as num, ifnull(aluno.rm, '-') as rm, serie, aluno.nome, " + \
                  'concat(LPAD(SUBSTR(ra_aluno, -9, 1), 1, 0), SUBSTR(ra_aluno, -8, 2), ".", substr(ra_aluno, -6, 3), ".", substr(ra_aluno, -3, 3), "-", aluno.digito_ra) as ra, ' + \
                  "if(fim_mat <= '" + info['fim_bim']  + "', situacao.abv1, if(matricula > '" + info['inicio']  + r"', DATE_FORMAT(matricula,'%d/%m/%Y'), '')) as mat, " + \
                  "if(fim_mat <= '" + info['fim_bim']  + r"', DATE_FORMAT(fim_mat,'%d/%m/%Y'), '') as fim_mat, " + \
                  "ifnull((SELECT group_concat(dificuldade) from alunos_dificuldades where num_classe = " + info['num_classe'] + " and bimestre = " + info['bimestre'] + " and ra = aluno.ra), '') as dificuldade " + \
                  "from vinculo_alunos_turmas " + \
                  'inner join aluno ON aluno.ra = vinculo_alunos_turmas.ra_aluno ' + \
                  'inner join situacao ON vinculo_alunos_turmas.situacao = situacao.id ' + \
                  "where num_classe = " + info['num_classe']  + " and matricula <= '" + info['fim_bim']  + "' order by num_chamada"

            alunos = banco.executarConsulta(sql)

            if (len(alunos) < 1):
                sql = 'SELECT ' + \
                    "num_chamada as num, ifnull(aluno.rm, '-') as rm, aluno.nome, " + \
                    'concat(LPAD(SUBSTR(ra_aluno, -9, 1), 1, 0), SUBSTR(ra_aluno, -8, 2), ".", substr(ra_aluno, -6, 3), ".", substr(ra_aluno, -3, 3), "-", aluno.digito_ra) as ra, ' + \
                    "if(fim_mat < '" + info['fim_bim']  + "', situacao.abv1, if(matricula > '" + info['inicio']  + r"', DATE_FORMAT(matricula,'%d/%m/%Y'), '')) as mat, " + \
                    "if(fim_mat < '" + info['fim_bim']  + r"', DATE_FORMAT(fim_mat,'%d/%m/%Y'), '') as fim_mat, " + \
                    "ifnull((SELECT group_concat(dificuldade) from alunos_dificuldades where bimestre = " + info['bimestre'] + " and ra = aluno.ra), '') as dificuldade " + \
                    "from vinculo_alunos_if " + \
                    'inner join aluno ON aluno.ra = vinculo_alunos_if.ra_aluno ' + \
                    'inner join situacao ON vinculo_alunos_if.situacao = situacao.id ' + \
                    "where num_classe_if = " + info['num_classe']  + " and matricula <= '" + info['fim_bim']  + "' order by num_chamada"

                #print(sql)
                alunos = banco.executarConsulta(sql)                

            for aluno in alunos:
                if (aluno['dificuldade'] != ''):
                    lista = aluno['dificuldade'].split(',')
                    aluno['dificuldade'] = converterLista(lista)
                
                print(aluno)

            sql = 'SELECT ' + \
	              'num_classe, nome_turma, duracao.descricao as desc_duracao, periodo.descricao as periodo, tipo_ensino.descricao as tipo_ensino, turma.ano, ' + \
                  r"CASE WHEN turma.duracao < 3 THEN DATE_FORMAT(1bim_inicio,'%d/%m/%Y')" + \
                  r"ELSE DATE_FORMAT(3bim_inicio,'%d/%m/%Y') END as inicio, " + \
	              r"CASE WHEN turma.duracao = 1 OR turma.duracao = 3 THEN DATE_FORMAT(4bim_fim,'%d/%m/%Y')" + \
                  r"ELSE DATE_FORMAT(2bim_fim,'%d/%m/%Y') END as fim " + \
                  "from turma " + \
                  "inner join periodo on periodo.id = turma.periodo " + \
                  "inner join calendario on turma.ano = calendario.ano " + \
                  "inner join duracao on turma.duracao = duracao.id " + \
                  "inner join tipo_ensino on tipo_ensino.id = turma.tipo_ensino " + \
                  "where num_classe = " + info['num_classe']
            
            turma = banco.executarConsulta(sql)

            if (len(turma) < 1):
                sql = 'SELECT ' + \
                    'num_classe, nome_turma, duracao.descricao as desc_duracao, periodo.descricao as periodo, tipo_ensino.descricao as tipo_ensino, turma_if.ano, ' + \
                    r"CASE WHEN turma_if.duracao < 3 THEN DATE_FORMAT(1bim_inicio,'%d/%m/%Y')" + \
                    r"ELSE DATE_FORMAT(3bim_inicio,'%d/%m/%Y') END as inicio, " + \
                    r"CASE WHEN turma_if.duracao = 1 OR turma_if.duracao = 3 THEN DATE_FORMAT(4bim_fim,'%d/%m/%Y')" + \
                    r"ELSE DATE_FORMAT(2bim_fim,'%d/%m/%Y') END as fim " + \
                    "from turma_if " + \
                    "inner join periodo on periodo.id = turma_if.periodo " + \
                    "inner join calendario on turma_if.ano = calendario.ano " + \
                    "inner join duracao on turma_if.duracao = duracao.id " + \
                    "inner join tipo_ensino on tipo_ensino.id = turma_if.tipo_ensino " + \
                    "where num_classe = " + info['num_classe']
                
                turma = banco.executarConsulta(sql)  

            turma = turma[0]              

            disciplinas = banco.executarConsulta('select professor.nome_ata, disciplina, disciplinas.abv as desc_disc, disciplinas.descricao as completo, aulas_dadas from vinculo_prof_disc inner join professor on professor.rg = vinculo_prof_disc.rg_prof inner join disciplinas ON disciplinas.codigo_disciplina = vinculo_prof_disc.disciplina  where bimestre = %s and num_classe = %s order by disciplina' % (info['bimestre'], info['num_classe']))

            for item in disciplinas:
                sql = 'select ' + \
	                  "vinculo_alunos_turmas.ra_aluno, vinculo_alunos_turmas.num_chamada as num, nota, falta, if(ac!=0, ac, '-') as ac " + \
                      'from notas ' + \
                      'inner join vinculo_alunos_turmas on vinculo_alunos_turmas.ra_aluno = notas.ra_aluno and vinculo_alunos_turmas.num_classe = notas.num_classe ' + \
                      "where disciplina = %s and notas.num_classe = %s and bimestre = %s order by num_chamada" % (item['disciplina'], info['num_classe'], info['bimestre'])
                
                lista = {}
                notas = banco.executarConsulta(sql)


                if (len(notas) < 1):
                    sql = 'select ' + \
                        "vinculo_alunos_if.ra_aluno, vinculo_alunos_if.num_chamada as num, nota, falta, if(ac!=0, ac, '-') as ac " + \
                        'from notas ' + \
                        'inner join vinculo_alunos_if on vinculo_alunos_if.ra_aluno = notas.ra_aluno and vinculo_alunos_if.num_classe_if = notas.num_classe ' + \
                        "where disciplina = %s and notas.num_classe = %s and bimestre = %s order by num_chamada" % (item['disciplina'], info['num_classe'], info['bimestre']  )                  
                                                                                                                    
                    notas = banco.executarConsulta(sql)

                for aluno in notas:
                    lista[aluno['ra_aluno']] = aluno

                item['notas'] = lista

                sql = 'select ' + \
	                  'ra_aluno, sum(falta) as total_faltas, ' + \
                      'sum(ac) as ac, ' + \
                      'round(100 - (sum(falta) / (select sum(aulas_dadas) from vinculo_prof_disc where bimestre = %s and num_classe = %s) * 100)) as freq ' % (info['bimestre'], info['num_classe']) + \
                      'from notas where num_classe = %s and bimestre = %s group by ra_aluno' % (info['num_classe'], info['bimestre'])




            lista_freq = {}
            freq = banco.executarConsulta(sql)
            for aluno in freq:
                lista_freq[aluno['ra_aluno']] = aluno

            #print(disciplinas)
            return jsonify({'alunos':alunos, 'turma':turma, 'disciplinas':disciplinas, 'freq':lista_freq})

@app.route('/getPDFListIf', methods=['GET', 'POST'])
def getPDFListIf():
    if request.method == "POST":
        if request.is_json:
            num_classe = request.json

            # criar meu esquema de cores
            cores = [{'r':0, 'g':32, 'b':96}, {'r':8, 'g':88, 'b':29}, {'r':184, 'g':8, 'b':176}]

            # agora é a parte complicada

            # eu estou com o numero do if, precisa pegar todas as classes comuns vinculadas a este if
            classes_comuns = banco.executarConsulta('SELECT num_classe_em, turma.nome_turma FROM vinculo_if INNER JOIN turma ON turma.num_classe = num_classe_em where num_classe_if =  %s' % num_classe)

            #print(classes_comuns)

            index = 0
            esquema_cores = {}

            if (len(classes_comuns) == 1):
                esquema_cores[classes_comuns[0]['nome_turma']] = {'r':0, 'g':0, 'b':0}

            else:
                for item in classes_comuns:
                    esquema_cores[item['nome_turma']] = cores[index]
                    index += 1

            #print(esquema_cores)


            # agora farei uma consulta reversa e pegarei todas as classes IFs vinculadas a estas duas classes
            sql = "SELECT num_classe_if FROM vinculo_if WHERE num_classe_em IN ("
            for item in classes_comuns:
                sql += str(item['num_classe_em']) +", "

            sql = sql[:-2] + ') GROUP BY num_classe_if'

            #print(sql)

            classes_if = banco.executarConsulta(sql)
            
            #ok, agora que eu tenho as classes, preciso fazer uma consulta geral com todas elas e colocar tudo numa lista
            lista = []

            for item in classes_if:
                sql = "select num_classe, nome_turma, duracao.descricao as duracao, tipo_ensino.descricao as tipo_ensino, categoria_itinerario.descricao as cat_if, periodo.descricao as periodo from turma_if as turma INNER JOIN duracao ON duracao.id = turma.duracao INNER JOIN tipo_ensino ON tipo_ensino.id = turma.tipo_ensino INNER JOIN categoria_itinerario ON categoria_itinerario.id = turma.categoria INNER JOIN periodo ON periodo.id = turma.periodo where num_classe = %s" % item['num_classe_if']
                dados = banco.executarConsulta(sql)[0]
                #total = banco.executarConsulta("select count(*) as total, sum(case when situacao = 1 then 1 else 0 end) as ativos from vinculo_alunos_if where num_classe_if = %s" % item['num_classe_if'])[0]
                
                #sql =   r"SELECT vinculo_alunos_if.num_chamada, ifnull(aluno.rm, '-') as rm, " + \
                        #r'concat(LPAD(SUBSTR(vinculo_alunos_if.ra_aluno, -9, 1), 1, 0), SUBSTR(vinculo_alunos_if.ra_aluno, -8, 2), ".", substr(vinculo_alunos_if.ra_aluno, -6, 3), ".", substr(vinculo_alunos_if.ra_aluno, -3, 3), "-", aluno.digito_ra) as ra, ' + \
                        #"aluno.nome, situacao.abv1 as sit, turma.nome_turma as turma, " + \
                        #r"DATE_FORMAT(vinculo_alunos_if.matricula,'%d/%m/%Y') as matricula, DATE_FORMAT(vinculo_alunos_if.matricula, '%Y-%m-%d') as matricula_original, " + \
                        #r"DATE_FORMAT(vinculo_alunos_if.fim_mat,'%d/%m/%Y') as fim_mat, DATE_FORMAT(vinculo_alunos_if.fim_mat, '%Y-%m-%d') as fim_mat_original " + \
                        #"FROM vinculo_alunos_if INNER JOIN aluno ON aluno.ra = ra_aluno INNER JOIN situacao ON vinculo_alunos_if.situacao = situacao.id LEFT JOIN vinculo_alunos_turmas ON vinculo_alunos_if.ra_aluno = vinculo_alunos_turmas.ra_aluno LEFT JOIN turma ON turma.num_classe = vinculo_alunos_turmas.num_classe " + \
                        #"WHERE vinculo_alunos_if.num_classe_if = %s and vinculo_alunos_turmas.situacao = 1 group by ra ORDER BY num_chamada, vinculo_alunos_turmas.matricula desc" % (item['num_classe_if'])                
                
                sql =   "SELECT	" + \
                        "vinculo_alunos_if.num_chamada, ifnull(aluno.rm, '-') as rm, " + \
                        'concat(LPAD(SUBSTR(vinculo_alunos_if.ra_aluno, -9, 1), 1, 0), SUBSTR(vinculo_alunos_if.ra_aluno, -8, 2), ".", substr(vinculo_alunos_if.ra_aluno, -6, 3), ".", substr(vinculo_alunos_if.ra_aluno, -3, 3), "-", aluno.digito_ra) as ra, ' + \
                        "aluno.nome, situacao.abv1 as sit, turma.nome_turma as turma, " + \
                        r"DATE_FORMAT(vinculo_alunos_if.matricula,'%d/%m/%Y') as matricula, " + \
                        r"DATE_FORMAT(vinculo_alunos_if.matricula, '%Y-%m-%d') as matricula_original, " + \
                        r"DATE_FORMAT(vinculo_alunos_if.fim_mat,'%d/%m/%Y') as fim_mat, " + \
                        r"DATE_FORMAT(vinculo_alunos_if.fim_mat, '%Y-%m-%d') as fim_mat_original, " + \
                        "vinculo_alunos_turmas.fim_mat as fim_mat_turma " + \
                        "FROM vinculo_alunos_if " + \
                        "INNER JOIN aluno ON aluno.ra = ra_aluno " + \
                        "INNER JOIN situacao ON vinculo_alunos_if.situacao = situacao.id " + \
                        "LEFT JOIN vinculo_alunos_turmas ON vinculo_alunos_if.ra_aluno = vinculo_alunos_turmas.ra_aluno " + \
                        "LEFT JOIN turma ON turma.num_classe = vinculo_alunos_turmas.num_classe " + \
                        "WHERE vinculo_alunos_if.num_classe_if = %s and vinculo_alunos_turmas.situacao = 1 and vinculo_alunos_if.situacao = 1 " % item['num_classe_if'] + \
                        "HAVING (select max(fim_mat) from vinculo_alunos_turmas where ra_aluno = vinculo_alunos_if.ra_aluno) = fim_mat_turma " + \
                        "ORDER BY num_chamada"

                #print(len(classes_comuns))
                
                lista_turma = banco.executarConsulta(sql)

                if len(lista_turma) > 0:
                    classe = {'info':dados, 'lista':lista_turma, 'qtd_classes':len(classes_comuns), 'esquema_cores':esquema_cores}
                    #print(classe['info'])
                    lista.append(classe)

                

            # agora é a parte difícil, organizar a lista e retirar os itinerários repetidos

            newList = []

            for item in lista:
                for jitem in lista:
                    if item['info']['num_classe'] != jitem['info']['num_classe']:
                        if item['lista'] == jitem['lista']:                      
                            info = {'num_classe':"%s;%s" % (item['info']['num_classe'], jitem['info']['num_classe']), 'nome_turma':"%s\n%s" % (item['info']['nome_turma'], jitem['info']['nome_turma']), 'duracao':item['info']['duracao'], 'tipo_ensino':item['info']['tipo_ensino'], 'cat_if':item['info']['cat_if'], 'periodo':item['info']['periodo']}
                            
                            if newList != []:
                                achou = False
                                for new_item in newList:
                                    if str(item['info']['num_classe']) in new_item['info']['num_classe']:
                                        achou = True

                                if not achou:
                                    newList.append({'info':info, 'lista':item['lista'], 'qtd_classes':item['qtd_classes'], 'esquema_cores':item['esquema_cores']})    
                            else:
                                newList.append({'info':info, 'lista':item['lista'], 'qtd_classes':item['qtd_classes'], 'esquema_cores':item['esquema_cores']})


            #print(newList)


            if newList != []:
                return jsonify(newList)

            return jsonify(lista)


@app.route('/getAlunosTurmaIF', methods=['GET', 'POST'])
def getAlunosTurmaIF():
    if request.method == "POST":
        if request.is_json:
            num_classe = request.json

            sql =   r"select CASE WHEN turma.duracao < 3 THEN DATE_FORMAT(1bim_inicio,'%d/%m/%Y') ELSE DATE_FORMAT(3bim_inicio,'%d/%m/%Y') END as inicio, " + \
	                r"CASE WHEN turma.duracao = 1 OR turma.duracao = 3 THEN DATE_FORMAT(4bim_fim,'%d/%m/%Y') ELSE DATE_FORMAT(2bim_fim,'%d/%m/%Y') END as fim, " + \
                    r"categoria_itinerario.descricao as categoria " + \
                    "from calendario INNER JOIN turma_if as turma ON turma.ano = calendario.ano INNER JOIN categoria_itinerario ON categoria_itinerario.id = turma.categoria WHERE turma.num_classe = %s" % (num_classe)
            
            info = banco.executarConsulta(sql)

            sql =   "SELECT	" + \
                    "vinculo_alunos_if.num_chamada, ifnull(aluno.rm, '-') as rm, " + \
                    'concat(LPAD(SUBSTR(vinculo_alunos_if.ra_aluno, -9, 1), 1, 0), SUBSTR(vinculo_alunos_if.ra_aluno, -8, 2), ".", substr(vinculo_alunos_if.ra_aluno, -6, 3), ".", substr(vinculo_alunos_if.ra_aluno, -3, 3), "-", aluno.digito_ra) as ra, ' + \
                    "aluno.nome, situacao.abv1 as sit, vinculo_alunos_turmas.num_classe, turma.nome_turma as turma, " + \
                    r"DATE_FORMAT(vinculo_alunos_if.matricula,'%d/%m/%Y') as matricula, " + \
                    r"DATE_FORMAT(vinculo_alunos_if.matricula, '%Y-%m-%d') as matricula_original, " + \
                    r"DATE_FORMAT(vinculo_alunos_if.fim_mat,'%d/%m/%Y') as fim_mat, " + \
                    r"DATE_FORMAT(vinculo_alunos_if.fim_mat, '%Y-%m-%d') as fim_mat_original, " + \
                    "vinculo_alunos_turmas.fim_mat as fim_mat_turma " + \
                    "FROM vinculo_alunos_if " + \
                    "INNER JOIN aluno ON aluno.ra = ra_aluno " + \
                    "INNER JOIN situacao ON vinculo_alunos_if.situacao = situacao.id " + \
                    "LEFT JOIN vinculo_alunos_turmas ON vinculo_alunos_if.ra_aluno = vinculo_alunos_turmas.ra_aluno " + \
                    "LEFT JOIN turma ON turma.num_classe = vinculo_alunos_turmas.num_classe " + \
                    "WHERE vinculo_alunos_if.num_classe_if = %s " % num_classe + \
                    "HAVING (select max(fim_mat) from vinculo_alunos_turmas where ra_aluno = vinculo_alunos_if.ra_aluno) = fim_mat_turma " + \
                    "ORDER BY num_chamada"
        
            #print(sql)

            turma = banco.executarConsulta(sql)

            sql = "select count(*) as total, sum(case when situacao = 1 then 1 else 0 end) as ativos from vinculo_alunos_if where num_classe_if = %s" % (num_classe)
            total = banco.executarConsulta(sql)[0]            

            return jsonify({'info':info[0], 'turma':turma, 'total':total})

@app.route('/getAlunosTurma', methods=['GET', 'POST'])
def getAlunosTurma():
    if request.method == "POST":
        if request.is_json:
            num_classe = request.json    

            sql =   "select num_chamada, ifnull(aluno.rm, '-') as rm, " \
                    'concat(LPAD(SUBSTR(ra_aluno, -9, 1), 1, 0), SUBSTR(ra_aluno, -8, 2), ".", substr(ra_aluno, -6, 3), ".", substr(ra_aluno, -3, 3), "-", aluno.digito_ra) as ra, ' \
                    r"serie, aluno.nome, DATE_FORMAT(aluno.nascimento,'%d/%m/%Y') as nascimento, DATE_FORMAT(aluno.nascimento,'%Y-%m-%d') as nascimento_original, " \
                    "TIMESTAMPDIFF(YEAR, aluno.nascimento, NOW()) AS idade, " \
                    "aluno.sexo, ifnull(aluno.rg, '-') as rg, ifnull(LPAD(aluno.cpf, 11, 0), '-') as cpf, " \
                    r"DATE_FORMAT(matricula,'%d/%m/%Y') as matricula, DATE_FORMAT(matricula, '%Y-%m-%d') as matricula_original, " \
                    r"DATE_FORMAT(fim_mat,'%d/%m/%Y') as fim_mat, DATE_FORMAT(fim_mat, '%Y-%m-%d') as fim_mat_original, " \
                    'situacao.abv1 as sit  from vinculo_alunos_turmas ' \
                    'INNER JOIN aluno ON aluno.ra = ra_aluno ' \
                    'INNER JOIN situacao ON vinculo_alunos_turmas.situacao = situacao.id ' \
                    'where num_classe = ' + str(num_classe) + ' order by num_chamada'

            turma = banco.executarConsulta(sql)

            #print(turma)
            
            sql =   r"select CASE WHEN turma.duracao < 3 THEN DATE_FORMAT(1bim_inicio,'%d/%m/%Y') ELSE DATE_FORMAT(3bim_inicio,'%d/%m/%Y') END as inicio, " + \
	                r"CASE WHEN turma.duracao = 1 OR turma.duracao = 3 THEN DATE_FORMAT(4bim_fim,'%d/%m/%Y') ELSE DATE_FORMAT(2bim_fim,'%d/%m/%Y') END as fim " + \
                    "from calendario INNER JOIN turma ON turma.ano = calendario.ano WHERE turma.num_classe = %s" % (num_classe)
            
            duracao = banco.executarConsulta(sql)

            sql = "select count(*) as total, sum(case when situacao = 1 then 1 else 0 end) as ativos from vinculo_alunos_turmas where num_classe = %s" % (num_classe)

            total = banco.executarConsulta(sql)[0]

            return jsonify({'duracao':duracao, 'turma':turma, 'total':total})
            

@app.route('/pesquisarPlan', methods=['GET', 'POST'])
def pesquisarPlan():
    if request.method == "POST":
        if request.is_json:
            estrutura = xls()

            total = int(estrutura.getCountA("Lista Piloto", "J9:J1000")) + 9
            lista = []

            for i in range(9, total):

                try :
                    ra = estrutura.getValCell("Lista Piloto", "J%i" % i)
                    sexo = estrutura.getValCell("Lista Piloto", "F%i" % i)
                    rm = int(estrutura.getValCell("Lista Piloto", "B%i" % i))

                    if 'float' in str(type(ra)):
                        ra = str(int(ra))[:-1]
                    else:
                        ra = ra[:-1].replace('-', '').replace('.', '')

                    lista.append({'ra':ra, 'sexo':sexo, 'rm':rm})
                except:
                    pass

            
            #print(lista)
            return jsonify(lista)

@app.route('/pesquisarRGCPF', methods=['GET', 'POST'])
def pesquisarRGCPF():
    if request.method == "POST":
        if request.is_json:
            lista = request.json
            new_lista = buscarCPF(lista, 1)
            #print(new_lista)
            return jsonify(new_lista)

@app.route('/importarTurma', methods=['GET', 'POST'])
def importarTurma():

    if request.method == "POST":
        if request.is_json:
            lista = request.json
            return jsonify(banco.importarDadosTurma(lista))
        

@app.route('/getVinculoIf', methods=['GET', 'POST'])
def getVinculoIf():
    if request.method == "POST":
        if request.is_json:
            num_classe = request.json
            return jsonify(banco.executarConsulta('select num_classe_em from vinculo_if where num_classe_if = %s' % num_classe))


@app.route('/upload_turma', methods=['GET', 'POST'])
def uploadTurma():

    lista = []
    info = []


    if 'classe' in request.args:
        classe = request.args['classe']
        #print(classe)
        info = banco.executarConsulta('select num_classe, nome_turma, duracao.descricao as duracao, periodo.descricao as periodo, tipo_ensino.descricao as tipo_ensino from turma INNER JOIN duracao ON duracao.id = turma.duracao INNER JOIN periodo ON periodo.id = turma.periodo INNER JOIN tipo_ensino ON tipo_ensino.id = turma.tipo_ensino WHERE num_classe = %s' % classe)
        if (info == []):
            info = banco.executarConsulta('select num_classe, nome_turma, duracao.descricao as duracao, periodo.descricao as periodo, tipo_ensino.descricao as tipo_ensino from turma_if as turma INNER JOIN duracao ON duracao.id = turma.duracao INNER JOIN periodo ON periodo.id = turma.periodo INNER JOIN tipo_ensino ON tipo_ensino.id = turma.tipo_ensino WHERE num_classe = %s' % classe)

    if request.method == "POST":

        #print(request.form)
        info = banco.executarConsulta('select num_classe, nome_turma, duracao.descricao as duracao, periodo.descricao as periodo, tipo_ensino.descricao as tipo_ensino from turma INNER JOIN duracao ON duracao.id = turma.duracao INNER JOIN periodo ON periodo.id = turma.periodo INNER JOIN tipo_ensino ON tipo_ensino.id = turma.tipo_ensino WHERE num_classe = %s' % request.form.get('classe'))
        if (info == []):
            info = banco.executarConsulta('select num_classe, nome_turma, duracao.descricao as duracao, periodo.descricao as periodo, tipo_ensino.descricao as tipo_ensino from turma_if as turma INNER JOIN duracao ON duracao.id = turma.duracao INNER JOIN periodo ON periodo.id = turma.periodo INNER JOIN tipo_ensino ON tipo_ensino.id = turma.tipo_ensino WHERE num_classe = %s' % request.form.get('classe'))

        f = request.files.get('file')
        #print(request.form)
        #print(request.files)
        #data_filename = secure_filename(f.filename)
        dir = os.path.join(app.config['UPLOAD_FOLDER'], 'import.csv')
        f.save(dir)

        with open(dir, newline='', encoding="utf8") as csvfile:
            spamreader = csv.reader(csvfile, delimiter=';', quotechar='|')

            cont = 0

            for row in spamreader:
                cont += 1
                
                if cont > 3:
                    try:
                        situacao = row[10]

                        sit = 0

                        if situacao == "ATIVO" or situacao == "ENCERRADA":
                            sit = 1
                        elif situacao == 'BXTR' or situacao == 'TRAN':
                            sit = 2
                        elif situacao == "REMA":
                            sit = 3
                        elif situacao == "NCFP" or situacao == "NCOM":
                            sit = 5
                        elif situacao == "CONCL":
                            sit = 8
                        elif situacao == "APROVADO":
                            sit = 6
                        elif situacao == "RETIDO FREQ.":
                            sit = 10
                        elif situacao == 'RECL':
                            sit = 15


                        serie = "-"

                        if row[1] != "":
                            serie = row[1]

                        aluno = {'ra':row[4], 'digito':row[5], 'nome':row[3], 'nascimento':row[7], 'matricula':row[8], 'num_chamada':row[2], 'serie':serie, 'desc_sit':row[10], 'situacao':sit, 'fim_mat':row[9], 'sexo':'M', 'rg':'', 'cpf':'', 'rm':''}

                        # verificar por registro anterior do aluno e alterar os dados com os valores já salvos
                        dados_aluno = banco.executarConsulta("select ifnull(rm, '') as rm, sexo, ifnull(rg, '') as rg, ifnull(cpf, '') as cpf from aluno where ra = %s" % aluno['ra'])
                        
                        if len(dados_aluno) > 0:
                            # alterar informações
                            aluno['rm'] = dados_aluno[0]['rm']
                            aluno['sexo'] = dados_aluno[0]['sexo']
                            aluno['rg'] = dados_aluno[0]['rg']
                            aluno['cpf'] = dados_aluno[0]['cpf']
                        

                        lista.append(aluno)

                    except Exception as error:
                        print("An exception occurred:", error) # An exception occurred: division by zero:


    return render_template('upload_turma.jinja', lista=lista, info=info)

@app.route('/listaAlunos', methods=['GET', 'POST'])
def listaAlunos():

    if request.method == "POST":
        if request.is_json:
            ra = request.json

            sql = "select " + \
	                    "tba.num_classe, turma.nome_turma, serie, tipo_ensino.descricao as ensino, " + \
                        r"DATE_FORMAT(tba.matricula,'%d/%m/%Y') as mat, DATE_FORMAT(tba.fim_mat,'%d/%m/%Y') as fim_mat, " + \
                        'if ((select sexo from aluno where ra = %s) = "M", situacao.descricao, situacao.desc_fem) as situacao, situacao.abv1 as abv, turma.ano ' % ra + \
                        "from vinculo_alunos_turmas as tba " + \
                        "INNER JOIN turma ON tba.num_classe = turma.num_classe " + \
                        "INNER JOIN situacao ON situacao.id = tba.situacao " + \
                        "INNER JOIN tipo_ensino ON tipo_ensino.id = turma.tipo_ensino " + \
                        "where ra_aluno = %s " % ra + \
                        "order by tba.fim_mat desc"

            #print(sql)
            historico = banco.executarConsulta(sql)

            return jsonify(historico)


    lista = banco.executarConsulta(r"SELECT ifnull(rm, '-') as rm, nome, ra as ra_val, concat(LPAD(SUBSTR(ra, -9, 1), 1, 0), SUBSTR(ra, -8, 2), '.', substr(ra, -6, 3), '.', substr(ra, -3, 3), '-', aluno.digito_ra) as ra, DATE_FORMAT(nascimento,'%d/%m/%Y') as nascimento_show, DATE_FORMAT(nascimento, '%Y-%m-%d') as nascimento_val, TIMESTAMPDIFF(YEAR, aluno.nascimento, NOW()) AS idade, sexo, ifnull(rg, '-') as rg, ifnull(concat(LPAD(SUBSTR(cpf, -11, 1), 1, 0), SUBSTR(cpf, -10, 2), '.', substr(cpf, -8, 3), '.', substr(cpf, -5, 3), '-', substr(cpf, -2, 2)), '-') as cpf FROM aluno ORDER BY nome")

    #for item in lista:
        #print(item)

    return render_template('alunos.jinja', lista=lista)


@app.route('/notas', methods=['GET', 'POST'])
def notas():
    msg = ""

    if 'status' in request.args:
        if request.args['status'] == '1':
            msg = '<div class="alert alert-success alert-dismissible fade show" role="alert">' \
                    '<strong>Operação bem-sucedida!</strong> Notas atualizadas com sucesso!' \
                    '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                    '</div>'
        else:
            msg = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' \
                    '<strong>Atenção!</strong> Erro ao tentar salvar notas, <strong>Contate o administrador!</strong>' \
                    '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                    '</div>'

    if request.method == "POST":

        if request.is_json:
            info = request.json

            

            # significa que é pra carregar a lista de alunos e as notas atuais
            if info['action'] == 0:
                # consulta para pegar somente os alunos elegíveis a receber nota no bimestre
                sql = "SELECT num_chamada, ra, nome FROM vinculo_alunos_turmas INNER JOIN aluno ON vinculo_alunos_turmas.ra_aluno = aluno.ra WHERE num_classe = %s AND fim_mat >= '%s' AND matricula < '%s' ORDER BY num_chamada" % (info['num_classe'], info['fim'], info['fim'])
                #print(sql)
                alunos = banco.executarConsulta(sql)

                if (len(alunos) < 1): #quer dizer que é itineráfio formativo
                    sql = "SELECT num_chamada, ra, nome FROM vinculo_alunos_if INNER JOIN aluno ON vinculo_alunos_if.ra_aluno = aluno.ra WHERE num_classe_if = %s AND fim_mat >= '%s' AND matricula < '%s' ORDER BY num_chamada" % (info['num_classe'], info['fim'], info['fim'])
                    alunos = banco.executarConsulta(sql)

                for aluno in alunos:
                    dificuldades = banco.executarConsultaVetor('select dificuldade from alunos_dificuldades where ra = %s and bimestre = %s and num_classe = %s' % (aluno['ra'], info['bimestre'], info['num_classe']))
                    aluno['dificuldade'] = dificuldades

                # carregar as notas caso elas existam
                disciplinas = banco.executarConsulta('select disciplina, abv from notas inner join disciplinas on disciplinas.codigo_disciplina = notas.disciplina where bimestre = %s and num_classe = %s group by disciplina' % (info['bimestre'], info['num_classe']))

                professores = banco.executarConsulta('select professor.nome_ata, disciplina, disciplinas.abv as desc_disc, aulas_dadas from vinculo_prof_disc inner join professor on professor.rg = vinculo_prof_disc.rg_prof inner join disciplinas ON disciplinas.codigo_disciplina = vinculo_prof_disc.disciplina  where bimestre = %s and num_classe = %s order by disciplina' % (info['bimestre'], info['num_classe']))

                profs = {}

                for item in professores:
                    profs[item['disciplina']] = {'prof':item['nome_ata'], 'ad':item['aulas_dadas']}

                for item in disciplinas:
                    # agora é a parte mais chata, vou consultar lista de disciplina por disciplina
                    lista = banco.executarConsulta('select ra_aluno, nota, falta, if(ac=0, "-", ac) as ac from notas where bimestre = %s and num_classe = %s and disciplina = %s' % (info['bimestre'], info['num_classe'], item['disciplina']))

                    notas = []

                    for aluno in lista:
                        #print(aluno)
                        dict = {'ra_aluno':aluno['ra_aluno'], 'N':aluno['nota'], 'F':aluno['falta'], 'AC':aluno['ac']}
                        notas.append(dict)

                    item['notas'] = notas

                return jsonify({'alunos':alunos, 'notas':disciplinas, 'professores':profs, 'medias':[]})
            
            # significa que é pra importar o mapão da SED
            elif info['action'] == 1:
                file_dir = home_directory + r'\Downloads' + '\\' + info['file']

                data = pd.read_html(file_dir)
                print(data)
                #df2 = data[0].sum()
                
                #coluna = 1
                total = (len(data[0].axes[1]) - 1) / 5
                total_r = (len(data[0].axes[0])) - 2
                #print(len(data[0].axes[1]))
                #print(total)
                
                coluna = 1
                bimestre_final = 0

                if info['duracao'] == '1º Semestre':
                    bimestre_final = 2
                else:
                    bimestre_final = 4

                lista = []

                print(total)
                for i in range(0, int(math.ceil(total))):
                    item = {'disc':data[0][coluna][12]}
                    print(item)
                    
                    if str(item['disc']).isnumeric():

                        if data[0][31][6] == "Tipo de Fechamento: CONSELHO FINAL (QUINTO CONCEITO)":

                            professor = item['professor'] = banco.executarConsulta('select professor.nome_ata as nome from vinculo_prof_disc inner join professor ON professor.rg = vinculo_prof_disc.rg_prof where num_classe = %s and bimestre = %s and disciplina = %s' % (info['num_classe'], bimestre_final, item['disc']))

                            if len(professor) > 0:
                                item['abv'] = banco.executarConsulta('select abv from disciplinas where codigo_disciplina = %s' % item['disc'])[0]['abv']
                            
                                medias = {}
                                
                                for j in range(15, total_r):
                                    medias[data[0][coluna][j]] = {'M':data[0][coluna + 1][j]}

                                item['medias'] = medias
                                item['professor'] = professor[0]['nome']

                                lista.append(item)

                            coluna += 3
                        else:
                            ad = int(data[0][coluna][total_r].replace('Aulas Dadas: ', ''))

                            if ad > 0:
                                item['abv'] = banco.executarConsulta('select abv from disciplinas where codigo_disciplina = %s' % item['disc'])[0]['abv']

                                notas = {}

                                for j in range(15, total_r):
                                    notas[data[0][coluna][j]] = {'N':data[0][coluna + 1][j], 'F':data[0][coluna + 2][j], 'AC':data[0][coluna + 3][j]}

                                #print(total_r + 1)

                                item['AD'] = data[0][coluna][total_r].replace('Aulas Dadas: ', '')


                                item['notas'] = notas
                                lista.append(item)  

                            coluna += 5
        

                professores = banco.executarConsulta('select rg, nome_ata from vinculo_turma_prof INNER JOIN professor ON professor.rg = vinculo_turma_prof.rg_prof where id_turma = %s order by nome_ata' % info['num_classe'])
                #print(lista)

                #verificar se já existe professores vinculados a disciplina e se existir criar uma lista
                professores_atuais = banco.executarConsulta('select rg_prof, disciplina from vinculo_prof_disc where bimestre = %s and num_classe = %s' % (info['bimestre'], info['num_classe']))
                dict_aux = {}
                for item in professores_atuais:
                    dict_aux[item['disciplina']] = item['rg_prof']

                return jsonify({'lista':lista, 'professores':professores, 'professores_atuais':dict_aux})
            
            elif info['action'] == 2:
                return jsonify(banco.salvarVinculoProfs(info))
            
            elif info['action'] == 3:
                lista = banco.executarConsulta('select rg_prof from vinculo_turma_prof where id_turma = %s' % info['num_classe'])
                return jsonify(lista)
            
            elif info['action'] == 4:

                if info['bim'] == '5':
                    return jsonify(banco.salvarMedias(info))
                else:
                    return jsonify(banco.salvarNotas(info))
                
            elif info['action'] == 5:
                # consulta para pegar somente os alunos elegíveis a receber nota no bimestre
                sql = "SELECT num_chamada, ra, nome, if(sexo='M', situacao.descricao, situacao.desc_fem) as situacao, situacao.abv1 FROM vinculo_alunos_turmas INNER JOIN aluno ON vinculo_alunos_turmas.ra_aluno = aluno.ra INNER JOIN situacao ON situacao.id = vinculo_alunos_turmas.situacao WHERE num_classe = %s AND fim_mat >= '%s' AND matricula < '%s' ORDER BY num_chamada" % (info['num_classe'], info['fim'], info['fim'])
                #print(sql)
                alunos = banco.executarConsulta(sql)

                if (len(alunos) < 1): # é itinerário formativo
                    alunos = banco.executarConsulta("SELECT num_chamada, ra, nome, if(sexo='M', situacao.descricao, situacao.desc_fem) as situacao, situacao.abv1 FROM vinculo_alunos_if INNER JOIN aluno ON vinculo_alunos_if.ra_aluno = aluno.ra INNER JOIN situacao ON situacao.id = vinculo_alunos_if.situacao WHERE num_classe_if = %s AND fim_mat >= '%s' AND matricula < '%s' ORDER BY num_chamada" % (info['num_classe'], info['fim'], info['fim']))

                # carregar as médias caso elas existam
                disciplinas = banco.executarConsulta('select disciplina, abv from conceito_final inner join disciplinas on disciplinas.codigo_disciplina = conceito_final.disciplina where num_classe = %s group by disciplina' % (info['num_classe']))

                duracao = banco.executarConsulta('select duracao from turma where num_classe = %s' % info['num_classe'])

                if (len(duracao) < 1):
                    duracao = banco.executarConsulta('select duracao from turma_if where num_classe = %s' % info['num_classe'])

                duracao = duracao[0]['duracao']
                
                bimestre = 4
                if duracao == 2:
                    bimestre = 2

                sql = 'select professor.nome_ata, disciplina, disciplinas.abv as desc_disc, aulas_dadas from vinculo_prof_disc inner join professor on professor.rg = vinculo_prof_disc.rg_prof inner join disciplinas ON disciplinas.codigo_disciplina = vinculo_prof_disc.disciplina  where bimestre = %s and num_classe = %s order by disciplina' % (bimestre, info['num_classe'])
                professores = banco.executarConsulta(sql)
                #print(sql)

                profs = {}

                for item in professores:
                    profs[item['disciplina']] = {'prof':item['nome_ata']}

                for item in disciplinas:
                    # agora é a parte mais chata, vou consultar lista de disciplina por disciplina
                    lista = banco.executarConsulta('select ra_aluno, media from conceito_final where num_classe = %s and disciplina = %s' % (info['num_classe'], item['disciplina']))

                    notas = []

                    for aluno in lista:
                        #print(aluno)
                        dict = {'ra_aluno':aluno['ra_aluno'], 'M':aluno['media']}
                        notas.append(dict)

                    item['medias'] = notas

                return jsonify({'alunos':alunos, 'medias':disciplinas, 'professores':profs, 'notas':[]})

        if 'txt_coddisciplina' in request.form:
            codigo = request.form.get('txt_coddisciplina')
            desc = "'" + request.form.get('txt_descricao') + "'"
            abv = "'" + request.form.get('txt_abv') + "'" 
            classific = request.form.get('cbClassificacao')

            disc = {'codigo_disciplina':codigo, 'descricao':desc, 'abv':abv, 'classificacao':classific}
            
            if banco.insertOrUpdate(disc, 'disciplinas'):
                msg = '<div class="alert alert-success alert-dismissible fade show" role="alert">' \
                        '<strong>Operação bem-sucedida!</strong> Dados da disciplina <strong>' + request.form['txt_descricao'] + '</strong> atualizados com sucesso!' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'
            else:
                msg = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' \
                        '<strong>Atenção!</strong> Erro ao tentar alterar dados da disciplina, <strong>Contate o administrador!</strong>.' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'
        
        elif 'txt_rgprof' in request.form:
            disc = {'rg':request.form.get('txt_rgprof'), 'nome':"'" + request.form.get('txt_nomeprof') + "'", 'nome_ata':"'" + request.form.get('txt_nomeata') + "'"}
            if banco.insertOrUpdate(disc, 'professor'):
                msg = '<div class="alert alert-success alert-dismissible fade show" role="alert">' \
                        '<strong>Operação bem-sucedida!</strong> Dados do professor <strong>' + request.form['txt_nomeprof'] + '</strong> atualizados com sucesso!' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'
            else:
                msg = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' \
                        '<strong>Atenção!</strong> Erro ao tentar alterar dados do professor, <strong>Contate o administrador!</strong>.' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'
                
            
        if bool(request.files.get('fileDif', False)) == True:
            #print(request.form)
            bimestre = request.form.get('bimestre_import_dif')
            num_classe = request.form.get('num_classe_import_dif')

            f = request.files.get('fileDif')
            print(f)
            #data_filename = secure_filename(f.filename)
            dir = os.path.join(app.config['UPLOAD_FOLDER'], 'import.xlsx')
            f.save(dir) 

            excel = open_xls(dir)

            lista = []

            for row in range(23, 109):
                number = excel.getCell(row, 1)
                
                difs = []
                for col in range(2, 19):
                    if excel.getCell(row, col) == "X" or excel.getCell(row, col) == "x":
                        difs.append(excel.getCell(22, col))

                if difs != []:
                    lista.append({'Number':number, 'dificuldades':difs})

            
            # após conseguir criar a lista preciso processá-la para enviar ao banco de dados
            lista_db = []
            for item in lista:
                # descobrir ra
                ra = banco.executarConsulta('select ra_aluno from vinculo_alunos_turmas where num_classe = %s and num_chamada = %s' % (num_classe, item['Number']))[0]['ra_aluno']

                for dif in item['dificuldades']:
                    lista_db.append({'ra':ra, 'item':dif, 'bimestre':bimestre, 'num_classe':num_classe})

            # eu tenho a lista 100% processada para inserção no banco de dados
            if banco.salvarDificuldades(lista_db):
                msg = '<div class="alert alert-success alert-dismissible fade show" role="alert">' \
                        '<strong>Operação bem-sucedida!</strong> Dados da Lista de Dificuldades importados com sucesso!' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'
            else :
                msg = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' \
                        '<strong>Atenção!</strong> Erro ao tentar importar dificuldades, <strong>Favor revisar a tabela!</strong>. Verifique se os números são mesmo números.' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'
        

    disciplinas = banco.executarConsulta('select codigo_disciplina, disciplinas.descricao, disciplinas.abv, classificacao, classificacao.abv as classificacao_desc from disciplinas INNER JOIN classificacao ON classificacao.id = disciplinas.classificacao order by descricao')
    classificacao = banco.executarConsulta('select * from classificacao')
    professores = banco.executarConsulta('select * from professor order by nome_ata')
    dificuldades = banco.executarConsulta('select id, descricao as title from dificuldades')

    listaTipos = banco.executarConsulta('select tipo_ensino.id, tipo_ensino.descricao as tipo_ensino, if (count(turma.tipo_ensino) > 0, count(turma.tipo_ensino), count(turma_if.tipo_ensino)) as total from tipo_ensino LEFT JOIN turma ON turma.tipo_ensino = tipo_ensino.id LEFT JOIN turma_if ON turma_if.tipo_ensino = tipo_ensino.id GROUP BY id order by id')

    listaTurmas = []

    for item in listaTipos:
        
        if item['total'] > 0:

            if item['id'] != 2 and item['id'] != 5:
                turmas = banco.executarConsulta('select num_classe, nome_turma, duracao.descricao as duracao, turma.duracao as id_duracao, turma.tipo_ensino as id_ensino, periodo.descricao as periodo, turma.periodo as id_periodo from turma INNER JOIN duracao ON duracao.id = turma.duracao INNER JOIN periodo ON periodo.id = turma.periodo where tipo_ensino = %s and ano = year(now()) order by duracao, nome_turma' % item['id'])
            else:
                turmas = banco.executarConsulta('select num_classe, nome_turma, duracao.descricao as duracao, turma_if.duracao as id_duracao, turma_if.tipo_ensino as id_ensino, periodo.descricao as periodo, turma_if.periodo as id_periodo, turma_if.categoria as categoria from turma_if INNER JOIN duracao ON duracao.id = turma_if.duracao INNER JOIN periodo ON periodo.id = turma_if.periodo where tipo_ensino = %s and ano = year(now()) order by duracao, nome_turma' % item['id'])

            listaTurmas.append({'tipo_ensino':item, 'lista':turmas})


    bimestres = banco.executarConsulta('select * from calendario where ano = Year(Now())')
    #bimestres = banco.executarConsulta('select * from calendario where ano = 2023')
    bim = {'1bim':{'inicio':bimestres[0]['1bim_inicio'], 'fim':bimestres[0]['1bim_fim']}}
    bim['2bim'] = {'inicio':bimestres[0]['2bim_inicio'], 'fim':bimestres[0]['2bim_fim']}
    bim['3bim'] = {'inicio':bimestres[0]['3bim_inicio'], 'fim':bimestres[0]['3bim_fim']}
    bim['4bim'] = {'inicio':bimestres[0]['4bim_inicio'], 'fim':bimestres[0]['4bim_fim']}

    return render_template('notas.jinja', bimestres=json.dumps(bim, indent=4, sort_keys=True, default=str), classificacao=classificacao, msg=msg, disciplinas=disciplinas, listaTurmas=listaTurmas, professores=professores, dificuldades=json.dumps(dificuldades))


@app.route('/calendario', methods=['GET', 'POST'])
def calendario():

    # montando calendário padrão

    ano = 2024

    calendario = []
    letivos = 0

    # percorrendo todo os meses do ano
    for i in range(1, 13):
        qtd_dias = calendar.monthrange(ano, i)[1]

        dias = []

        for j in range(1, qtd_dias + 1):
            date_aux = datetime(ano, i, j)
            

            if date_aux.strftime("%a") != 'dom' and date_aux.strftime("%a") != 'sáb':
                letivos += 1
                dias.append({'dia':j, 'semana':date_aux.strftime("%a"), 'situacao':'Letivo'})
            else:
                dias.append({'dia':j, 'semana':date_aux.strftime("%a"), 'situacao':'-'})

        #desc_mes = datetime(ano, i, 1)

        calendario.append({'dias':dias, 'descricao':calendar.month_name[i].title()})

    return render_template('calendario.jinja', calendario=calendario, letivos=letivos)

if __name__ == '__main__':
    app.run('0.0.0.0',port=80)
    #serve(app, host='0.0.0.0', port=80, threads=8)