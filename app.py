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

@app.route('/', methods=['GET', 'POST'])
def index():

    msg = ""
    ano = datetime.now().year

    if request.method == 'POST':

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
    listaTipos = banco.executarConsulta('select tipo_ensino.id, tipo_ensino.descricao as tipo_ensino, if (count(turma.tipo_ensino) > 0, count(turma.tipo_ensino), count(turma_if.tipo_ensino)) as total from tipo_ensino LEFT JOIN turma ON turma.tipo_ensino = tipo_ensino.id LEFT JOIN turma_if ON turma_if.tipo_ensino = tipo_ensino.id GROUP BY id order by id')
    cat_itinerario = banco.executarConsulta('select * from categoria_itinerario')

    listaTurmas = []

    for item in listaTipos:
        
        if item['total'] > 0:

            color = 'table-dark'

            if item['id'] != 2 and item['id'] != 5:
                turmas = banco.executarConsulta('select num_classe, nome_turma, duracao.descricao as duracao, turma.duracao as id_duracao, turma.tipo_ensino as id_ensino, periodo.descricao as periodo, turma.periodo as id_periodo from turma INNER JOIN duracao ON duracao.id = turma.duracao INNER JOIN periodo ON periodo.id = turma.periodo where tipo_ensino = %s order by duracao, nome_turma' % item['id'])
            else:
                turmas = banco.executarConsulta('select num_classe, nome_turma, duracao.descricao as duracao, turma_if.duracao as id_duracao, turma_if.tipo_ensino as id_ensino, periodo.descricao as periodo, turma_if.periodo as id_periodo, turma_if.categoria as categoria from turma_if INNER JOIN duracao ON duracao.id = turma_if.duracao INNER JOIN periodo ON periodo.id = turma_if.periodo where tipo_ensino = %s order by duracao, nome_turma' % item['id'])
                color = 'table-primary'
                
            listaTurmas.append({'tipo_ensino':item, 'lista':turmas, 'color':color})


    #print(listaTurmas)

    return render_template('home.jinja', tipo_ensino=tipo_ensino, calendario=calendario[0], duracao=duracao, periodo=periodo, msg=msg, listaTurmas=listaTurmas, tipo_ensino_itinerario=tipo_ensino_itinerario, cat_itinerario=cat_itinerario)

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
                print(info)
                file_dir = home_directory + r'\Downloads' + '\\' + info['file']

                data = pd.read_html(file_dir)
                #print(data)
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

                for i in range(0, int(total)):
                    item = {'disc':data[0][coluna][12]}
                    #print(item)
                    
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


                return jsonify({'lista':lista, 'professores':professores})
            
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
                turmas = banco.executarConsulta('select num_classe, nome_turma, duracao.descricao as duracao, turma.duracao as id_duracao, turma.tipo_ensino as id_ensino, periodo.descricao as periodo, turma.periodo as id_periodo from turma INNER JOIN duracao ON duracao.id = turma.duracao INNER JOIN periodo ON periodo.id = turma.periodo where tipo_ensino = %s order by duracao, nome_turma' % item['id'])
            else:
                turmas = banco.executarConsulta('select num_classe, nome_turma, duracao.descricao as duracao, turma_if.duracao as id_duracao, turma_if.tipo_ensino as id_ensino, periodo.descricao as periodo, turma_if.periodo as id_periodo, turma_if.categoria as categoria from turma_if INNER JOIN duracao ON duracao.id = turma_if.duracao INNER JOIN periodo ON periodo.id = turma_if.periodo where tipo_ensino = %s order by duracao, nome_turma' % item['id'])

            listaTurmas.append({'tipo_ensino':item, 'lista':turmas})


    bimestres = banco.executarConsulta('select * from calendario where ano = Year(Now())')
    bim = {'1bim':{'inicio':bimestres[0]['1bim_inicio'], 'fim':bimestres[0]['1bim_fim']}}
    bim['2bim'] = {'inicio':bimestres[0]['2bim_inicio'], 'fim':bimestres[0]['2bim_fim']}
    bim['3bim'] = {'inicio':bimestres[0]['3bim_inicio'], 'fim':bimestres[0]['3bim_fim']}
    bim['4bim'] = {'inicio':bimestres[0]['4bim_inicio'], 'fim':bimestres[0]['4bim_fim']}

    return render_template('notas.jinja', bimestres=json.dumps(bim, indent=4, sort_keys=True, default=str), classificacao=classificacao, msg=msg, disciplinas=disciplinas, listaTurmas=listaTurmas, professores=professores, dificuldades=json.dumps(dificuldades))

if __name__ == '__main__':
    app.run('0.0.0.0',port=80)
    #serve(app, host='0.0.0.0', port=80, threads=8)