#import locale
from MySQL import db
from getInfoSED import buscarCPF
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, Response
from waitress import serve
from datetime import datetime
from werkzeug.utils import secure_filename
from excel import xls, open_xls
from utilitarios import converterLista, getMes, hojePorExtenso, series_fund, getSituacao, converterDataMySQL
from flask_socketio import SocketIO, emit
import pandas as pd
import os
import csv
import json
from pyppeteer import launch
import locale
import math
import calendar
from jinja_try_catch import TryCatchExtension


locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')

UPLOAD_FOLDER = os.path.join('staticFiles', 'uploads')

# vou ver se consigo abrir certinho
app=Flask(__name__)
app.secret_key = "abc123"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'justasecretkeythatishouldputhere'
socketio = SocketIO(app, async_mode='threading')

app.jinja_env.add_extension(TryCatchExtension)


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

        if request.is_json:
            num_classe = request.get_json()

            data = banco.executarConsulta(f"select tipo, tipo_disc_matriz.descricao as desc_tipo, disc_disciplina as disc, disciplinas.descricao as desc_disc, area, ifnull(area_matriz.desc_curta, '-') as desc_area, qtd_aulas, minutos from matriz_curricular inner join disciplinas on disciplinas.codigo_disciplina = disc_disciplina inner join area_matriz on area_matriz.id = area inner join tipo_disc_matriz on tipo_disc_matriz.id = tipo where num_classe = {num_classe} order by tipo, area, disc_disciplina")
            
            return jsonify(data)

        if 'matriz' in request.form:
            matriz = json.loads(request.form['matriz'])
            if banco.alterarMatriz(matriz):
                msg = '<div class="alert alert-success alert-dismissible fade show" role="alert">' \
                        '<strong>Operação bem-sucedida!</strong> Matriz alterada com sucesso!' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'
            else:
                msg = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' \
                        '<strong>Atenção!</strong> Erro ao tentar alterar matriz, verifique se foi tudo digitado corretamente.' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'

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

            classe = {'num_classe':request.form['txtnumeroclasse'], 'nome_turma':"'" + request.form['txtnometurma'] + "'", 'duracao':request.form['cbduracao'], 'tipo_ensino':request.form['cbtipoensino'], 'periodo':request.form['cbperiodo'], 'ano':request.form['ano']}
            
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


    # pegar dados para compor a matriz
    tipo_disc = banco.executarConsulta('select id, descricao from tipo_disc_matriz')
    area_conhecimento = banco.executarConsulta('select id, desc_curta from area_matriz where id > 0')
    disc = banco.executarConsulta('select codigo_disciplina, descricao from disciplinas order by codigo_disciplina')

    return render_template('home.jinja', tipo_ensino=tipo_ensino, calendario=calendario[0], duracao=duracao, periodo=periodo, msg=msg, listaTurmas=listaTurmas, tipo_ensino_itinerario=tipo_ensino_itinerario, cat_itinerario=cat_itinerario, anos=anos, tipo_disc=tipo_disc, area_conhecimento=area_conhecimento, disc=disc)

@app.route('/relatorios', methods=['GET', 'POST'])
def relatorios():

    if request.method == 'POST':
        if 'cb_relatorio' in request.form:
            opcao = int(request.form['cb_relatorio'])

            # lista combo
            combo_final = ['<option value="0">Lista de Alunos Ativos Faltando RG ou CPF</option>']
            
            if (opcao == 1):
                combo_final.append('<option value="1" selected>Lista de Alunos Ativos Faltando RG</option>')
            else:
                combo_final.append('<option value="1">Lista de Alunos Ativos Faltando RG</option>')

            if (opcao == 2):
                combo_final.append('<option value="2" selected>Lista de Alunos Ativos Faltando CPF</option>')
            else:
                combo_final.append('<option value="2">Lista de Alunos Ativos Faltando CPF</option>')                


            if (opcao == 0 or opcao == 1 or opcao == 2): # alunos faltando Documentação
                turmas = banco.executarConsulta('select num_classe, nome_turma from turma where ano = year(now()) order by tipo_ensino, nome_turma')
                
                soma = 0

                if (opcao == 0):
                    where = '(rg is null or cpf is null)'
                    text_final = 'algum documento.'
                elif (opcao == 1):
                    where = 'rg is null'
                    text_final = 'RG.'
                elif (opcao == 2):
                    where = 'cpf is null'
                    text_final = 'CPF.'                    

                for turma in turmas:
                    alunos = banco.executarConsulta('select ' + \
	                                                'concat(LPAD(SUBSTR(ra_aluno, -9, 1), 1, 0), SUBSTR(ra_aluno, -8, 2), ".", substr(ra_aluno, -6, 3), ".", substr(ra_aluno, -3, 3), "-", aluno.digito_ra) as ra, ' + \
                                                    'aluno.nome, ' + \
	                                                'CASE ' + \
		                                            'WHEN rg is null and cpf is null THEN "Deve <b>RG</b> e <b>CPF</b>." ' + \
                                                    'WHEN rg is null and cpf is not null THEN "Deve <b>RG</b>." ' + \
                                                    'WHEN rg is not null and cpf is null THEN "Deve <b>CPF</b>." END as descricao ' + \
                                                    'from vinculo_alunos_turmas ' + \
                                                    'inner join aluno on aluno.ra = vinculo_alunos_turmas.ra_aluno ' + \
                                                    'where num_classe = %s and situacao = 1 and %s ' % (turma['num_classe'], where) + \
                                                    'order by nome')
                    
                    soma += len(alunos)

                    for aluno in alunos:
                        aluno['nome'] = aluno['nome'].title().replace('Da ', 'da ').replace("De ", "de ").replace("Do ", 'do ').replace("Dos ", 'dos ') 
                    
                    turma['alunos'] = alunos

                return render_template('relatorios.jinja', opcao=opcao, turmas=turmas, soma=soma, text_final=text_final, combo_final=combo_final)


    combo_final = ['<option value="0">Lista de Alunos Ativos Faltando RG ou CPF</option>', '<option value="1">Lista de Alunos Ativos Faltando RG</option>', '<option value="2">Lista de Alunos Ativos Faltando CPF</option>']

    return render_template('relatorios.jinja', opcao = -1, combo_final=combo_final)

@app.route('/render_livro_ponto_adm',  methods=['GET', 'POST'])
def render_livro_ponto_adm():

    cpf = int(request.args.getlist('cpf')[0])
    mes = int(request.args.getlist('mes')[0])
    ano = int(request.args.getlist('ano')[0])

    dados = banco.executarConsulta("select nome, cpf, rg, digito, horario, intervalo, cargos_livro_ponto.descricao as cargo, CASE WHEN estudante = 1 THEN 'Sim' ELSE 'Não' END AS estudante, CASE WHEN plantao = 1 THEN 'Sim' ELSE 'Não' END AS plantao from funcionario_livro_ponto inner join cargos_livro_ponto on cargos_livro_ponto.id = funcionario_livro_ponto.cargo where cpf = %s" % cpf)[0]

    aux_rg = '%08d' % int(dados['rg'])
    dados['rg'] = aux_rg[0:2] + "." + aux_rg[2:5] + "." + aux_rg[5:] + '-' + dados['digito']

    aux = '%011d' % int(dados['cpf'])
    dados['cpf'] = aux[:3] + "." + aux[3:6] + "." + aux[6:9] + "-" + aux[9:]

    # preencher o mês
    _, num_dias = calendar.monthrange(ano, mes)

    # Cria uma lista para armazenar os resultados
    dias_com_fim_de_semana = []
    verso_txt = []
    afastamentos = []
    aux_afs = {}
    cont_afs = 1
    afastamento = False


    for dia in range(1, num_dias + 1):
        data = datetime(ano, mes, dia)

        # antes de mais nada verifica se existe afastamento
        inicio_afastamento = banco.executarConsulta("select * from afastamentos_ponto_adm where cpf = %s and inicio = '%s-%s-%s'" % (cpf, ano, mes, dia))

        if len(inicio_afastamento) > 0:
            afastamento = True
            aux_afs['nome'] = 'afastamento_%s' % cont_afs
            aux_afs['inicio'] = dia
            cont_afs += 1



            if (inicio_afastamento[0]['inicio'] != inicio_afastamento[0]['fim']):
                dias_com_fim_de_semana.append({'dia':dia, 'tipo':'', 'obs':'VIDE VERSO', 'class':'red', 'tr-class':'class="line-afast"'})
                if 'Aposentando' in inicio_afastamento[0]['descricao']:
                    verso_txt.append('A partir do dia %02d - %s' % (inicio_afastamento[0]['inicio'].day, inicio_afastamento[0]['descricao']))
                else:
                    verso_txt.append('De %02d até %02d - %s' % (inicio_afastamento[0]['inicio'].day, inicio_afastamento[0]['fim'].day, inicio_afastamento[0]['descricao']))
            else:
                verso_txt.append('Dia %02d - %s' % (inicio_afastamento[0]['inicio'].day, inicio_afastamento[0]['descricao']))

        if not afastamento:

            # Verifica se é feriado ou pf, se for puxa o feriado/pf
            feriado = banco.executarConsulta("select eventos_calendario.descricao, cat_letivo.descricao as tipo from eventos_calendario inner join cat_letivo on cat_letivo.id = eventos_calendario.evento where '%s-%s-%s' in (data_inicial, data_final) and evento in (3, 4, 5, 13) and instancia_calendario = 0" % (ano, mes, dia))

            if len(feriado) > 0:
                dias_com_fim_de_semana.append({'dia':dia, 'tipo':feriado[0]['tipo'].upper(), 'obs':'VIDE VERSO', 'class':'red', 'tr-class':''})
                verso_txt.append('Dia %02d - %s' % (dia, feriado[0]['descricao']))
            elif data.weekday() == 5:
                dias_com_fim_de_semana.append({'dia':dia, 'tipo':'SÁBADO', 'obs':'', 'class':'', 'tr-class':''})
            elif data.weekday() == 6:
                dias_com_fim_de_semana.append({'dia':dia, 'tipo':'DOMINGO', 'obs':'', 'class':'', 'tr-class':''})
            else:
                dias_com_fim_de_semana.append({'dia':dia, 'tipo':'', 'obs':'', 'class':'', 'tr-class':''})

        else:
            print(len(inicio_afastamento))
            fim_afastamento = banco.executarConsulta("select * from afastamentos_ponto_adm where cpf = %s and fim = '%s-%s-%s'" % (cpf, ano, mes, dia))

            if len(fim_afastamento) > 0: # pegou o fim
                dias_com_fim_de_semana.append({'dia':dia, 'tipo':'', 'obs':'VIDE VERSO', 'class':'red', 'tr-class':'class="line-afast"'})
                afastamento = False
                aux_afs['fim'] = dia
                if (aux_afs['fim'] - aux_afs['inicio'] > 1):
                    afastamentos.append(aux_afs)
                aux_afs = {}
                
            elif len(inicio_afastamento) == 0:
                dias_com_fim_de_semana.append({'dia':dia, 'tipo':'', 'obs':'', 'class':'divisor', 'tr-class':''})

    return render_template('render_pdf/render_livro_ponto_adm.jinja', mes=getMes(mes), ano=ano, dados=dados, dias=dias_com_fim_de_semana, verso=verso_txt, afastamentos=afastamentos)



@app.route('/render_livro_ponto',  methods=['GET', 'POST'])
def render_livro_ponto():

    ano = int(request.args.getlist('ano')[0])
    mes = int(request.args.getlist('mes')[0])
    ua_padrao = banco.executarConsulta("select valor from config where id_config = 'ua_sede'")[0]['valor']
    dias_semana = ['seg', 'ter', 'qua', 'qui', 'sex', 'sáb', 'dom']

    professor_individual = request.args.getlist('professor')
    
    condicao_extra = ''

    if len(professor_individual) > 0:
        condicao_extra = 'and cpf = %s and di = %s' % (professor_individual[0].replace('.', '').replace('-', ''), request.args.getlist('di')[0])


    folha_extra = 0

    if len(request.args.getlist('number')) > 0:
        folha_extra = int(request.args.getlist('number')[0])


    # ---------------------------------------------------------------------------
    # pegar a lista de professores
    sql = "select " + \
          "instancia_calendario, nome, if(di = 0, '-', di) as di, rg, ifnull(digito, '') as digito, ifnull(rs, '-') as rs, ifnull(pv, '') as pv, cpf, " + \
          "cargos_livro_ponto.descricao as cargo, concat(categoria_livro_ponto.letra, ' - ', categoria_livro_ponto.descricao) as categoria, " + \
          "(CASE WHEN afastamento IS NULL THEN REPLACE(concat('Atribuída(s) ', (select count(case when seg != 'ATPC' then 1 end) + count(case when ter != 'ATPC' then 1 end) + count(case when qua != 'ATPC' then 1 end) + count(case when qui != 'ATPC' then 1 end) + count(case when sex != 'ATPC' then 1 end) from horario_livro_ponto where cpf_professor = professor_livro_ponto.cpf), ' aula(s) nesta UE'), 'Atribuída(s) 0 aula(s) nesta UE', 'Não Possui Aulas Atribuídas') ELSE CONCAT(afastamento_livro_ponto.prefixo, afastamento_livro_ponto.descricao) END) AS situacao, " + \
          "ifnull(FNREF, '') as FNREF, jornada_livro_ponto.descricao as jornada, jornada_livro_ponto.qtd as qtd_jornada, " + \
          "(select count(case when seg != 'ATPC' then 1 end) + count(case when ter != 'ATPC' then 1 end) + count(case when qua != 'ATPC' then 1 end) + count(case when qui != 'ATPC' then 1 end) + count(case when sex != 'ATPC' then 1 end) from horario_livro_ponto where cpf_professor = professor_livro_ponto.cpf) as total_aulas, " + \
          "ifnull(professor_livro_ponto.afastamento, '') as afastamento, " + \
          "ifnull(disciplinas.descricao, 'Não Possui') as disciplina, ifnull(obs, '') as obs, " + \
          'ifnull(aulas_outra_ue, 0) as aulas_outra_ue, ' + \
          "case when atpc > 0 or atpl > 0 then concat(' + ', atpc, ' ATPC(s) + ', atpl, ' ATPL(s)') else '' end as atpc, " + \
          "ifnull(atpc + atpl, 0) as soma_atpc, " + \
          'assina_livro, ' + \
          "concat(c.id, ' - ', c.descricao) as sede_c, concat(f.id, ' - ', f.descricao) as sede_f " + \
          "from professor_livro_ponto " + \
          "inner join sede_livro_ponto as c on c.id = professor_livro_ponto.sede_classificacao inner join sede_livro_ponto as f on f.id = professor_livro_ponto.sede_controle_freq " + \
          "left join disciplinas on disciplinas.codigo_disciplina = professor_livro_ponto.disciplina " + \
          "inner join cargos_livro_ponto on cargos_livro_ponto.id = professor_livro_ponto.cargo inner join categoria_livro_ponto on categoria_livro_ponto.id = professor_livro_ponto.categoria left join afastamento_livro_ponto ON afastamento_livro_ponto.id = professor_livro_ponto.afastamento inner join jornada_livro_ponto on jornada_livro_ponto.id = professor_livro_ponto.jornada where ativo = 1 " + condicao_extra + " order by rg"

    professores = banco.executarConsulta(sql)

    pos_inicial = 2278

    sumario = []
    cont_pag = 1
    # ---------------------------------------------------------------------------
    # processar as informações de cada professor
    for professor in professores:

        sumario.append({'professor':professor['nome'], 'pag':cont_pag})
        cont_pag += 1

        professor['pos'] = pos_inicial

        aux_rg = '%08d' % int(professor['rg'])
        professor['rg'] = aux_rg[0:2] + "." + aux_rg[2:5] + "." + aux_rg[5:]

        if (professor['digito'] != ''):
            professor['rg'] = professor['rg'] + "-" + professor['digito']

        aux_rs = '%08d' % int(professor['rs'])
        professor['rs'] = aux_rs[0:2] + "." + aux_rs[2:5] + "." + aux_rs[5:]
        if (professor['pv'] != ''):
            professor['rs'] = professor['rs'] + " / " + '%02d' % int(professor['pv'])   

        aux = '%011d' % int(professor['cpf'])
        professor['cpf'] = aux[:3] + "." + aux[3:6] + "." + aux[6:9] + "-" + aux[9:]               

        pos_inicial += 1124
        
        professor['txt_carga'] = 'Carga Horária:'
        professor['txt_sit'] = 'Afast.:'
        professor['class_afast'] = ''

        if professor['afastamento'] == '':
            professor['txt_sit'] = 'Qtd. Aulas:'
            if professor['total_aulas'] > 0:
                professor['carga'] = "%s aula(s) nesta UE." % professor['total_aulas']
        else:
            professor['class_afast'] = 'red'

        if professor['jornada'] != '-': # quer dizer que é jornada preciso calcular a jornada caso o professor não esteja afastado ou designado
            professor['txt_carga'] = "Carga Suplementar:"

            if professor['afastamento'] == '': # quer dizer que o professor não está afastado

                total = int(professor['total_aulas']) + int(professor['aulas_outra_ue'])
                resto = total - professor['qtd_jornada']

                professor['jornada'] = professor['jornada'] + ' - ' + str(professor['qtd_jornada']) + ' aulas'
                
                if resto > 0:
                    professor['carga'] = "%s aula(s)" % resto
                else:
                    professor['carga'] = "Não Possui"

                if int(professor['sede_c'][:5]) != int(ua_padrao):
                    professor['carga'] = "Sede em outra UE"

        else:
            professor['jornada'] = 'Não Possui'

        # criar quadro de carga horária do professor
        quadro = []
        if int(professor['sede_c'][:5]) == int(ua_padrao): # quadro estará visível somente para professores com sede aqui
            if professor['afastamento'] == '': # quadro estará visível somente para professores que não estão designados ou afastados
                if professor['total_aulas'] > 0: # quadro estará visível apenas para quem tiver aula
                    if professor['jornada'] != 'Não Possui': # para os professores que tem jornada
                        quadro.append({'col1':'<b>RESUMO (horas)</b>', 'col2':'Semanal', 'col3':'Mensal'})
                        
                        horas_jornada = int(round((professor['qtd_jornada'] + professor['soma_atpc']) * 45 / 60, 0))
                        quadro.append({'col1':'JORNADA', 'col2':horas_jornada, 'col3':horas_jornada * 5})

                        horas_suplementar = int(round((int(professor['total_aulas']) + int(professor['aulas_outra_ue']) - professor['qtd_jornada']) * 45 / 60, 0))
                        quadro.append({'col1':'CARGA SUPLEMENTAR', 'col2':horas_suplementar, 'col3':horas_suplementar * 5})

                        quadro.append({'col1':'TOTAL', 'col2':horas_jornada + horas_suplementar, 'col3':horas_jornada * 5 + horas_suplementar * 5})
                    else: # para quem não tem jornada
                        quadro.append({'col1':'<b>RESUMO (horas)</b>', 'col2':'Semanal', 'col3':'Mensal'})
                        quadro.append({'col1':'NÃO POSSUI JORNADA', 'col2':'-', 'col3':'-'})

                        horas_carga = int(round((professor['total_aulas'] + professor['aulas_outra_ue'] + professor['soma_atpc']) * 45 / 60, 0))
                        quadro.append({'col1':'CARGA HORÁRIA', 'col2':horas_carga, 'col3':horas_carga * 5})
                        quadro.append({'col1':'TOTAL', 'col2':horas_carga, 'col3':horas_carga * 5})



        professor['quadro'] = quadro

        # criar quadro de aulas do professor
        professor['quadro_aula'] = banco.executarConsulta(r"select periodo_livro_ponto.descricao as periodo, DATE_FORMAT(inicio, '%H:%i') as inicio, DATE_FORMAT(fim, '%H:%i') as fim, ifnull(seg, '') as seg, ifnull(ter, '') as ter, ifnull(qua, '') as qua, ifnull(qui, '') as qui, ifnull(sex, '') as sex, ifnull(sab, '') as sab, ifnull(dom, '') as dom from horario_livro_ponto inner join periodo_livro_ponto on periodo_livro_ponto.id = horario_livro_ponto.periodo where cpf_professor = " + aux + ' ORDER BY inicio')

        # após processar as informações do professor, ainda preciso criar uma tulpa com a quantidade de aulas por dia da semana
        professor['qtd_aulas_semanais'] = banco.executarConsulta('select count(seg) as seg, count(ter) as ter, count(qua) as qua, count(qui) as qui, count(sex) as sex, count(sab) as sáb, count(dom) as dom from horario_livro_ponto where cpf_professor = %s' % aux)[0]

        aulas_ue = banco.executarConsulta('select * from aulas_outra_ue_livro_ponto where cpf_professor = %s' % aux)
        aulas_outra_ue = {}

        for aula in aulas_ue:
            aulas_outra_ue[aula['semana']] = aula['qtd']

        professor['aulas_ue'] = aulas_outra_ue

        total_aulas_geral = {}

        # finalizar fazendo a soma total
        for dia in dias_semana:

            if dia in aulas_outra_ue:
                total = int(professor['qtd_aulas_semanais'][dia]) + int(aulas_outra_ue[dia])
            else:
                total = int(professor['qtd_aulas_semanais'][dia])

            if total < 1:
                total_aulas_geral[dia] = ''
            else: 
                total_aulas_geral[dia] = total

        professor['total_geral'] = total_aulas_geral


        # ---------------------------------------------------------------------------
        # pegar os dias do mes
        qtd_dias = qtd_dias = calendar.monthrange(ano, mes)[1]
        professor['extra_red'] = ''
        cont_deixou = 0
        top_deixou = 303
        height_deixou = 0
        dias = []

        for i in range(1, qtd_dias + 1):
            date_aux = datetime(ano, mes, i)

            if date_aux.strftime("%a") != 'dom' and date_aux.strftime("%a") != 'sáb': # dias de semana
                evento = banco.executarConsulta("select eventos_calendario.evento as id, cat_letivo.descricao, cat_letivo.qtd_letivo from eventos_calendario inner join cat_letivo on cat_letivo.id = eventos_calendario.evento where ('%s' BETWEEN data_inicial and data_final) and instancia_calendario = %s" % (date_aux.strftime("%y-%m-%d"), professor['instancia_calendario']))

                if len(evento) > 0: # existe um evento

                    if evento[0]['id'] == 11:
                        professor['extra_red'] = '<div class="red-line-extra" style="height: %spx"></div>' % (i * 16)
                    elif evento[0]['id'] == 12:
                        if cont_deixou == 0:
                            top_deixou += ((i - 1) * 16)
                            cont_deixou += 1
                        else:
                            cont_deixou += 1
                            height_deixou = cont_deixou * 16
                            professor['extra_red'] = '<div class="red-line-extra-min" style="top: %spx; height: %spx"></div>' % (top_deixou, height_deixou)
                            

                    if evento[0]['qtd_letivo'] < 1 and (evento[0]['id'] < 7 or evento[0]['id'] in (10, 11, 12)): # significa que é feriado ou dia não letivo e não é replanejamento
                        dias.append({'dia':'%02d' % i, 'Assinatura':evento[0]['descricao'].replace("Sem vínculo", '').replace('Deixou de ministrar aulas nesta U.E.', ''), 'semana':date_aux.strftime("%a"), 'class-bg':'gray', 'class-txt':'black', 'evento':evento[0]['id']})
                    else:
                        dias.append({'dia':'%02d' % i, 'Assinatura':'', 'semana':date_aux.strftime("%a"), 'class-bg':'', 'class-txt':'black', 'evento':evento[0]['id']})
                else:
                    dias.append({'dia':'%02d' % i, 'Assinatura':'', 'semana':date_aux.strftime("%a"), 'class-bg':'', 'class-txt':'black', 'evento':0})
            else: # sábado e domingo
                evento = banco.executarConsulta("select eventos_calendario.evento as id, cat_letivo.descricao, cat_letivo.qtd_letivo from eventos_calendario inner join cat_letivo on cat_letivo.id = eventos_calendario.evento where ('%s' BETWEEN data_inicial and data_final) and instancia_calendario = %s" % (date_aux.strftime("%y-%m-%d"), professor['instancia_calendario']))

                if len(evento) > 0: # existe um evento, talvez seja reposição

                    if evento[0]['id'] == 11:
                        professor['extra_red'] = '<div class="red-line-extra" style="height: %spx"></div>' % (i * 16)
                    elif evento[0]['id'] == 12:
                        if cont_deixou == 0:
                            top_deixou += ((i - 1) * 16)
                            cont_deixou += 1
                        else:
                            height_deixou = cont_deixou * 16
                            professor['extra_red'] = '<div class="red-line-extra-min" style="top: %spx; height: %spx"></div>' % (top_deixou, height_deixou)
                            cont_deixou += 1

                    if evento[0]['qtd_letivo'] > 0: # significa que é reposição de dia letivo
                        dias.append({'dia':'%02d' % i, 'Assinatura':'', 'semana':date_aux.strftime("%a"), 'class-bg':'', 'class-txt':'red', 'evento':evento[0]['id']})
                    else:
                        dias.append({'dia':'%02d' % i, 'Assinatura':evento[0]['descricao'].replace("Sem vínculo", '').replace('Deixou de ministrar aulas nesta U.E.', ''), 'semana':date_aux.strftime("%a"), 'class-bg':'gray', 'class-txt':'red', 'evento':evento[0]['id']})
                else:
                    dias.append({'dia':'%02d' % i, 'Assinatura':date_aux.strftime("%A").title(), 'semana':date_aux.strftime("%a"), 'class-bg':'gray', 'class-txt':'red', 'evento':0})

        professor['dias']   = dias

        linhas = 5 + (30 - len(dias))

        # criar um texto citando os eventos mensais de acordo com o calendário pedagógico
        eventos = banco.executarConsulta('select data_inicial, data_final, cat_letivo.descricao as cat, eventos_calendario.descricao, eventos_calendario.evento as id_evento from eventos_calendario inner join cat_letivo on cat_letivo.id = eventos_calendario.evento where MONTH(data_inicial) = %s and YEAR(data_inicial) = %s and instancia_calendario = %s and eventos_calendario.evento != 11 order by data_inicial' % (mes, ano, professor['instancia_calendario']))
        txt_eventos = ''

        lst_final_eventos = []

        if professor['assina_livro'] == 0:
            lst_final_eventos.append("NÃO ASSINA ESTE LIVRO PONTO")
            eventos = []

        if professor['obs'] != '':
            lst_final_eventos.append(professor['obs'])

        for evento in eventos:

            if evento['id_evento'] == 12:
                if txt_eventos != '':
                    lst_final_eventos.append(txt_eventos[:-2])
                    txt_eventos = ''

                txt_descricao = evento['cat']
                # definir como aparecerá no campo observação, se tiver os detalhes, serão os detalhes, senão só a descrição básica
                if evento['descricao'] is not None:
                    txt_descricao = evento['descricao']

                txt_eventos += 'A partir de %s: %s, ' % (evento['data_inicial'].strftime('%d'), txt_descricao)
            else:
                txt_descricao = evento['cat']
                # definir como aparecerá no campo observação, se tiver os detalhes, serão os detalhes, senão só a descrição básica
                if evento['descricao'] is not None:
                    txt_descricao = evento['descricao']

                if evento['data_inicial'] == evento['data_final']: # evento de apenas um dia
                    txt_eventos += 'Dia %s: %s, ' % (evento['data_inicial'].strftime('%d'), txt_descricao)
                else: # evento de período
                    txt_eventos += 'De %s até %s: %s, ' % (evento['data_inicial'].strftime('%d'), evento['data_final'].strftime('%d'), txt_descricao)

            if len(txt_eventos) > 100:
                lst_final_eventos.append(txt_eventos[:-2])
                txt_eventos = ''

        lst_final_eventos.append(txt_eventos[:-2])
        professor['eventos'] = lst_final_eventos


    info_assinatura = banco.executarConsulta("select (select valor from config where id_config = 'diretor_ponto') as diretor, (select valor from config where id_config = 'rg_diretor_ponto') as rg_diretor, (select valor from config where id_config = 'secretario_ponto') as secretario, (select valor from config where id_config = 'rg_secretario_ponto') as rg_secretario, (select valor from config where id_config = 'cargo_secretario_ponto') as cargo_secretario")[0]

    sumario.sort(key=lambda t: (locale.strxfrm(t['professor'])))

    # ---------------------------------------------------------------------------
    # renderizar template
    return render_template('render_pdf/render_livro_ponto.jinja', professores=professores, data='%s / %s' % (getMes(mes), ano), dias=dias, eventos=lst_final_eventos, linhas=linhas, info_assinatura=info_assinatura, dias_semana=dias_semana, sumario=sumario, folha_extra=folha_extra)


@app.route('/render_certificados_conclusao',  methods=['GET', 'POST'])
def render_certificados_conclusao():
    if request.method == 'GET':
        classe = request.args.getlist('classe')[0]

        tipo_ensino = banco.executarConsulta('select tipo_ensino from turma where num_classe = %s' % classe)[0]['tipo_ensino']

        if  tipo_ensino > 1: # eja
            nome_vice = banco.executarConsultaVetor('select valor from config where id_config = "vice-eja-nome"')[0]
            rg_vice = banco.executarConsultaVetor('select valor from config where id_config = "vice-eja-rg"')[0]
        else: # regular
            nome_vice = banco.executarConsultaVetor('select valor from config where id_config = "vice-regular-nome"')[0]
            rg_vice = banco.executarConsultaVetor('select valor from config where id_config = "vice-regular-rg"')[0]  


        if tipo_ensino == 3:
            modalidade = "Ensino Fundamental"
        else:
            modalidade = 'Ensino Médio'

        alunos = banco.executarConsulta(r"select aluno.nome, aluno.rg, serie, aluno.sexo, DATE_FORMAT (aluno.nascimento,'%d/%m/%Y') as nascimento, DATE_FORMAT (vinculo_alunos_turmas.fim_mat,'%d/%m/%Y') as fim from vinculo_alunos_turmas  inner join aluno on aluno.ra = vinculo_alunos_turmas.ra_aluno where num_classe = " + classe + " and situacao in (1, 6) and serie in (3, 4, 12) order by nome")

        for aluno in alunos:
            aluno['nome_assinatura'] = aluno['nome'].title().replace('Da ', 'da ').replace("De ", "de ").replace("Do ", 'do ').replace("Dos ", 'dos ')
            aluno['nascimento'] = aluno['nascimento'][0:2] + ' de ' + getMes(aluno['nascimento'][3:5]).lower() + ' de ' + aluno['nascimento'][6:10]
            aluno['fim'] = aluno['fim'][0:2] + ' de ' + getMes(aluno['fim'][3:5]).lower() + ' de ' + aluno['fim'][6:10]
            if aluno['sexo'] == 'M':
                aluno['texto_final'] = 'O Diretor da Escola confere, nos termos do inciso VII, artigo 24 da Lei 9394/96, a <b>%s</b>, nascido em %s, o presente CERTIFICADO por haver concluído o %s, em %s.' % (aluno['nome'], aluno['nascimento'], modalidade, aluno['fim'])
            else:
                aluno['texto_final'] = 'O Diretor da Escola confere, nos termos do inciso VII, artigo 24 da Lei 9394/96, a <b>%s</b>, nascida em %s, o presente CERTIFICADO por haver concluído o %s, em %s.' % (aluno['nome'], aluno['nascimento'], modalidade, aluno['fim'])





    nome_diretor = banco.executarConsultaVetor('select valor from config where id_config = "diretor_ponto"')[0]
    rg_diretor = banco.executarConsultaVetor('select valor from config where id_config = "rg_diretor_ponto"')[0]

    return render_template('render_pdf/render_certificado.jinja', alunos=alunos, nome_vice=nome_vice, nome_diretor=nome_diretor, rg_diretor=rg_diretor, rg_vice=rg_vice)


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
                "if(fim_mat <= '" + fim  + "' and situacao <> 6 and situacao <> 10, situacao.abv1, if(matricula > '" + inicio  + r"', DATE_FORMAT(matricula,'%d/%m/%Y'), '')) as mat, " + \
                "if(fim_mat < '" + fim  + r"', DATE_FORMAT(fim_mat,'%d/%m/%Y'), '') as fim_mat, " + \
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
                        notas = banco.executarConsulta('select notas.disciplina, nota, falta, ac, media from notas left join conceito_final on conceito_final.disciplina = notas.disciplina and conceito_final.num_classe = notas.num_classe and conceito_final.ra_aluno = notas.ra_aluno where notas.ra_aluno = %s and notas.num_classe = %s and bimestre = %s' % (aluno['ra_bruto'], itf['num_classe_if'], bimestre))
                        
                        for n in notas:
                            notas_if[n['disciplina']] = {'nota':n['nota'], 'falta':n['falta'], 'ac':n['ac'], 'media':n['media']}

                    aluno['if'] = notas_if

                    sql = 'select ' + \
	                      'sum(falta) as total_faltas_if, ' + \
                          'sum(ac) as total_ac_if, ' + \
                          'round(100 - ((select sum(falta) from notas where ra_aluno = ' + str(aluno['ra_bruto']) + ' and bimestre = ' + str(bimestre) + ' and num_classe in (' + turmas_if_concat + ')) * 100 / (select sum(aulas_dadas) from vinculo_prof_disc where bimestre = ' + str(bimestre) + ' and num_classe in (select num_classe from notas where ra_aluno = ' + str(aluno['ra_bruto']) + ' and bimestre = ' + str(bimestre) + ' and num_classe in (' + turmas_if_concat + ') group by(num_classe)))), 0) as freq_if ' + \
                          'from notas ' + \
                          'where num_classe in (' + turmas_if_concat + ') and bimestre = ' + str(bimestre) + ' and ra_aluno = ' + str(aluno['ra_bruto'])

                    freq_if = banco.executarConsulta(sql)[0]

                    sql = 'select ' + \
	                      'sum(falta) as total_faltas_if, ' + \
                          'sum(ac) as total_ac_if, ' + \
                          'round(100 - ((select (sum(falta) - sum(ac)) from notas where ra_aluno = ' + str(aluno['ra_bruto']) + ' and num_classe in (' + turmas_if_concat + ')) * 100 / (select sum(aulas_dadas) from vinculo_prof_disc where num_classe in (select num_classe from notas where ra_aluno = ' + str(aluno['ra_bruto']) + ' and num_classe in (' + turmas_if_concat + ') group by(num_classe)))), 0) as freq_if ' + \
                          'from notas ' + \
                          'where num_classe in (' + turmas_if_concat + ') and ra_aluno = ' + str(aluno['ra_bruto'])
                    
                    freq_if_final = banco.executarConsulta(sql)[0]


                    aluno['freq_if'] = freq_if
                    aluno['freq_if_final'] = freq_if_final

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

            # verificar se existe conselho final
            turma['lista_conceito_final'] = []
            turma['conceito_final'] = False
            lista = {}

            if turma['desc_duracao'] != 'Anual' and bimestre == '2' or bimestre == '4': # significa que é o último bimestre
                turma['conceito_final'] = True

            if turma['conceito_final']:
                # criar lista dos alunos
                sql = "SELECT num_chamada as num, ifnull(aluno.rm, '-') as rm, serie, aluno.nome, " \
                    'concat(LPAD(SUBSTR(ra_aluno, -9, 1), 1, 0), SUBSTR(ra_aluno, -8, 2), ".", substr(ra_aluno, -6, 3), ".", substr(ra_aluno, -3, 3), "-", aluno.digito_ra) as ra, ' \
                    r"ra_aluno as ra_bruto, situacao.abv1 as mat, DATE_FORMAT(fim_mat,'%d/%m/%Y') as fim_mat, " \
                    "CASE WHEN sexo = 'M' THEN situacao.descricao ELSE situacao.desc_fem END as desc_ata, " \
                    '(select sum(falta) from notas where ra_aluno = ra_bruto and num_classe = ' + str(turma['num_classe']) + ') as total_faltas, ' \
                    'round(100 - ((select (sum(falta) - sum(ac)) from notas where ra_aluno = ra_bruto and num_classe = ' + str(turma['num_classe']) + ') * 100 / (select sum(aulas_dadas) from  vinculo_prof_disc where num_classe = ' + str(turma['num_classe']) + ')), 0) as freq, ' \
                    '(select sum(ac) from notas where ra_aluno = ra_bruto and num_classe = ' + str(turma['num_classe']) + ') as ac ' \
                    'from vinculo_alunos_turmas inner join aluno ON aluno.ra = vinculo_alunos_turmas.ra_aluno ' \
                    'inner join situacao ON vinculo_alunos_turmas.situacao = situacao.id ' \
                    'where num_classe = ' + str(turma['num_classe']) + ' order by num_chamada'
                
                turma['top_lista_conselho_final'] = top
                top += limite
                turma['situacao_final'] = banco.executarConsulta('SELECT (select count(situacao) from vinculo_alunos_turmas where num_classe = %s and situacao = 6 ) as aprovados, (select count(situacao) from vinculo_alunos_turmas where num_classe = %s and situacao = 10 ) as reprovados, (select count(situacao) from vinculo_alunos_turmas where num_classe = %s and situacao <> 6 and situacao <> 10 ) as outros' % (turma['num_classe'], turma['num_classe'], turma['num_classe']))[0]
                turma['lista_conceito_final']  = banco.executarConsulta(sql)

                for aluno in turma['lista_conceito_final']:
                    aluno['nome'] = aluno['nome'].title().replace('Da ', 'da ').replace("De ", "de ").replace("Do ", 'do ').replace("Dos ", 'dos ')                 

                    # pegar notas
                    for item in turma['disciplinas']:
                        sql = 'SELECT vinculo_alunos_turmas.ra_aluno, vinculo_alunos_turmas.num_chamada as num, media '
                        sql += 'from conceito_final '
                        sql += 'inner join vinculo_alunos_turmas on vinculo_alunos_turmas.ra_aluno = conceito_final.ra_aluno and vinculo_alunos_turmas.num_classe = conceito_final.num_classe '
                        sql += 'where conceito_final.disciplina = %s and conceito_final.num_classe = %s order by num_chamada' % (item['disciplina'], turma['num_classe'])
                        
                        notas = banco.executarConsulta(sql)

                        for aluno in notas:
                            lista[aluno['ra_aluno']] = aluno

                        item['conceito_final'] = lista

                turma['top_mapao_conselho_final'] = top
                top += limite
                turma['top_verso_conselho_final'] = top
                top += limite
                turma['top_blank_if_final'] = top
                top += limite                

                if len(turmas_if) > 0:
                    turma['top_if_final'] = top
                    top += limite
                    turma['top_if_final_verso'] = top
                    top += limite


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
                "if(fim_mat <= '" + fim  + "' and situacao <> 6 and situacao <> 10, situacao.abv1, if(matricula > '" + inicio  + r"', DATE_FORMAT(matricula,'%d/%m/%Y'), '')) as mat, " + \
                "if(fim_mat < '" + fim  + r"', DATE_FORMAT(fim_mat,'%d/%m/%Y'), '') as fim_mat, " + \
                "ifnull((SELECT group_concat(dificuldade) from alunos_dificuldades where num_classe = " + num_classe + " and bimestre = " + bimestre + " and ra = aluno.ra), '') as dificuldade, " + \
                '(select sum(falta) from notas where ra_aluno = ra_bruto and bimestre = ' + bimestre + ' and num_classe = ' + num_classe + ') as total_faltas, ' + \
                'round(100 - ((select sum(falta) from notas where ra_aluno = ra_bruto and bimestre = ' + bimestre + ' and num_classe = ' + num_classe + ') * 100 / (select sum(aulas_dadas) from  vinculo_prof_disc where bimestre = ' + bimestre + ' and num_classe = ' + num_classe + ')), 0) as freq, ' + \
                '(select sum(ac) from notas where ra_aluno = ra_bruto and bimestre = ' + bimestre + ' and num_classe = ' + num_classe + ') as ac ' + \
                "from vinculo_alunos_turmas " + \
                'inner join aluno ON aluno.ra = vinculo_alunos_turmas.ra_aluno ' + \
                'inner join situacao ON vinculo_alunos_turmas.situacao = situacao.id ' + \
                "where num_classe = " + num_classe  + " and matricula <= '" + fim  + "' order by num_chamada"

        alunos = banco.executarConsulta(sql)

        if (len(alunos) < 1):
            sql = 'SELECT ' + \
                "num_chamada as num, ifnull(aluno.rm, '-') as rm, aluno.nome, " + \
                'concat(LPAD(SUBSTR(ra_aluno, -9, 1), 1, 0), SUBSTR(ra_aluno, -8, 2), ".", substr(ra_aluno, -6, 3), ".", substr(ra_aluno, -3, 3), "-", aluno.digito_ra) as ra, ' + \
                "ra_aluno as ra_bruto, " + \
                "if(fim_mat <= '" + fim  + "', situacao.abv1 and situacao <> 6 and situacao <> 10, if(matricula > '" + inicio  + r"', DATE_FORMAT(matricula,'%d/%m/%Y'), '')) as mat, " + \
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
            print(aluno)
            if aluno['fim_mat'] == '' or aluno['mat'] == 'APROV' or aluno['mat'] == 'RETD':
                ativos += 1
            maximo += 1
            if (aluno['dificuldade'] != ''):
                lista = aluno['dificuldade'].split(',')
                aluno['dificuldade'] = converterLista(lista)
                
                #print(aluno)

        total['total_ativos'] = ativos
        total['total'] = maximo

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
                        notas = banco.executarConsulta('select notas.disciplina, nota, falta, ac, media from notas left join conceito_final on conceito_final.disciplina = notas.disciplina and conceito_final.num_classe = notas.num_classe and conceito_final.ra_aluno = notas.ra_aluno where notas.ra_aluno = %s and notas.num_classe = %s and bimestre = %s' % (aluno['ra_bruto'], itf['num_classe_if'], bimestre))

                        for n in notas:
                            notas_if[n['disciplina']] = {'nota':n['nota'], 'falta':n['falta'], 'ac':n['ac'], 'media':n['media']}

                    aluno['if'] = notas_if

                    sql = 'select ' + \
	                      'sum(falta) as total_faltas_if, ' + \
                          'sum(ac) as total_ac_if, ' + \
                          'round(100 - ((select sum(falta) from notas where ra_aluno = ' + str(aluno['ra_bruto']) + ' and bimestre = ' + str(bimestre) + ' and num_classe in (' + turmas_if_concat + ')) * 100 / (select sum(aulas_dadas) from vinculo_prof_disc where bimestre = ' + str(bimestre) + ' and num_classe in (select num_classe from notas where ra_aluno = ' + str(aluno['ra_bruto']) + ' and bimestre = ' + str(bimestre) + ' and num_classe in (' + turmas_if_concat + ') group by(num_classe)))), 0) as freq_if ' + \
                          'from notas ' + \
                          'where num_classe in (' + turmas_if_concat + ') and bimestre = ' + str(bimestre) + ' and ra_aluno = ' + str(aluno['ra_bruto'])

                    freq_if = banco.executarConsulta(sql)[0]

                    sql = 'select ' + \
	                      'sum(falta) as total_faltas_if, ' + \
                          'sum(ac) as total_ac_if, ' + \
                          'round(100 - ((select (sum(falta) - sum(ac)) from notas where ra_aluno = ' + str(aluno['ra_bruto']) + ' and num_classe in (' + turmas_if_concat + ')) * 100 / (select sum(aulas_dadas) from vinculo_prof_disc where num_classe in (select num_classe from notas where ra_aluno = ' + str(aluno['ra_bruto']) + ' and num_classe in (' + turmas_if_concat + ') group by(num_classe)))), 0) as freq_if ' + \
                          'from notas ' + \
                          'where num_classe in (' + turmas_if_concat + ') and ra_aluno = ' + str(aluno['ra_bruto'])
                    
                    freq_if_final = banco.executarConsulta(sql)[0]
                    
                    aluno['freq_if'] = freq_if  
                    aluno['freq_if_final'] = freq_if_final

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

        # verificar se o bimestre é o último, se for será necessário também desenhar o quinto conceito
        lista_conceito_final = []
        conceito_final = False
        situacao_final = None

        if turma['desc_duracao'] != 'Anual' and bimestre == '2' or bimestre == '4': # significa que é o último bimestre
            conceito_final = True

        if conceito_final:
            # pegar lista do conselho final
            sql = "SELECT num_chamada as num, ifnull(aluno.rm, '-') as rm, serie, aluno.nome, " \
                  'concat(LPAD(SUBSTR(ra_aluno, -9, 1), 1, 0), SUBSTR(ra_aluno, -8, 2), ".", substr(ra_aluno, -6, 3), ".", substr(ra_aluno, -3, 3), "-", aluno.digito_ra) as ra, ' \
                  r"ra_aluno as ra_bruto, situacao.abv1 as mat, DATE_FORMAT(fim_mat,'%d/%m/%Y') as fim_mat, " \
                  "CASE WHEN sexo = 'M' THEN situacao.descricao ELSE situacao.desc_fem END as desc_ata, " \
                  '(select sum(falta) from notas where ra_aluno = ra_bruto and num_classe = ' + num_classe + ') as total_faltas, ' \
                  'round(100 - ((select (sum(falta) - sum(ac)) from notas where ra_aluno = ra_bruto and num_classe = ' + num_classe + ') * 100 / (select sum(aulas_dadas) from  vinculo_prof_disc where num_classe = ' + num_classe + ')), 0) as freq, ' \
                  '(select sum(ac) from notas where ra_aluno = ra_bruto and num_classe = ' + num_classe + ') as ac ' \
                  'from vinculo_alunos_turmas inner join aluno ON aluno.ra = vinculo_alunos_turmas.ra_aluno ' \
                  'inner join situacao ON vinculo_alunos_turmas.situacao = situacao.id ' \
                  'where num_classe = ' + num_classe + ' order by num_chamada'
            
            lista_conceito_final = banco.executarConsulta(sql)

            for aluno in lista_conceito_final:
                aluno['nome'] = aluno['nome'].title().replace('Da ', 'da ').replace("De ", "de ").replace("Do ", 'do ').replace("Dos ", 'dos ') 

            situacao_final = banco.executarConsulta('SELECT (select count(situacao) from vinculo_alunos_turmas where num_classe = %s and situacao = 6 ) as aprovados,   (select count(situacao) from vinculo_alunos_turmas where num_classe = %s and situacao = 10 ) as reprovados, (select count(situacao) from vinculo_alunos_turmas where num_classe = %s and situacao <> 6 and situacao <> 10 ) as outros' % (num_classe, num_classe, num_classe))[0]


            # pegar notas do conselho final
            for item in disciplinas:
                sql = 'SELECT vinculo_alunos_turmas.ra_aluno, vinculo_alunos_turmas.num_chamada as num, media '
                sql += 'from conceito_final '
                sql += 'inner join vinculo_alunos_turmas on vinculo_alunos_turmas.ra_aluno = conceito_final.ra_aluno and vinculo_alunos_turmas.num_classe = conceito_final.num_classe '
                sql += 'where conceito_final.disciplina = %s and conceito_final.num_classe = %s order by num_chamada' % (item['disciplina'], num_classe)

                notas = banco.executarConsulta(sql)

                item['conceito_final'] = {}

                for aluno in notas:
                    item['conceito_final'][aluno['ra_aluno']] = aluno


            # pegar conceito final do IF quando houver
            #print(turmas_if)


        return render_template('render_pdf/render_conselho_bimestre.jinja', alunos=alunos, turma=turma, disciplinas=disciplinas, freq=freq, total=total, bimestre=bimestre, fim_bimestre=fim_bimestre, dificuldades=dificuldades, turmas_if=turmas_if, colspan_if=colspan_if, lista_conceito_final=lista_conceito_final, situacao_final=situacao_final)

@app.route('/render_lista', methods=['GET', 'POST'])
def render_lista():

    if request.method == 'GET':
        tipo = request.args.getlist('tipo')[0]
        num_classe = request.args.getlist('num_classe')[0]
        order = request.args.getlist('order')[0]
        
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

            # pegar total
            if head['status'] == 'andamento':
                total = banco.executarConsulta('select (select count(*) from vinculo_alunos_turmas where num_classe = %s) as total, (select count(*) from vinculo_alunos_turmas where num_classe = %s and situacao = 1) as total_ativos' % (num_classe, num_classe))[0]
                desc_total = 'ativos'
                alunos =  banco.executarConsulta('SELECT ' + \
                                "num_chamada as num, ifnull(aluno.rm, '-') as rm, aluno.nome, vinculo_alunos_turmas.serie, " + \
                                'concat(LPAD(SUBSTR(ra_aluno, -9, 1), 1, 0), SUBSTR(ra_aluno, -8, 2), ".", substr(ra_aluno, -6, 3), ".", substr(ra_aluno, -3, 3), "-", aluno.digito_ra) as ra, ' + \
                                "if(fim_mat < '" + info['fim']  + "', situacao.abv1, if(matricula > '" + info['inicio']  + r"', DATE_FORMAT(matricula,'%d/%m/%Y'), '')) as mat, " + \
                                "if(fim_mat < '" + info['fim']  + r"', DATE_FORMAT(fim_mat,'%d/%m/%Y'), '') as fim_mat, " + \
                                "DATE_FORMAT(nascimento, '%d/%m/%Y') as nascimento, aluno.sexo, ifnull(rg, '-') as rg, ifnull(concat(LPAD(SUBSTR(cpf, -11, 1), 1, 0), SUBSTR(cpf, -10, 2), '.', substr(cpf, -8, 3), '.', substr(cpf, -5, 3), '-', substr(cpf, -2, 2)), '-') as cpf " + \
                                "from vinculo_alunos_turmas " + \
                                'inner join aluno ON aluno.ra = vinculo_alunos_turmas.ra_aluno ' + \
                                'inner join situacao ON vinculo_alunos_turmas.situacao = situacao.id ' + \
                                "where num_classe = " + num_classe  + " " + order)                
            else:
                total = banco.executarConsulta('select (select count(*) from vinculo_alunos_turmas where num_classe = %s) as total, (select count(*) from vinculo_alunos_turmas where num_classe = %s and situacao = 6) as total_ativos' % (num_classe, num_classe))[0]
                desc_total = 'aprovados'
                alunos =  banco.executarConsulta('SELECT ' + \
                                "num_chamada as num, ifnull(aluno.rm, '-') as rm, aluno.nome, vinculo_alunos_turmas.serie, " + \
                                'concat(LPAD(SUBSTR(ra_aluno, -9, 1), 1, 0), SUBSTR(ra_aluno, -8, 2), ".", substr(ra_aluno, -6, 3), ".", substr(ra_aluno, -3, 3), "-", aluno.digito_ra) as ra, ' + \
                                "if(fim_mat < '" + info['fim']  + "', situacao.abv1, if(matricula > '" + info['inicio']  + r"', DATE_FORMAT(matricula,'%d/%m/%Y'), '')) as mat, " + \
                                "if(fim_mat < '" + info['fim']  + r"', DATE_FORMAT(fim_mat,'%d/%m/%Y'), UPPER(if(sexo = 'F', situacao.desc_fem, situacao.descricao))) as fim_mat, " + \
                                "DATE_FORMAT(nascimento, '%d/%m/%Y') as nascimento, aluno.sexo, ifnull(rg, '-') as rg, ifnull(concat(LPAD(SUBSTR(cpf, -11, 1), 1, 0), SUBSTR(cpf, -10, 2), '.', substr(cpf, -8, 3), '.', substr(cpf, -5, 3), '-', substr(cpf, -2, 2)), '-') as cpf " + \
                                "from vinculo_alunos_turmas " + \
                                'inner join aluno ON aluno.ra = vinculo_alunos_turmas.ra_aluno ' + \
                                'inner join situacao ON vinculo_alunos_turmas.situacao = situacao.id ' + \
                                "where num_classe = " + num_classe  + " " + order)


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
                alunos = banco.executarConsulta('select num_chamada, aluno.nome, (select turma.nome_turma from vinculo_alunos_turmas inner join turma on vinculo_alunos_turmas.num_classe = turma.num_classe where ra_aluno = vinculo_alunos_if.ra_aluno and (situacao = 1 or situacao = 6) order by fim_mat desc limit 1) as serie from vinculo_alunos_if inner join aluno on aluno.ra = ra_aluno where num_classe_if = %s and situacao in (1, 16) order by num_chamada' % classe['num_classe_if'])
                
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

        elif tipo == 'assinatura':
            titulo = request.args.getlist('titulo')[0]

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
                            "where num_classe = " + num_classe  + " and situacao = 1 " + order)
            
            escola = banco.executarConsulta("select descricao from sede_livro_ponto where id = (select valor from config where id_config = 'ua_sede')")[0]['descricao']

            nome_turma = banco.executarConsulta(f'select nome_turma from turma where num_classe = {num_classe}')[0]['nome_turma']

            for item in alunos:
                item['nome'] = item['nome'].title().replace('Da ', 'da ').replace("De ", "de ").replace("Do ", 'do ').replace("Dos ", 'dos ')

            return render_template('render_pdf/render_lista_assinatura.jinja', titulo=titulo, alunos=alunos, escola=escola.upper(), nome_turma=nome_turma)

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

            elif aux_info['tipo'] == 4: # declaração de matrícula padrão com frequência

                match (aux_info['info_classe']['tipo_ensino']):
                    case 1:
                        serie = "na <b>%sª série do %s,</b>" % (aux_info['info_classe']['serie'], aux_info['info_classe']['tipo_ensino_desc'])
                    case 3:
                        serie = 'na <b>%sª série (Correspondente ao %s) do %s,</b>' % (aux_info['info_classe']['serie'], series_fund[aux_info['info_classe']['serie']], aux_info['info_classe']['tipo_ensino_desc'])
                    case 4:
                        serie = 'no <b>%sº Termo do %s,</b>' % (aux_info['info_classe']['serie'], aux_info['info_classe']['tipo_ensino_desc'])


                titulo = 'DECLARAÇÃO DE MATRÍCULA'
                if aux_info['bimestre'] > 0:
                    texto += ' é alun%s regularmente matriculad%s %s com frequência de <b>%s%s</b> registrada até o final do <b>%sº bimestre.</b>' % (pronome, pronome, serie, aux_info['percent'], r'%', aux_info['bimestre'])
                else:
                    list_serie = list(serie)
                    list_serie[-5] = '.'
                    texto += ' é alun%s regularmente matriculad%s %s' % (pronome, pronome, "".join(list_serie))

                
            data_atual = datetime.now()
            data_formatada = data_atual.strftime("%d de %B de %Y")

            return render_template('render_pdf/render_declaracao.jinja', texto=texto, titulo=titulo, data=data_formatada, cor=num_classe, anos=aux_info['anos'], pronome=pronome)
        
        elif tipo == 'ficha_mat':

            rm = request.args.getlist('rm')[0]
            ra = request.args.getlist('ra')[0]
            rg = request.args.getlist('rg')[0]
            ano = request.args.getlist('ano')[0]
            if rg == '-':
                rg = '&nbsp;'
            cpf = request.args.getlist('cpf')[0]
            if cpf == '-':
                cpf = '&nbsp;'
            sexo = request.args.getlist('sexo')[0]
            nome = request.args.getlist('nome')[0]
            nome_social = request.args.getlist('nome_social')[0]
            pai = request.args.getlist('pai')[0]
            mae = request.args.getlist('mae')[0]
            cidade = request.args.getlist('cidade')[0]
            estado = request.args.getlist('estado')[0]
            nascimento = request.args.getlist('nascimento')[0]
            endereco = request.args.getlist('endereco')[0]
            telefone = request.args.getlist('telefone')[0]
            email = request.args.getlist('email')[0]
            serie_desc = request.args.getlist('serie_desc')[0]
            serie_simples = request.args.getlist('serie_simples')[0]
            fund = request.args.getlist('fund')[0]

            if fund == '':
                fund = '&nbsp;'

            medio = request.args.getlist('medio')[0]

            if medio == '':
                medio = '&nbsp;'

            # teste in http://localhost/render_lista?tipo=ficha_mat&num_classe=0&rm=5610&ra=109.789.948-2&rg=68.645.560-5&cpf=598.165.948-38&sexo=F&nome=GABRIELLA+GUIMAR%C3%83ES+PRADO&pai=DOUGLAS+PEREIRA+PRADO&mae=FERNANDA+DE+ALMEIDA+GUIMARAES&cidade=GUARATINGUET%C3%81&estado=SP&nascimento=29/07/2006&endereco=Rua+Dois,+65,+Compl.A,+Pit%C3%A9u,+Cachoeira+Paulista&telefone=(12)+99251-4094&email=leticiavictoria9035@gmail.com&serie=9%C2%BA+ANO&fund=X&medio=
            print(ano)

            return render_template('render_pdf/render_ficha_matricula.jinja', rm=rm, ra=ra, rg=rg, cpf=cpf, cor='white', sexo=sexo, nome=nome, nome_social=nome_social, pai=pai, mae=mae, cidade=cidade, estado=estado, nascimento=nascimento, endereco=endereco, telefone=telefone, email=email, serie=serie_desc, fund=fund, medio=medio, hoje=hojePorExtenso(), serie_simples=serie_simples, ano=ano)
        
        elif tipo == "ata_final":

            info = []
            ls_final = []
            ls_keys = []

            with open('staticFiles/uploads/info.json', 'r', encoding='utf-8-sig') as file:
                info = json.load(file)

            dados = []
            with open('staticFiles/uploads/table.json', 'r', encoding='utf-8-sig') as file:
                dados = json.load(file)

            for item in dados:
                dict = {'num':item['Nº'], 'nome':item['ALUNO'].title().replace('Da ', 'da ').replace('De ', 'de ').replace("Do ", "do ").replace("Dos ", "dos "), 'sit':item['RESULTADO FINAL'].replace("RetidoRendimento", "Retido").replace('RetidoFrequencia', 'Retido')}

                ls_keys = []
                key_list = item.keys()
                for key in key_list:
                    if key not in ('Nº', 'RA', 'ALUNO', 'SITUAÇÃO ALUNO', 'RESULTADO FINAL'):
                        new_key = key.replace(". ", '').replace("L.", "").replace("LIN", "POR")[0:3].replace("PRO", 'PV')
                        ls_keys.append(new_key)
                        dict[new_key] = item[key].replace(',00', '')


                ls_final.append(dict)
            print(ls_final)

            return render_template('render_pdf/render_ata_final.jinja', info=info, dados=ls_final, ls_keys=ls_keys)

@app.route('/atualizar_matriz_auto', methods=['GET', 'POST'])
async def atualizar_matriz_auto():

    info = request.json

    num_classe = info['num_classe']

    browser = await launch(
        {'headless': False},
        handleSIGINT=False,
        handleSIGTERM=False,
        handleSIGHUP=False
    )

    page = await browser.newPage()
    # Navigate the page to a URL
    await page.goto('https://sed.educacao.sp.gov.br/')

    # Set screen size
    await page.setViewport({'width':1366, 'height':768})

    await page.waitForSelector("#name")

    # Type into login
    await page.type('#name', 'rg490877795sp')
    await page.type('#senha', 'BGarden@FF8')


    await page.click("#botaoEntrar")

    await page.waitForSelector("#decorMenuFilterTxt")    

    await page.goto('https://sed.educacao.sp.gov.br//NCA/ColetaTurma/TurmaClasse/Index', {'waitUntil':'networkidle0'})

    await page.waitForSelector('.blockUI', {'hidden':True})

    await page.evaluate('''$("#divClasse").removeAttr('style');''')

    await page.evaluate('''$("#divFiltros").attr('style', 'display:none');''')

    await page.evaluate('''$("#tipoPesquisa").val('1');''')

    await page.type('#numeroClassePesq', f'{num_classe}')

    print(num_classe)

    await page.click('#btnPesquisar')

    await page.waitForSelector('#tabelaDados')

    script = await page.evaluate('''$("#tabelaDados tbody td:eq(10) a").attr('onclick');''')

    await page.evaluate(script)

    await page.waitForSelector('.blockUI', {'hidden':True})

    await page.waitForSelector('#btnEditarFundamento')

    await page.evaluate('VisualizarFundamentoLegal();')

    await page.waitForSelector('#divVisualizarFundamentoLegal')

    rows = await page.evaluate('''() => {
        const rows = document.querySelectorAll('#divVisualizarFundamentoLegal table tbody tr');
        return Array.from(rows, row => {
            const cells = row.querySelectorAll('td, th');
            return Array.from(cells, cell => cell.innerText);
        });
    }''')

    lista = []

    for item in rows:
        try:
            tipo = banco.executarConsultaVetor(f"select id from tipo_disc_matriz where desc_completa like '{item[1]}'")[0]
            disc = item[0].split(' - ')[0]
            area = banco.executarConsultaVetor(f'select area from matriz_curricular where disc_disciplina = {disc} limit 1')[0]
            qtd = item[2].replace('\n', '').replace(" ", "")

            lista.append({'num_classe':num_classe, 'tipo':tipo, 'disc':disc, 'area':area, 'qtd':qtd, 'minutos':info['minutos']})
        except Exception as error:
            print("An exception occurred:", error) # An exception occurred: division by zero

    await browser.close()

    return jsonify(lista)


@app.route('/atualizar_lista_auto', methods=['GET', 'POST'])
async def atualizar_lista_auto():

    ano = request.json
    print(ano)

    browser = await launch(
        {'headless': False},
        handleSIGINT=False,
        handleSIGTERM=False,
        handleSIGHUP=False
    )

    page = await browser.newPage()
    # Navigate the page to a URL
    await page.goto('https://sed.educacao.sp.gov.br/')

    # Set screen size
    await page.setViewport({'width':1366, 'height':768})

    await page.waitForSelector("#name")

    # Type into login
    await page.type('#name', 'rg490877795sp')
    await page.type('#senha', 'BGarden@FF8')


    await page.click("#botaoEntrar")

    await page.waitForSelector("#decorMenuFilterTxt")


    # pegar lista das turmas
    turmas = banco.executarConsulta('select num_classe, nome_turma, duracao.descricao as desc_duracao from turma inner join duracao on duracao.id = turma.duracao where ano = %s order by duracao, tipo_ensino, nome_turma' % ano)

    for turma in turmas:  
        
        await page.goto('https://sed.educacao.sp.gov.br//NCA/RelacaoAlunosClasse/Index', {'waitUntil':'networkidle0'})

        await page.type('#numeroClassePesq', str(turma['num_classe']))

        await page.evaluate('''() => {
            pesquisar();
        }''')    

        socketio.emit('update_info', '<b>Atualizando dados da %s - %s (%s)</b>' % (turma['nome_turma'], turma['desc_duracao'], ano))

        await page.waitForSelector("#tabelaDadosClasse")

        code = await page.evaluate('$("#tabelaDadosClasse").find("tbody").find("a").attr("onclick");')

        await page.evaluate(code + ';')

        await page.waitForSelector("#tabelaAlunosClasse")

        tabela = await page.evaluate('''() => {
            let table = $("#tabelaAlunosClasse").DataTable();

            table.order( [1,'asc'] ).draw();

            var columnNames = table.columns().header().toArray().map(header => $(header).text());

            var dataDictList = table.rows().data().toArray().map(row => {
                let rowData = {};
                columnNames.forEach((colName, index) => {
                    rowData[colName] = row[index];
                });
                return rowData;
            });    

            return Promise.resolve(dataDictList);
        }''')

        lista = []

        for item in tabela:

            nascimento = "'" + converterDataMySQL(item['Data de Nascimento']) + "'"
            inicio_mat = "'" + converterDataMySQL(item['Data Início Matrícula']) + "'"
            fim_mat = "'" + converterDataMySQL(item['Data Fim Matrícula']) + "'"


            aluno = {'ra':int(item['RA']), 'digito':"'" + item['Dig. RA'] + "'", 'nome':'"' + item['Nome do Aluno'] + '"', 'nascimento':nascimento, 'matricula':inicio_mat, 'num_chamada':item['Nº'], 'serie':item['Série'], 'situacao':getSituacao(item['Situação']), 'fim_mat':fim_mat, 'num_classe':turma['num_classe']}
            dados_extras = banco.executarConsulta("select ifnull(rg, '') as rg, ifnull(cpf, 'null') as cpf, sexo, ifnull(rm, 'null') as rm from aluno where ra = %s" % aluno['ra'])
            
            if len(dados_extras) > 0:
                aluno['rg'] = "'" + dados_extras[0]['rg'] + "'"
                aluno['cpf'] = dados_extras[0]['cpf']
                aluno['sexo'] = "'" + dados_extras[0]['sexo'] + "'"
                aluno['rm'] = dados_extras[0]['rm']
            else:
                aluno['rg'] = 'null'
                aluno['cpf'] = 'null'
                aluno['sexo'] = '-'
                aluno['rm'] = 'null'

            lista.append(aluno)
                
        
        if (banco.importarDadosTurma(lista)):
            socketio.emit('update_info', '<b>Dados da %s - %s <span class="text-success">atualizados com sucesso!</span></b>' % (turma['nome_turma'], turma['desc_duracao']))
        else:
            socketio.emit('update_info', '<b class="text-danger">Falha ao tentar atualizar dados da %s - %s!</b>' % (turma['nome_turma'], turma['desc_duracao']))


    # repetir o mesmo processo, porém para if
    turmas = banco.executarConsulta('select num_classe, nome_turma, duracao.descricao as desc_duracao from turma_if inner join duracao on duracao.id = turma_if.duracao where ano = %s order by duracao, tipo_ensino, nome_turma' % ano)    

    for turma in turmas:  
        
        await page.goto('https://sed.educacao.sp.gov.br//NCA/RelacaoAlunosClasse/Index', {'waitUntil':'networkidle0'})

        await page.type('#numeroClassePesq', str(turma['num_classe']))

        await page.evaluate('''() => {
            pesquisar();
        }''')    

        socketio.emit('update_info', '<b>Atualizando dados da %s - %s (%s)</b>' % (turma['nome_turma'], turma['desc_duracao'], ano))

        await page.waitForSelector("#tabelaDadosClasse")

        code = await page.evaluate('$("#tabelaDadosClasse").find("tbody").find("a").attr("onclick");')

        await page.evaluate(code + ';')

        await page.waitForSelector("#tabelaAlunosClasse")

        tabela = await page.evaluate('''() => {
            let table = $("#tabelaAlunosClasse").DataTable();

            table.order( [1,'asc'] ).draw();

            var columnNames = table.columns().header().toArray().map(header => $(header).text());

            var dataDictList = table.rows().data().toArray().map(row => {
                let rowData = {};
                columnNames.forEach((colName, index) => {
                    rowData[colName] = row[index];
                });
                return rowData;
            });    

            return Promise.resolve(dataDictList);
        }''')

        lista = []

        for item in tabela:

            nascimento = "'" + converterDataMySQL(item['Data de Nascimento']) + "'"
            inicio_mat = "'" + converterDataMySQL(item['Data Início Matrícula']) + "'"
            fim_mat = "'" + converterDataMySQL(item['Data Fim Matrícula']) + "'"


            aluno = {'ra':int(item['RA']), 'digito':"'" + item['Dig. RA'] + "'", 'nome':"'" + item['Nome do Aluno'] + "'", 'nascimento':nascimento, 'matricula':inicio_mat, 'num_chamada':item['Nº'], 'serie':"0", 'situacao':getSituacao(item['Situação']), 'fim_mat':fim_mat, 'num_classe':turma['num_classe']}
            dados_extras = banco.executarConsulta("select ifnull(rg, '') as rg, ifnull(cpf, 'null') as cpf, sexo, ifnull(rm, 'null') as rm from aluno where ra = %s" % aluno['ra'])
            
            if len(dados_extras) > 0:
                aluno['rg'] = "'" + dados_extras[0]['rg'] + "'"
                aluno['cpf'] = dados_extras[0]['cpf']
                aluno['sexo'] = "'" + dados_extras[0]['sexo'] + "'"
                aluno['rm'] = dados_extras[0]['rm']
            else:
                aluno['rg'] = 'null'
                aluno['cpf'] = 'null'
                aluno['sexo'] = '-'
                aluno['rm'] = 'null'

            lista.append(aluno)
                
        
        if (banco.importarDadosTurma(lista)):
            socketio.emit('update_info', '<b>Dados da %s - %s <span class="text-success">atualizados com sucesso!</span></b>' % (turma['nome_turma'], turma['desc_duracao']))
        else:
            socketio.emit('update_info', '<b class="text-danger">Falha ao tentar atualizar dados da %s - %s!</b>' % (turma['nome_turma'], turma['desc_duracao']))

    await page.screenshot({'path': 'static/images/etapas_navegacao/ETAPA 1.png'})

    await browser.close()

    return jsonify(True)


@app.route('/gerar_pdf', methods=['GET', 'POST'])
async def gerar_pdf():
    info = request.json
    global aux_info

    if info['destino'] == 1:
        pdf_path = 'static/docs/lista.pdf'

        browser = await launch(
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False
        )

        page = await browser.newPage()
        await page.goto('http://localhost/render_lista?tipo=%s&num_classe=%s&order=%s' % (info['tipo'], info['turma'], info['order']), {'waitUntil':'networkidle2'})
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
        await page.goto('http://localhost/render_lista?tipo=%s&num_classe=%s&order=0' % (info['tipo'], info['turma']), {'waitUntil':'networkidle2'})
        await page.pdf({'path': pdf_path, 'format':'A4', 'scale':1, 'printBackground':True})
        await browser.close()

        return jsonify(pdf_path)  

    elif info['destino'] == 3:

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
        await page.goto('http://localhost/render_lista?tipo=declaracao&num_classe=white&order=0')
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
        await page.goto('http://localhost/render_conselho_bimestre?bimestre=%s&num_classe=%s&order=0' % (info['bimestre'], info['num_classe']), {'waitUntil':'networkidle2'})
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
        await page.goto('http://localhost/render_conselho_bimestre_all?bimestre=%s&ano=%s&order=0' % (info['bimestre'], info['ano']), {'waitUntil':'networkidle2'})
        await page.pdf({'path': pdf_path, 'format':'A4', 'scale':1, 'printBackground':True})
        await browser.close()

        return jsonify(pdf_path)
    
    elif info['destino'] == 7: # livro ponto completo
        pdf_path = 'static/docs/livro_ponto.pdf'

        browser = await launch(
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False
        )

        page = await browser.newPage()
        await page.goto('http://localhost/render_livro_ponto?mes=%s&ano=%s&order=0' % (info['mes'], info['ano']), {'waitUntil':'networkidle2'})
        await page.pdf({'path': pdf_path, 'format':'A4', 'scale':1, 'printBackground':True})
        await browser.close()

        return jsonify(pdf_path)
    
    elif info['destino'] == 8: # certificados
        pdf_path = 'static/docs/certificados.pdf'

        browser = await launch(
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False
        )

        page = await browser.newPage()
        await page.goto('http://localhost/render_certificados_conclusao?classe=%s&order=0' % info['classe'], {'waitUntil':'networkidle2'})
        await page.pdf({'path': pdf_path, 'format':'A4', 'landscape':True, 'scale':1, 'printBackground':True})
        await browser.close()

        return jsonify(pdf_path)
    
    elif info['destino'] == 9: # livro ponto individual
        pdf_path = 'static/docs/certificados.pdf'

        browser = await launch(
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False
        )

        page = await browser.newPage()
        await page.goto('http://localhost/render_livro_ponto?mes=%s&ano=%s&professor=%s&number=%s&di=%s&order=0' % (info['mes'], info['ano'], info['professor'], info['number'], info['di']), {'waitUntil':'networkidle2'})
        await page.pdf({'path': pdf_path, 'format':'A4', 'scale':1, 'printBackground':True})
        await browser.close()

        return jsonify(pdf_path)
    
    elif info['destino'] == 10: # ficha de matrícula
        pdf_path = 'static/docs/ficha.pdf'

        try:
            browser = await launch(
                handleSIGINT=False,
                handleSIGTERM=False,
                handleSIGHUP=False
            )

            page = await browser.newPage()

            # efetuar login na SED
            await page.goto('https://sed.educacao.sp.gov.br/')
            await page.waitForSelector('#name', {'visible': True}) 
            await page.evaluate('''(selector, value) => { document.querySelector(selector).value = value; }''', '#name', 'rg490877795sp')    
            await page.evaluate('''(selector, value) => {
                document.querySelector(selector).value = value;
            }''', '#senha', 'BGarden@FF8')  
            await page.evaluate("() => document.querySelector('#botaoEntrar').removeAttribute('disabled')")
            await page.click("#botaoEntrar")
            await page.waitForSelector('#ambientes-aprendizagem', {'visible': True})

            # abrir a ficha do aluno e pegar informações
            await page.goto("https://sed.educacao.sp.gov.br/NCA/FichaAluno/Index", {'timeout':60000, 'waitUntil':'domcontentloaded'})
            await page.evaluate('''() => {
                const element = document.querySelector('.blockOverlay');
                if (element) {
                    element.remove();
                }
            }''')
            await page.evaluate('''() => {
                const element = document.querySelector('.blockPage');
                if (element) {
                    element.remove();
                }
            }''')
            await page.waitForSelector('#btnPesquisar', {'visible': True})
            await page.evaluate("() => document.querySelector('#fieldSetRA').removeAttribute('style')")
            await page.evaluate('''(selector, value) => { document.querySelector(selector).value = value; }''', '#txtRa', info['ra']) 
            await page.waitForSelector('.blockUI', {'hidden':True})
            await page.evaluate('''(selector, value) => { document.querySelector(selector).value = value; }''', '#TipoConsultaFichaAluno', 1) 
            await page.click("#btnPesquisar")
            await page.waitForSelector('#tabelaDados', {'visible': True})
            script = await page.evaluate("document.getElementsByClassName('colVisualizar')[1].getElementsByTagName('a')[0].getAttribute('onclick')")
            await page.evaluate(script)
            await page.waitForSelector('#sedUiModalWrapper_1', {'visible': True})

            # pegar dados do aluno para inserir na planilha
            dados = await page.evaluate("document.getElementById('sedUiModalWrapper_1title').textContent")
            lista = dados.split('-')

            nome = await page.evaluate("document.getElementById('NomeAluno').value")
            nome_social = await page.evaluate("document.getElementById('NomeSocial').value")
            ra = lista[1][7:10] + '.' + lista[1][10:13] + '.' + lista[1][13:16] + '-' + lista[2][0:1]
            data_nascimento = lista[3][18:]
            cidade_nascimento = await page.evaluate("document.getElementById('CidadeNascimento').value")
            uf_nascimento = await page.evaluate("document.getElementById('UFNascimento').value")
            rg = await page.evaluate("document.getElementById('RgAluno').value") + '-' + await page.evaluate("document.getElementById('DigRgAluno').value")
            uf_rg = await page.evaluate("document.getElementById('sgUfRg').value")
            print(uf_rg)
            if rg != '':
                if uf_rg == 'RJ':
                    rg = rg[0:2] + '.' + rg[2:5] + '.' + rg[5:] + '/' + uf_rg
                else:
                    rg = rg[6:8] + '.' + rg[8:11] + '.' + rg[11:]
            else:
                rg = '-'
            cpf = await page.evaluate("document.getElementById('CpfAluno').value")
            if cpf == '':
                cpf = '-'
            print(cpf)
            sexo = await page.evaluate("document.getElementById('Sexo').value")
            sexo = sexo[0:1]
            pai = await page.evaluate("document.getElementById('NomePai').value")
            mae = await page.evaluate("document.getElementById('NomeMae').value")

            if int(info['tipo_endereco']) == 1:
                endereco = info['endereco_manual']
            else:
                endereco = await page.evaluate("document.getElementById('Endereco').value")
                endereco = endereco.title().replace('Da ', 'da ').replace("De ", "de ").replace("Do ", 'do ').replace("Dos ", 'dos ') 
                num_casa = await page.evaluate("document.getElementById('EnderecoNR').value")
                endereco += ', %s' % num_casa
                comp = await page.evaluate("document.getElementById('EnderecoComplemento').value")
                if comp != '':
                    endereco += ', %s' % comp.title().replace('Da ', 'da ').replace("De ", "de ").replace("Do ", 'do ').replace("Dos ", 'dos ') 
                bairro = await page.evaluate("document.getElementById('EnderecoBairro').value")
                endereco += ', %s' % bairro.title().replace('Da ', 'da ').replace("De ", "de ").replace("Do ", 'do ').replace("Dos ", 'dos ') 
                cidade_endereco = await page.evaluate("document.getElementById('EnderecoCidade').value")
                endereco += ', %s' % cidade_endereco.title().replace('Da ', 'da ').replace("De ", "de ").replace("Do ", 'do ').replace("Dos ", 'dos ') 
                estado_endereco = await page.evaluate("document.getElementById('EnderecoUF').value")
                endereco += '/%s' % estado_endereco


            # montar url para inserir os dados no render
            url = 'http://localhost/render_lista?tipo=ficha_mat&num_classe=0&order=0'
            url += '&rm=%s&ra=%s&rg=%s&cpf=%s&sexo=%s' % (info['rm'], ra, rg, cpf, sexo)
            url += '&nome=%s&nome_social=%s&pai=%s&mae=%s&cidade=%s&estado=%s&nascimento=%s&endereco=%s&telefone=%s&email=%s' % (nome.replace(' ', '+'), nome_social.replace(' ', '+'), pai.replace(' ', '+'), mae.replace(' ', '+'), cidade_nascimento.replace(' ', '+'), uf_nascimento, data_nascimento, endereco, info['telefone'], info['email'])
            url += '&serie_desc=%s&serie_simples=%s&fund=%s&medio=%s&ano=%s' % (info['serie_desc'], info['serie_simples'], info['fund'], info['medio'], info['ano'])

            print(url)

            #page = await browser.newPage()
            await page.goto(url, {'waitUntil':'networkidle2'})
            await page.pdf({'path': pdf_path, 'format':'A4', 'scale':1, 'printBackground':True})
            await browser.close()

            return jsonify({'status':True,'path':pdf_path})
        
        except Exception as error:
            print("An exception occurred:", error)
            return jsonify({'status':False, 'error':"An exception occurred: %s" % error, 'msg':'RA localizado!'})


    elif info['destino'] == 11: # declaração com frequência

        pdf_path = 'static/docs/declaracao_freq.pdf'
        
        aluno = banco.executarConsulta('select nome, rg, sexo from aluno where ra = %s' % info['ra'].replace('.', '')[:9])[0]
        
        info_classe = banco.executarConsulta('select turma.num_classe, serie, tipo_ensino, tipo_ensino.descricao as tipo_ensino_desc from turma inner join vinculo_alunos_turmas on vinculo_alunos_turmas.num_classe = turma.num_classe inner join tipo_ensino on tipo_ensino.id = turma.tipo_ensino where ra_aluno = %s and situacao = 1' % info['ra'].replace('.', '')[:9])[0]

        sql = 'SELECT '
        sql += '(select sum(falta) - sum(ac) from notas inner join vinculo_alunos_turmas on vinculo_alunos_turmas.ra_aluno = notas.ra_aluno and vinculo_alunos_turmas.situacao = 1 left join vinculo_alunos_if on vinculo_alunos_if.ra_aluno = notas.ra_aluno and vinculo_alunos_if.situacao = 1 where notas.ra_aluno = %s and (notas.num_classe = vinculo_alunos_turmas.num_classe or notas.num_classe = vinculo_alunos_if.num_classe_if)) as faltas,' % info['ra'].replace('.', '')[:9]
        sql += '(select sum(aulas_dadas) from vinculo_prof_disc inner join vinculo_alunos_turmas on vinculo_alunos_turmas.situacao = 1 and vinculo_alunos_turmas.ra_aluno = %s left join vinculo_alunos_if on vinculo_alunos_if.situacao = 1 and vinculo_alunos_if.ra_aluno = %s where vinculo_prof_disc.num_classe = vinculo_alunos_turmas.num_classe or vinculo_prof_disc.num_classe = vinculo_alunos_if.num_classe_if) as aulas_dadas,' % (info['ra'].replace('.', '')[:9], info['ra'].replace('.', '')[:9])
        sql += '(select max(bimestre) from notas inner join turma on turma.num_classe = notas.num_classe where ra_aluno = %s and turma.ano = YEAR(CURDATE())) as bimestre' % info['ra'].replace('.', '')[:9]

        freq = banco.executarConsulta(sql)

        if (freq[0]['faltas']):
            freq_percent = round((freq[0]['aulas_dadas'] - freq[0]['faltas']) / freq[0]['aulas_dadas'] * 100, 2)
            bimestre = freq[0]['bimestre']
        else:
            freq_percent = -1
            bimestre = 0

        aux_info = {'nome':aluno['nome'], 'rg':aluno['rg'], 'genero':aluno['sexo'].lower(), 'tipo':4, 'info_classe':info_classe, 'percent':freq_percent, 'bimestre':bimestre, 'anos':None}

        browser = await launch(
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False
        )

        page = await browser.newPage()
        await page.goto('http://localhost/render_lista?tipo=declaracao&num_classe=white&order=0', {'waitUntil':'networkidle2'})
        await page.pdf({'path': pdf_path, 'format':'A4', 'scale':1, 'printBackground':True})
        await browser.close()

        return jsonify(pdf_path)


    elif info['destino'] == 12: # boletins

        pdf_path = 'static/docs/boletins.pdf'
            
        browser = await launch(
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False
        )

        page = await browser.newPage()
        await page.goto('http://localhost/render_boletim?num_classe=%s&ano=%s&order=0' % (info['num_classe'], info['ano']), {'waitUntil':'networkidle2'})
        await page.pdf({'path': pdf_path, 'format':'A4', 'scale':1, 'printBackground':True})
        await browser.close()

        return jsonify(pdf_path)

    elif info['destino'] == 13: # declaração completa

        pdf_path = 'static/docs/declaracao_freq.pdf'
        
        aluno = banco.executarConsulta('select nome, rg, sexo from aluno where ra = %s' % info['ra'].replace('.', '')[:9])[0]
        
        info_classe = banco.executarConsulta('select turma.num_classe, serie, tipo_ensino, tipo_ensino.descricao as tipo_ensino_desc from turma inner join vinculo_alunos_turmas on vinculo_alunos_turmas.num_classe = turma.num_classe inner join tipo_ensino on tipo_ensino.id = turma.tipo_ensino where ra_aluno = %s and situacao = 1' % info['ra'].replace('.', '')[:9])[0]

        sql = 'SELECT '
        sql += '(select sum(falta) - sum(ac) from notas inner join vinculo_alunos_turmas on vinculo_alunos_turmas.ra_aluno = notas.ra_aluno and vinculo_alunos_turmas.situacao = 1 left join vinculo_alunos_if on vinculo_alunos_if.ra_aluno = notas.ra_aluno and vinculo_alunos_if.situacao = 1 where notas.ra_aluno = %s and (notas.num_classe = vinculo_alunos_turmas.num_classe or notas.num_classe = vinculo_alunos_if.num_classe_if)) as faltas,' % info['ra'].replace('.', '')[:9]
        sql += '(select sum(aulas_dadas) from vinculo_prof_disc inner join vinculo_alunos_turmas on vinculo_alunos_turmas.situacao = 1 and vinculo_alunos_turmas.ra_aluno = %s left join vinculo_alunos_if on vinculo_alunos_if.situacao = 1 and vinculo_alunos_if.ra_aluno = %s where vinculo_prof_disc.num_classe = vinculo_alunos_turmas.num_classe or vinculo_prof_disc.num_classe = vinculo_alunos_if.num_classe_if) as aulas_dadas,' % (info['ra'].replace('.', '')[:9], info['ra'].replace('.', '')[:9])
        sql += '(select max(bimestre) from notas inner join turma on turma.num_classe = notas.num_classe where ra_aluno = %s and turma.ano = YEAR(CURDATE())) as bimestre' % info['ra'].replace('.', '')[:9]

        freq = banco.executarConsulta(sql)

        if (freq[0]['faltas']):
            freq_percent = round((freq[0]['aulas_dadas'] - freq[0]['faltas']) / freq[0]['aulas_dadas'] * 100, 2)
            bimestre = freq[0]['bimestre']
        else:
            freq_percent = -1
            bimestre = 0

        aux_info = {'nome':aluno['nome'], 'rg':aluno['rg'], 'genero':aluno['sexo'].lower(), 'tipo':4, 'info_classe':info_classe, 'percent':freq_percent, 'bimestre':bimestre, 'anos':info['anos']}

        browser = await launch(
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False
        )

        page = await browser.newPage()
        await page.goto('http://localhost/render_lista?tipo=declaracao&num_classe=white&order=0', {'waitUntil':'networkidle2'})
        await page.pdf({'path': pdf_path, 'format':'A4', 'scale':1, 'printBackground':True})
        await browser.close()

        return jsonify(pdf_path)
    
    elif info['destino'] == 14: #livro ponto ADM

        pdf_path = 'static/docs/ponto.pdf'
        cpf = info['cpf']
        ano = info['ano']
        mes = info['mes']

        browser = await launch(
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False
        )

        page = await browser.newPage()
        await page.goto('http://localhost/render_livro_ponto_adm?cpf=%s&mes=%s&ano=%s&order=0' % (cpf, mes, ano), {'waitUntil':'networkidle2'})
        await page.pdf({'path': pdf_path, 'format':'A4', 'scale':1, 'printBackground':True})
        await browser.close()

        return jsonify(pdf_path)





@app.route('/teste', methods=['GET', 'POST'])
def teste():

    return render_template('teste.jinja')
        


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

@app.route('/ficha_matricula', methods=['GET', 'POST'])
def ficha_matricula():

    return render_template('ficha_de_matricula.jinja')



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

            total_habilitados_certificado = banco.executarConsultaVetor('select count(*) as total from vinculo_alunos_turmas where num_classe = %s and situacao in (6, 1) and serie in (3, 4, 12)' % num_classe)[0]
            
            if (total_habilitados_certificado > 0):
                certificado = True
            else:
                certificado = False
            
            sql =   r"select CASE WHEN turma.duracao < 3 THEN DATE_FORMAT(1bim_inicio,'%d/%m/%Y') ELSE DATE_FORMAT(3bim_inicio,'%d/%m/%Y') END as inicio, " + \
	                r"CASE WHEN turma.duracao = 1 OR turma.duracao = 3 THEN DATE_FORMAT(4bim_fim,'%d/%m/%Y') ELSE DATE_FORMAT(2bim_fim,'%d/%m/%Y') END as fim " + \
                    "from calendario INNER JOIN turma ON turma.ano = calendario.ano WHERE turma.num_classe = %s" % (num_classe)
            
            duracao = banco.executarConsulta(sql)

            sql = "select count(*) as total, sum(case when situacao = 1 then 1 else 0 end) as ativos from vinculo_alunos_turmas where num_classe = %s" % (num_classe)

            total = banco.executarConsulta(sql)[0]

            return jsonify({'duracao':duracao, 'turma':turma, 'total':total, 'certificado':certificado})
            

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
async def pesquisarRGCPF():
    if request.method == "POST":
        if request.is_json:
            lista = request.json
            new_list = []
            
            browser = await launch(
                {'headless': False},
                handleSIGINT=False,
                handleSIGTERM=False,
                handleSIGHUP=False
            )

            page = await browser.newPage()
            # Navigate the page to a URL
            await page.goto('https://sed.educacao.sp.gov.br/')

            # Set screen size
            await page.setViewport({'width':1366, 'height':768})

            await page.waitForSelector("#name")

            # Type into login
            await page.type('#name', 'rg490877795sp')
            await page.type('#senha', 'BGarden@FF8')


            await page.click("#botaoEntrar")

            await page.waitForSelector("#decorMenuFilterTxt")

            for item in lista:
                await page.goto("https://sed.educacao.sp.gov.br/NCA/FichaAluno/Index", {'timeout':60000, 'waitUntil':'domcontentloaded'})

                await page.waitForSelector('.blockUI', {'hidden':True})
                await page.evaluate('''$("#fieldSetRA").removeAttr("style")''')
                await page.evaluate('''(selector, value) => { document.querySelector(selector).value = value; }''', '#txtRa', item)
                await page.evaluate('''$("#TipoConsultaFichaAluno").val(1)''') 
                await page.evaluate('CarregarPesquisaFichaAluno()')

                await page.waitForSelector('#tabelaDados')

                script_txt = await page.evaluate('''$(".colVisualizar a").attr('onclick')''')
                await page.evaluate(script_txt)

                await page.waitForSelector("#dtAlteracaoAluno")

                sexo = await page.evaluate('$("#Sexo").val()')
                sexo = sexo[0:1]
                cpf = await page.evaluate('$("#CpfAluno").val()')
                cpf = cpf.replace('.', '').replace('-', '')
                estado = await page.evaluate('$("#sgUfRg").val()')

                if estado == 'SP':
                    rg = await page.evaluate("document.getElementById('RgAluno').value") + '-' + await page.evaluate("document.getElementById('DigRgAluno').value")
                    rg = rg[6:8] + '.' + rg[8:11] + '.' + rg[11:]
                else:
                    rg = await page.evaluate("document.getElementById('RgAluno').value") + '-' + await page.evaluate("document.getElementById('DigRgAluno').value") + '/' + estado

                new_list.append({'cpf':cpf, 'rg':rg, 'sexo':sexo})

            await browser.close()

            return jsonify(new_list)

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

                        if situacao == "ATIVO":
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
                        elif situacao == "RETIDO FREQ." or situacao == 'RETIDO REND.':
                            sit = 10
                        elif situacao == 'RECL':
                            sit = 15
                        elif situacao == 'ENCERRADA':
                            sit = 16


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

    anos = banco.executarConsulta('select ano from turma group by ano order by ano desc')

    ano_base = anos[0]['ano']

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

        if 'cb_ano' in request.form:
            ano_base = request.form.get('cb_ano')
        
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
                
        elif bool(request.files.get('mapao', False)) == True:

            isthisFile = request.files.get('mapao')
            file_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'mapao.xls')
            isthisFile.save(file_dir)

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

            if request.form.getlist('duracao')[0] == '1º Semestre':
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

                        professor = item['professor'] = banco.executarConsulta('select professor.nome_ata as nome from vinculo_prof_disc inner join professor ON professor.rg = vinculo_prof_disc.rg_prof where num_classe = %s and bimestre = %s and disciplina = %s' % (request.form.getlist('num_classe')[0], bimestre_final, item['disc']))

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


            professores = banco.executarConsulta('select rg, nome_ata from vinculo_turma_prof INNER JOIN professor ON professor.rg = vinculo_turma_prof.rg_prof where id_turma = %s order by nome_ata' % request.form.getlist('num_classe')[0])
            #print(lista)

            #verificar se já existe professores vinculados a disciplina e se existir criar uma lista
            professores_atuais = banco.executarConsulta('select rg_prof, disciplina from vinculo_prof_disc where bimestre = %s and num_classe = %s' % (request.form.getlist('bimestre')[0], request.form.getlist('num_classe')[0]))
            dict_aux = {}
            for item in professores_atuais:
                dict_aux[item['disciplina']] = item['rg_prof']

            return jsonify({'lista':lista, 'professores':professores, 'professores_atuais':dict_aux})

        

    disciplinas = banco.executarConsulta('select codigo_disciplina, disciplinas.descricao, disciplinas.abv, classificacao, classificacao.abv as classificacao_desc from disciplinas INNER JOIN classificacao ON classificacao.id = disciplinas.classificacao order by descricao')
    classificacao = banco.executarConsulta('select * from classificacao')
    professores = banco.executarConsulta('select * from professor order by nome_ata')
    dificuldades = banco.executarConsulta('select id, descricao as title from dificuldades')


    listaTipos = banco.executarConsulta('select tipo_ensino.id, tipo_ensino.descricao as tipo_ensino, if (count(turma.tipo_ensino) > 0, count(turma.tipo_ensino), count(turma_if.tipo_ensino)) as total from tipo_ensino LEFT JOIN turma ON turma.tipo_ensino = tipo_ensino.id LEFT JOIN turma_if ON turma_if.tipo_ensino = tipo_ensino.id GROUP BY id order by id')

    listaTurmas = []

    for item in listaTipos:
        
        if item['total'] > 0:

            if item['id'] != 2 and item['id'] != 5:
                turmas = banco.executarConsulta('select num_classe, nome_turma, duracao.descricao as duracao, turma.duracao as id_duracao, turma.tipo_ensino as id_ensino, periodo.descricao as periodo, turma.periodo as id_periodo from turma INNER JOIN duracao ON duracao.id = turma.duracao INNER JOIN periodo ON periodo.id = turma.periodo where tipo_ensino = %s and ano = %s order by duracao, nome_turma' % (item['id'], ano_base))
            else:
                turmas = banco.executarConsulta('select num_classe, nome_turma, duracao.descricao as duracao, turma_if.duracao as id_duracao, turma_if.tipo_ensino as id_ensino, periodo.descricao as periodo, turma_if.periodo as id_periodo, turma_if.categoria as categoria from turma_if INNER JOIN duracao ON duracao.id = turma_if.duracao INNER JOIN periodo ON periodo.id = turma_if.periodo where tipo_ensino = %s and ano = %s order by duracao, nome_turma' % (item['id'], ano_base))

            listaTurmas.append({'tipo_ensino':item, 'lista':turmas})


    bimestres = banco.executarConsulta('select * from calendario where ano = %s' % ano_base)
    #bimestres = banco.executarConsulta('select * from calendario where ano = 2023')
    bim = {'1bim':{'inicio':bimestres[0]['1bim_inicio'], 'fim':bimestres[0]['1bim_fim']}}
    bim['2bim'] = {'inicio':bimestres[0]['2bim_inicio'], 'fim':bimestres[0]['2bim_fim']}
    bim['3bim'] = {'inicio':bimestres[0]['3bim_inicio'], 'fim':bimestres[0]['3bim_fim']}
    bim['4bim'] = {'inicio':bimestres[0]['4bim_inicio'], 'fim':bimestres[0]['4bim_fim']}

    return render_template('notas.jinja', bimestres=json.dumps(bim, indent=4, sort_keys=True, default=str), classificacao=classificacao, msg=msg, disciplinas=disciplinas, listaTurmas=listaTurmas, professores=professores, dificuldades=json.dumps(dificuldades), anos=anos, ano_base=ano_base)

@app.route('/frequencia', methods=['GET', 'POST'])
def frequencia():

    msg = ''

    if request.method == 'POST':
        if request.is_json:
            info = request.json

            if info['action'] == 1: # pegar lista de alunos
                
                sql = "select vinculo_alunos_turmas.ra_aluno, aluno.nome, " + \
                      'if(frequencia.freq = 0, "", "checked") as check_form, ' + \
                      'if(frequencia.freq = 0, "text-danger", "") as text_form ' + \
                      "from vinculo_alunos_turmas " + \
                      "inner join aluno on aluno.ra = vinculo_alunos_turmas.ra_aluno " + \
                      "left join frequencia on frequencia.ra_aluno = vinculo_alunos_turmas.ra_aluno and frequencia.`date` = '%s' " % info['dia'] + \
                      "where num_classe = %s and ('%s' BETWEEN matricula and fim_mat) order by nome" % (info['num_classe'], info['dia'])
                
                alunos = banco.executarConsulta(sql)

                sql = "select count(frequencia.freq) as total " + \
                      "from vinculo_alunos_turmas " + \
                      "inner join aluno on aluno.ra = vinculo_alunos_turmas.ra_aluno " + \
                      "left join frequencia on frequencia.ra_aluno = vinculo_alunos_turmas.ra_aluno and frequencia.`date` = '%s' " % info['dia'] + \
                      "where num_classe = %s and ('%s' BETWEEN matricula and fim_mat) order by nome" % (info['num_classe'], info['dia'])
                
                total = banco.executarConsultaVetor(sql)[0]


                return jsonify({'lista':alunos, 'total':total})
            
            elif info['action'] == 2: # salvar lista

                lista = info['lista']

                resultado = True

                for item in lista:
                    if not banco.insertOrUpdate(item, 'frequencia'):
                        resultado = False

                return jsonify(resultado)
            
            elif info['action'] == 3:

                texto_final = '*Faltas do dia %s/%s/%s*' % (info['data'][8:10], info['data'][5:7], info['data'][0:4])
                texto_final += '<br><br>'

                turmas = banco.executarConsulta('select num_classe, nome_turma from turma where ano = %s order by tipo_ensino, nome_turma' % info['data'][:4])

                for turma in turmas:
                    texto_final += "*" + turma['nome_turma'].replace(' série ', '') + ':*<br>'

                    alunos = banco.executarConsulta("SELECT	vinculo_alunos_turmas.ra_aluno, aluno.nome FROM vinculo_alunos_turmas INNER JOIN frequencia ON frequencia.ra_aluno = vinculo_alunos_turmas.ra_aluno and frequencia.date = '%s'INNER JOIN aluno ON aluno.ra = vinculo_alunos_turmas.ra_aluno WHERE num_classe = %s and vinculo_alunos_turmas.situacao = 1 and freq = 0 ORDER BY nome" % (info['data'], turma['num_classe']))

                    if len(alunos) < 1:
                        texto_final += ' - Sem Faltas Registradas<br>'

                    for aluno in alunos:
                        texto_final += '- %s<br>' % aluno['nome'].title().replace('Da ', 'da ').replace("De ", "de ").replace("Do ", 'do ').replace("Dos ", 'dos ') 

                    texto_final += '<br>'


                #print(texto_final.replace('<br>', '\n'))
                return jsonify(texto_final)

    listaTipos = banco.executarConsulta('select tipo_ensino.id, tipo_ensino.descricao as tipo_ensino, if (count(turma.tipo_ensino) > 0, count(turma.tipo_ensino), count(turma_if.tipo_ensino)) as total from tipo_ensino LEFT JOIN turma ON turma.tipo_ensino = tipo_ensino.id LEFT JOIN turma_if ON turma_if.tipo_ensino = tipo_ensino.id WHERE id != 2 and id != 5 GROUP BY id order by id')

    listaTurmas = []
    hoje = datetime.now()

    for item in listaTipos:
        
        if item['total'] > 0:

            if item['id'] != 2 and item['id'] != 5:
                turmas = banco.executarConsulta('select num_classe, nome_turma, duracao.descricao as duracao, turma.duracao as id_duracao, turma.tipo_ensino as id_ensino, periodo.descricao as periodo, turma.periodo as id_periodo from turma INNER JOIN duracao ON duracao.id = turma.duracao INNER JOIN periodo ON periodo.id = turma.periodo where tipo_ensino = %s and ano = year(now()) order by duracao, nome_turma' % item['id'])
            else:
                turmas = banco.executarConsulta('select num_classe, nome_turma, duracao.descricao as duracao, turma_if.duracao as id_duracao, turma_if.tipo_ensino as id_ensino, periodo.descricao as periodo, turma_if.periodo as id_periodo, turma_if.categoria as categoria from turma_if INNER JOIN duracao ON duracao.id = turma_if.duracao INNER JOIN periodo ON periodo.id = turma_if.periodo where tipo_ensino = %s and ano = year(now()) order by duracao, nome_turma' % item['id'])

            listaTurmas.append({'tipo_ensino':item, 'lista':turmas})

    return render_template('frequencia.jinja', listaTurmas=listaTurmas, data=hoje.strftime('%Y-%m-%d'), msg=msg)


@app.route('/render_boletim', methods=['GET', 'POST'])
def boletim():

    num_classe = request.args.getlist('num_classe')[0]
    ano = request.args.getlist('ano')[0]

    duracao = banco.executarConsultaVetor('select duracao from turma where num_classe = %s' % num_classe)[0]

    if duracao == 1:
        desc_duracao = ''
    elif duracao == 2:
        desc_duracao = ' - <span class="red">1º Semestre</span>'
    else:
        desc_duracao = ' - <span class="red">2º Semestre</span>'

    # pegar todos os alunos ativos dessa turma
    alunos = banco.executarConsulta('select ra_aluno, nome, situacao.descricao as situacao from vinculo_alunos_turmas inner join aluno on aluno.ra = vinculo_alunos_turmas.ra_aluno inner join situacao on vinculo_alunos_turmas.situacao = situacao.id where num_classe = %s and situacao in (1, 6, 7, 8, 10) order by nome' % num_classe)

    # pegar as disciplinas das turmas
    disciplinas = banco.executarConsulta('select disciplinas.descricao as disc, notas.disciplina, disciplinas.classificacao from notas inner join disciplinas on disciplinas.codigo_disciplina = notas.disciplina where num_classe = %s group by disciplina order by classificacao, disciplina' % num_classe)

    # pegar a informação da classe
    info_classe = banco.executarConsulta('select nome_turma, tipo_ensino.descricao as tipo_ensino from turma inner join tipo_ensino on tipo_ensino.id = turma.tipo_ensino where num_classe = %s' % num_classe)[0]

    # correr a lista dos alunos e buscar a nota
    for aluno in alunos:
        notas_aluno = banco.executarConsulta('select bimestre, nota, falta, ac, disciplinas.descricao as disc, disciplinas.codigo_disciplina from notas inner join disciplinas on disciplinas.codigo_disciplina = notas.disciplina inner join turma on turma.ano = %s and turma.duracao = %s and turma.num_classe = notas.num_classe where ra_aluno = %s order by disc, bimestre' % (ano, duracao, aluno['ra_aluno']))
        notas_aluno_if = banco.executarConsulta('select bimestre, nota, falta, ac, disciplinas.descricao as disc, disciplinas.codigo_disciplina from notas inner join disciplinas on disciplinas.codigo_disciplina = notas.disciplina inner join turma_if on turma_if.ano = %s and turma_if.duracao = %s and turma_if.num_classe = notas.num_classe where ra_aluno = %s order by disc, bimestre' % (ano, duracao, aluno['ra_aluno']))

        desc_if = banco.executarConsulta('select descricao from categoria_itinerario inner join turma_if on turma_if.categoria = categoria_itinerario.id where turma_if.duracao = %s and turma_if.num_classe in (select num_classe_if from vinculo_alunos_if where ra_aluno = %s and year(matricula) = %s)' % (duracao, aluno['ra_aluno'], ano))
        
        if len(desc_if) > 0:
            aluno['nome_if'] = desc_if[0]['descricao']
        else:
            aluno['nome_if'] = None

        notas = {}
        aux = {}

        if len(notas_aluno) > 0:
            disc = notas_aluno[0]['codigo_disciplina']

            for item in notas_aluno:
                if item['codigo_disciplina'] == disc:
                    aux[item['bimestre']] = {'n':item['nota'], 'f':item['falta'], 'ac':item['ac']}
                else:
                    notas[disc] = aux
                    aux = {}
                    disc = item['codigo_disciplina']

                    aux[item['bimestre']] = {'n':item['nota'], 'f':item['falta'], 'ac':item['ac']}

            notas[disc] = aux
            
            aluno['notas'] = notas

        notas = []
        aux = {}

        if len(notas_aluno_if) > 0:

            disc = notas_aluno_if[0]['codigo_disciplina']

            for item in notas_aluno_if:
                if item['codigo_disciplina'] == disc:
                    aux[item['bimestre']] = {'n':item['nota'], 'f':item['falta'], 'ac':item['ac']}

                    aux['desc'] = item['disc']
                    aux['cod'] = item['codigo_disciplina']

                else:
                    notas.append(aux)
            
                    aux = {}
                    disc = item['codigo_disciplina']

                    aux[item['bimestre']] = {'n':item['nota'], 'f':item['falta'], 'ac':item['ac']}
                    aux['desc'] = item['disc']
                    aux['cod'] = item['codigo_disciplina']
            
            notas.append(aux)

            aluno['notas_if'] = notas


        # calcular frequência
  

        sql = 'select disciplina, sum(falta) - sum(ac) as faltas from notas left join turma on turma.num_classe = notas.num_classe left join turma_if on turma_if.num_classe = notas.num_classe where ra_aluno = %s and (turma.ano = %s or turma_if.ano = %s) group by disciplina ' % (aluno['ra_aluno'], ano, ano)
        #print(sql)
        freq_disciplinas = banco.executarConsulta(sql)
        
        freq_final = {}
        conceito_final = {}

        for disc in freq_disciplinas:
            sql = 'select '
            sql += 'ifnull((select aulas_dadas from vinculo_prof_disc where bimestre = 1 and disciplina = %s and num_classe = (select notas.num_classe from notas left join turma on turma.num_classe = notas.num_classe left join turma_if on turma_if.num_classe = notas.num_classe where disciplina = %s and ra_aluno = %s and bimestre = 1 and (turma.ano = %s or turma_if.ano = %s) and (turma.duracao = %s or turma_if.duracao = %s))), 0) + ' % (disc['disciplina'], disc['disciplina'], aluno['ra_aluno'], ano, ano, duracao, duracao)
            sql += 'ifnull((select aulas_dadas from vinculo_prof_disc where bimestre = 2 and disciplina = %s and num_classe = (select notas.num_classe from notas left join turma on turma.num_classe = notas.num_classe left join turma_if on turma_if.num_classe = notas.num_classe where disciplina = %s and ra_aluno = %s and bimestre = 2 and (turma.ano = %s or turma_if.ano = %s) and (turma.duracao = %s or turma_if.duracao = %s))), 0) + ' % (disc['disciplina'], disc['disciplina'], aluno['ra_aluno'], ano, ano, duracao, duracao)
            sql += 'ifnull((select aulas_dadas from vinculo_prof_disc where bimestre = 3 and disciplina = %s and num_classe = (select notas.num_classe from notas left join turma on turma.num_classe = notas.num_classe left join turma_if on turma_if.num_classe = notas.num_classe where disciplina = %s and ra_aluno = %s and bimestre = 3 and (turma.ano = %s or turma_if.ano = %s) and (turma.duracao = %s or turma_if.duracao = %s))), 0) + ' % (disc['disciplina'], disc['disciplina'], aluno['ra_aluno'], ano, ano, duracao, duracao)
            sql += 'ifnull((select aulas_dadas from vinculo_prof_disc where bimestre = 4 and disciplina = %s and num_classe = (select notas.num_classe from notas left join turma on turma.num_classe = notas.num_classe left join turma_if on turma_if.num_classe = notas.num_classe where disciplina = %s and ra_aluno = %s and bimestre = 4 and (turma.ano = %s or turma_if.ano = %s) and (turma.duracao = %s or turma_if.duracao = %s))), 0) as aulas_dadas ' % (disc['disciplina'], disc['disciplina'], aluno['ra_aluno'], ano, ano, duracao, duracao)

            print(sql)

            aulas_dadas = banco.executarConsulta(sql)[0]['aulas_dadas']
            try:
                freq_calc = 100 - (disc['faltas'] * 100 / aulas_dadas)
                freq_final[disc['disciplina']] = round(freq_calc, 1)
            except:
                freq_final[disc['disciplina']] = ''

            media = banco.executarConsultaVetor("select ifnull(media, '-') from conceito_final inner join turma on turma.num_classe = conceito_final.num_classe and turma.ano = %s where disciplina = %s and ra_aluno = %s" % (ano, disc['disciplina'], aluno['ra_aluno']))
            if len(media) > 0:
                conceito_final[disc['disciplina']] = banco.executarConsultaVetor("select ifnull(media, '-') from conceito_final inner join turma on turma.num_classe = conceito_final.num_classe and turma.ano = %s where disciplina = %s and ra_aluno = %s" % (ano, disc['disciplina'], aluno['ra_aluno']))[0]
            else:
                # verificar se é nota de if
                media = banco.executarConsultaVetor("select ifnull(media, '-') from conceito_final inner join turma_if on turma_if.num_classe = conceito_final.num_classe and turma_if.ano = %s where disciplina = %s and ra_aluno = %s" % (ano, disc['disciplina'], aluno['ra_aluno']))
                if len(media) > 0:
                    conceito_final[disc['disciplina']] = media[0]
                else:
                    conceito_final[disc['disciplina']] = 'null'


        aluno['freq'] = freq_final
        aluno['final'] = conceito_final


    return render_template('render_pdf/render_boletim.jinja', alunos=alunos, disciplinas=disciplinas, info_classe=info_classe, duracao=duracao, ano=ano, desc_duracao=desc_duracao)


@app.route('/ponto_adm', methods=['GET', 'POST'])
def ponto_adm():
    
    msg=''

    if request.method == 'POST': # houve envio de formulário

        if request.is_json:
            info = request.json

            if info['destino'] == 0: # pegar os dados do professor para editar no formulário
                detalhes = banco.executarConsulta("select cpf, nome, rg, ifnull(digito, '') as digito, cargo, plantao, estudante, horario, intervalo from funcionario_livro_ponto WHERE cpf = %s" % info['cpf'])[0]
                return jsonify(detalhes)
            
            elif info['destino'] == 1: # quadro de aulas
                lista = banco.executarConsulta(r"SELECT cpf, DATE_FORMAT(inicio,'%d/%m/%Y') as dt_inicio, DATE_FORMAT(fim,'%d/%m/%Y') as dt_fim, descricao FROM afastamentos_ponto_adm WHERE cpf = " + str(info['cpf']) + ' order by inicio')
                return jsonify(lista)

        if 'nome' in request.form: # inserir ou alterar novo funcionário

            dados = {}
            dados['cpf'] = request.form['cpf'].replace('.', '').replace('-', '')
            dados['nome'] = "'%s'" % request.form['nome']
            dados['rg'] = "'%s'" % request.form['rg']
            dados['digito'] = 'null' if request.form['digito_rg'] == '' else "'%s'" % request.form['digito_rg']
            dados['cargo'] = request.form['cargo']
            dados['horario'] = "'%s'" % request.form['txt_horario']
            dados['intervalo'] = "'%s'" % request.form['txt_intervalo']
            dados['estudante'] = 1 if 'estudante' in request.form else 0
            dados['plantao'] = 1 if 'plantao' in request.form else 0

            if banco.insertOrUpdate(dados, 'funcionario_livro_ponto'):
                msg = '<div class="alert alert-success alert-dismissible fade show" role="alert">' \
                        '<strong>Operação bem-sucedida!</strong> Dados do(a) Funcionário(a) <strong>' + dados['nome'] + '</strong> inseridos com sucesso!' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'  
            else:
                msg = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' \
                        '<strong>Atenção!</strong> Erro ao tentar inserir dados do funcionário no banco de dados!"' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'  


        if 'ativacao' in request.form: # é pra desativar ou ativar o funcionário
            ativacao = int(request.form['ativacao'])
            id = request.form['cpf']
            
            basic_sql = 'UPDATE funcionario_livro_ponto SET ativo = %s WHERE cpf = %s' % (ativacao, id)

            if banco.executeBasicSQL(basic_sql):
                if ativacao == 0:
                    msg = '<div class="alert alert-success alert-dismissible fade show" role="alert">' \
                            '<strong>Operação realizada com sucesso!</strong> Funcionário desativado do Livro Ponto' \
                            '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                            '</div>'    
                else:
                    msg = '<div class="alert alert-success alert-dismissible fade show" role="alert">' \
                            '<strong>Operação realizada com sucesso!</strong> Funcionário reativado no Livro Ponto' \
                            '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                            '</div>'                      
            else:
                msg = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' \
                        '<strong>Atenção!</strong> Erro ao tentar inserir dados do funcionário no banco de dados!"' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'    


        if 'info_afs' in request.form: # é pra criar a lista de afastamentos

            lista = json.loads(request.form['info_afs'])
            cpf = int(request.form['cpf'])

            print(lista)

            if banco.inserirAfastamentos(cpf, lista):
                msg = '<div class="alert alert-success alert-dismissible fade show" role="alert">' \
                        '<strong>Operação realizada com sucesso!</strong> Lista de Afastamentos registrados com sucesso!' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'    

            else:
                msg = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' \
                        '<strong>Atenção!</strong> Erro ao tentar inserir dados no banco de dados! Verifique se as datas não batem!' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'              


    cargos = banco.executarConsulta('select * from cargos_livro_ponto where tipo = 2')

    funcionarios = banco.executarConsulta("select nome, rg, CASE WHEN digito IS NULL THEN '' ELSE CONCAT('-', digito) END AS digito, cpf, cargos_livro_ponto.descricao as cargo from funcionario_livro_ponto inner join cargos_livro_ponto on cargos_livro_ponto.id = funcionario_livro_ponto.cargo where ativo = 1 order by nome")
    for funcionario in funcionarios:
        funcionario['raw_cpf'] = funcionario['cpf']
        cpf = "%011d" % funcionario['cpf']
        funcionario['cpf'] = '%s.%s.%s-%s' % (cpf[:3], cpf[3:6], cpf[6:9], cpf[9:])

        rg = "%08d" % int(funcionario['rg'])
        funcionario['rg'] = '%s.%s.%s%s' % (rg[:2], rg[2:5], rg[5:8], funcionario['digito'])

    desativados = banco.executarConsulta("select nome, rg, CASE WHEN digito IS NULL THEN '' ELSE CONCAT('-', digito) END AS digito, cpf, cargos_livro_ponto.descricao as cargo from funcionario_livro_ponto inner join cargos_livro_ponto on cargos_livro_ponto.id = funcionario_livro_ponto.cargo where ativo = 0 order by nome")
    for funcionario in desativados:
        funcionario['raw_cpf'] = funcionario['cpf']
        cpf = "%011d" % funcionario['cpf']
        funcionario['cpf'] = '%s.%s.%s-%s' % (cpf[:3], cpf[3:6], cpf[6:9], cpf[9:])

        rg = "%08d" % int(funcionario['rg'])
        funcionario['rg'] = '%s.%s.%s%s' % (rg[:2], rg[2:5], rg[5:8], funcionario['digito'])


    # pegar os meses
    meses = []
    data_atual = datetime.now()

    index = 1
    for mes in list(calendar.month_name)[1:]:
        meses.append({'desc':mes.title(), 'valor':index, 'atual':int(data_atual.strftime("%m")) == index})  
        index += 1  

    return render_template('livro_ponto_admin.jinja', meses=meses, ano=data_atual.strftime("%Y"), cargos=cargos, msg=msg, funcionarios=funcionarios, desativados=desativados)

@app.route('/ponto', methods=['GET', 'POST'])
def ponto():

    msg = ''

    if request.method == 'POST': # houve envio de formulário

        if request.is_json: # enviado por ajax
            info = request.json

            if info['destino'] == 0: # pegar os dados do professor para editar no formulário
                detalhes = banco.executarConsulta("select instancia_calendario, cpf, nome, rg, ifnull(digito, '') as digito, ifnull(rs, '') as rs, ifnull(pv, '') as pv, cargo, categoria, jornada, sede_classificacao, sede_controle_freq, ifnull(di, '') as di, ifnull(disciplina, 'null') as disciplina, ifnull(afastamento, 'null') as afastamento, assina_livro, ifnull(FNREF, '') as FNREF, ifnull(obs, '') as obs, ifnull(atpc, '') as atpc, ifnull(atpl, '') as atpl, ifnull(aulas_outra_ue, '') as aulas_outra_ue from professor_livro_ponto WHERE cpf = %s and di = %s" % (info['cpf'], info['di']))[0]
                return jsonify(detalhes)
            
            elif info['destino'] == 1: # pegar quadro aula
                quadro = banco.executarConsulta(r"select periodo,  DATE_FORMAT(inicio, '%H:%i') as inicio, DATE_FORMAT(fim, '%H:%i') as fim, ifnull(seg, '') as seg, ifnull(ter, '') as ter, ifnull(qua, '') as qua, ifnull(qui, '') as qui, ifnull(sex, '') as sex, ifnull(sab, '') as sab, ifnull(dom, '') as dom from horario_livro_ponto where cpf_professor = " + info['cpf'] + ' ORDER BY inicio')

                aulas_ue = banco.executarConsulta('select * from aulas_outra_ue_livro_ponto where cpf_professor = %s' % info['cpf'])
                aulas = {}

                for aula in aulas_ue:
                    aulas[aula['semana']] = aula['qtd']

                return jsonify({'quadro':quadro, 'aulas_ue':aulas})
            
            elif info['destino'] == 2: # pegar os dado do professor para exibir no formulário

                print(info)

                sql = "SELECT nome, rg, ifnull(digito, '') as digito, ifnull(rs, '') as rs, ifnull(pv, '') as pv, cargos_livro_ponto.descricao as cargo, concat(categoria_livro_ponto.letra, ' - ', categoria_livro_ponto.descricao) as categoria, " + \
                      "jornada_livro_ponto.descricao as jornada, sede_c.descricao as sede_classificacao, sede_f.descricao as sede_controle_freq, ifnull(di, '') as di, " + \
                      "CASE WHEN disciplina IS NULL THEN '-' ELSE disciplinas.descricao END as disciplina, " + \
                      "CASE WHEN afastamento IS NULL THEN '-' ELSE CONCAT(professor_livro_ponto.afastamento, ' - ', afastamento_livro_ponto.descricao) END as afastamento, " + \
                      "CASE WHEN assina_livro = 1 THEN 'Sim' ELSE 'Não' END as assina_livro, "  + \
                      "case when atpc > 0 or atpl > 0 then concat(atpc, ' ATPC(s) + ', atpl, ' ATPL(s)') else '' end as atpc, " + \
                      "ifnull(aulas_outra_ue, '') as aulas_outra_ue, " + \
                      "ifnull(FNREF, '') as FNREF, ifnull(obs, '') as obs " + \
                      "FROM professor_livro_ponto " + \
                      "LEFT JOIN cargos_livro_ponto ON cargos_livro_ponto.id = professor_livro_ponto.cargo " + \
                      "LEFT JOIN categoria_livro_ponto ON categoria_livro_ponto.id = professor_livro_ponto.categoria " + \
                      "LEFT JOIN jornada_livro_ponto ON jornada_livro_ponto.id = professor_livro_ponto.jornada " + \
                      "LEFT JOIN sede_livro_ponto AS sede_c ON sede_c.id = professor_livro_ponto.sede_classificacao " + \
                      "LEFT JOIN sede_livro_ponto AS sede_f ON sede_f.id = professor_livro_ponto.sede_controle_freq " + \
                      "LEFT JOIN disciplinas ON disciplinas.codigo_disciplina = professor_livro_ponto.disciplina " + \
                      "LEFT JOIN afastamento_livro_ponto ON afastamento_livro_ponto.id = professor_livro_ponto.afastamento " + \
                      "WHERE cpf = %s and di = %s" % (info['cpf'], info['di'])

                detalhes = banco.executarConsulta(sql)[0]

                aux = '%011d' % int(info['cpf'])
                detalhes['cpf'] = aux[:3] + "." + aux[3:6] + "." + aux[6:9] + "-" + aux[9:]

                aux_rg = '%08d' % int(detalhes['rg'])

                detalhes['rg'] = aux_rg[0:2] + "." + aux_rg[2:5] + "." + aux_rg[5:]

                if (detalhes['digito'] != ''):
                    detalhes['rg'] = detalhes['rg'] + "-" + detalhes['digito']

                # os detalhes estão completos, basta agora pegar o quadro
                quadro = banco.executarConsulta(r"select periodo_livro_ponto.descricao as periodo, DATE_FORMAT(inicio, '%H:%i') as inicio, DATE_FORMAT(fim, '%H:%i') as fim, ifnull(seg, '') as seg, ifnull(ter, '') as ter, ifnull(qua, '') as qua, ifnull(qui, '') as qui, ifnull(sex, '') as sex, ifnull(sab, '') as sab, ifnull(dom, '') as dom from horario_livro_ponto inner join periodo_livro_ponto on periodo_livro_ponto.id = horario_livro_ponto.periodo where cpf_professor = " + info['cpf'] + ' ORDER BY inicio')

                return jsonify({'quadro':quadro, 'detalhes':detalhes})
            
        if 'quadro' in request.form: # é pra cadastrar o quadro de aulas do professor
            id = request.form['cpf']
            quadro = json.loads(request.form.getlist('quadro')[0])['lista_final']
            outras_ue = json.loads(request.form.getlist('quadro')[0])['aulas_ue']

            if banco.inserirQuadro(id, quadro, outras_ue):
                msg = '<div class="alert alert-success alert-dismissible fade show" role="alert">' \
                        '<strong>Operação realizada com sucesso!</strong> Quadro de aulas do professor registrado com sucesso!' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'    

            else:
                msg = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' \
                        '<strong>Atenção!</strong> Erro ao tentar inserir dados do professor no banco de dados! Por favor quando for descrever a aula ou APTC, use no máximo 4 caracteres.' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'                   
            
        if 'ativacao' in request.form: # é pra desativar ou ativar o professor
            ativacao = int(request.form['ativacao'])
            id = request.form['cpf']
            di = request.form['di']
            
            basic_sql = 'UPDATE professor_livro_ponto SET ativo = %s WHERE cpf = %s and di = %s' % (ativacao, id, di)

            if banco.executeBasicSQL(basic_sql):
                if ativacao == 0:
                    msg = '<div class="alert alert-success alert-dismissible fade show" role="alert">' \
                            '<strong>Operação realizada com sucesso!</strong> Professor desativado do Livro Ponto' \
                            '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                            '</div>'    
                else:
                    msg = '<div class="alert alert-success alert-dismissible fade show" role="alert">' \
                            '<strong>Operação realizada com sucesso!</strong> Professor reativado no Livro Ponto' \
                            '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                            '</div>'                      
            else:
                msg = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' \
                        '<strong>Atenção!</strong> Erro ao tentar inserir dados do professor no banco de dados!"' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'                     


        if 'nome' in request.form: # é para cadastrar ou alterar professor

            # preparar dados
            dados = {}
            dados['cpf'] = request.form['cpf'].replace('.', '').replace('-', '')
            dados['nome'] = "'%s'" % request.form['nome']
            dados['rg'] = "'%s'" % request.form['rg']
            dados['digito'] = 'null' if request.form['digito_rg'] == '' else "'%s'" % request.form['digito_rg']
            dados['rs'] = 'null' if request.form['rs'] == '' else request.form['rs']
            dados['pv'] = 'null' if request.form['pv'] == '' else request.form['pv']
            dados['cargo'] = request.form['cargo']
            dados['categoria'] = request.form['categoria']
            dados['jornada'] = request.form['jornada']
            dados['sede_classificacao'] = request.form['sede_classificacao']
            dados['sede_controle_freq'] = request.form['sede_frequencia']
            dados['di'] = 'null' if request.form['di'] == '' else request.form['di']
            dados['disciplina'] = request.form['disciplina']
            dados['afastamento'] = request.form['afastamento']
            dados['FNREF'] = 'null' if request.form['faixa'] == '' else "'%s'" % request.form['faixa']
            dados['assina_livro'] = 1 if 'assina' in request.form else 0
            dados['obs'] = 'null' if request.form['obs'] == '' else "'%s'" % request.form['obs']
            dados['atpc'] = 'null' if request.form['atpc'] == '' else "'%s'" % request.form['atpc']
            dados['atpl'] = 'null' if request.form['atpl'] == '' else "'%s'" % request.form['atpl']
            dados['aulas_outra_ue'] = 'null' if request.form['aulas'] == '' else "'%s'" % request.form['aulas']
            dados['instancia_calendario'] = request.form['cb_instancia']

            if banco.insertOrUpdate(dados, 'professor_livro_ponto'):
                msg = '<div class="alert alert-success alert-dismissible fade show" role="alert">' \
                        '<strong>Operação bem-sucedida!</strong> Dados do(a) Professor(a) <strong>' + dados['nome'] + '</strong> inseridos com sucesso!' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'  
            else:
                msg = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' \
                        '<strong>Atenção!</strong> Erro ao tentar inserir dados do professor no banco de dados!"' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'                   


    cargos = banco.executarConsulta('select * from cargos_livro_ponto where tipo = 1')
    categorias = banco.executarConsulta('select * from categoria_livro_ponto')
    jornadas = banco.executarConsulta('select * from jornada_livro_ponto')
    escolas = banco.executarConsulta("select id, concat('UA: ', id, ' - ', descricao) as descricao from sede_livro_ponto order by id")
    disciplinas = banco.executarConsulta('select codigo_disciplina as id, descricao from disciplinas where classificacao = 1 order by descricao')
    afastamentos = banco.executarConsulta("select id, concat(id, ' - ', descricao) as desc_longo from afastamento_livro_ponto order by descricao")

    professores = banco.executarConsulta("select nome, rg, CASE WHEN digito IS NULL THEN '' ELSE CONCAT('-', digito) END AS digito, cpf, di, categoria_livro_ponto.descricao as categoria, ifnull(afastamento_livro_ponto.descricao, '-') as afastamento from professor_livro_ponto inner join categoria_livro_ponto on categoria_livro_ponto.id = professor_livro_ponto.categoria left join afastamento_livro_ponto on afastamento_livro_ponto.id = professor_livro_ponto.afastamento where ativo = 1 order by nome")
    for professor in professores:
        professor['raw_cpf'] = professor['cpf']
        cpf = "%011d" % professor['cpf']
        professor['cpf'] = '%s.%s.%s-%s' % (cpf[:3], cpf[3:6], cpf[6:9], cpf[9:])

        rg = "%08d" % int(professor['rg'])
        professor['rg'] = '%s.%s.%s%s' % (rg[:2], rg[2:5], rg[5:8], professor['digito'])

    desativados = banco.executarConsulta("select nome, rg, CASE WHEN digito IS NULL THEN '' ELSE CONCAT('-', digito) END AS digito, cpf, di from professor_livro_ponto where ativo = 0 order by nome")
    for professor in desativados:
        professor['raw_cpf'] = professor['cpf']
        cpf = "%011d" % professor['cpf']
        professor['cpf'] = '%s.%s.%s-%s' % (cpf[:3], cpf[3:6], cpf[6:9], cpf[9:])

        rg = "%08d" % int(professor['rg'])
        professor['rg'] = '%s.%s.%s%s' % (rg[:2], rg[2:5], rg[5:8], professor['digito'])    


    periodos = banco.executarConsulta('select * from periodo_livro_ponto')
    instancias = banco.executarConsulta('select * from calendario_ponto order by descricao')


    # pegar os meses
    meses = []
    data_atual = datetime.now()

    index = 1
    for mes in list(calendar.month_name)[1:]:
        meses.append({'desc':mes.title(), 'valor':index, 'atual':int(data_atual.strftime("%m")) == index})

        index += 1    

    return render_template('livro_ponto.jinja', cargos=cargos, categorias=categorias, jornadas=jornadas, escolas=escolas, disciplinas=disciplinas, afastamentos=afastamentos, msg=msg, professores=professores, desativados=desativados, periodos=periodos, meses=meses, ano=data_atual.strftime("%Y"), instancias=instancias)


@app.route('/calendario', methods=['GET', 'POST'])
def calendario():

    status = ''
    ano = datetime.now().year
    instancia = 1

    if request.method == 'POST': # recebeu novo pedido para cadastrar evento ou instancia

        if 'nova_instancia' in request.form:
            if banco.executeBasicSQL("INSERT INTO calendario_ponto(descricao) VALUES('%s')" % request.form['nova_instancia']):
                status = '<div class="alert alert-success alert-dismissible fade show" role="alert">' \
                        '<strong>Operação bem sucedida!</strong> Instância cadastrada com sucesso.' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'  
            else:
                status = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' \
                        '<strong>Erro falta!</strong> Falha ao tentar inserir informações no Banco de Dados!' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'                              
            

        elif 'cb_instancias' in request.form:
            instancia = int(request.form['cb_instancias'])
        
        else:
            data_inicial = request.form['data_inicial']
            data_final = request.form['data_final']
            evento = request.form['cb_evento']
            descricao = request.form['descricao']
            instancia = int(request.form['instancia'])

            # verificar se o ano foi digitado corretamente
            if int(data_inicial[0:4]) == ano and int(data_final[0:4]) == ano:
                # prosseguir
                if banco.inserirEvento(data_inicial, data_final, evento, descricao, instancia):
                    status = '<div class="alert alert-success alert-dismissible fade show" role="alert">' \
                            '<strong>Operação bem sucedida!</strong> Evento cadastrado com sucesso.' \
                            '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                            '</div>'          
                else:
                    status = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' \
                            '<strong>Erro falta!</strong> Falha ao tentar inserir informações no Banco de Dados!' \
                            '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                            '</div>'                  
            else:
                status = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' \
                        '<strong>Atenção!</strong> Por favor digite uma data dentro do <strong>ano atual!</strong>' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'

    # montando calendário

    calendario = []
    letivos = 0

    # percorrendo todo os meses do ano
    for i in range(1, 13):
        qtd_dias = calendar.monthrange(ano, i)[1]

        dias = []
        letivos_mes = 0

        for j in range(1, qtd_dias + 1):
            date_aux = datetime(ano, i, j)
            

            if date_aux.strftime("%a") != 'dom' and date_aux.strftime("%a") != 'sáb': # dias de semana

                evento = banco.executarConsulta("select cat_letivo.descricao, cat_letivo.qtd_letivo from eventos_calendario inner join cat_letivo on cat_letivo.id = eventos_calendario.evento where ('%s' BETWEEN data_inicial and data_final) and instancia_calendario = %s" % (date_aux.strftime("%y-%m-%d"), instancia))

                situacao = 'Letivo'
                color = 'table-light'

                if (len(evento) > 0):
                    letivos += evento[0]['qtd_letivo']
                    letivos_mes += evento[0]['qtd_letivo']
                    situacao = evento[0]['descricao']
                    color = 'table-danger'
                else:
                    letivos += 1
                    letivos_mes += 1

                dias.append({'dia':j, 'semana':date_aux.strftime("%a"), 'situacao':situacao, 'color':color})
            else:

                evento = banco.executarConsulta("select cat_letivo.descricao, cat_letivo.qtd_letivo from eventos_calendario inner join cat_letivo on cat_letivo.id = eventos_calendario.evento where ('%s' BETWEEN data_inicial and data_final) and instancia_calendario = %s" % (date_aux.strftime("%y-%m-%d"), instancia))

                situacao = '-'
                color = 'table-secondary'

                if (len(evento) > 0):
                    letivos += evento[0]['qtd_letivo']
                    letivos_mes += evento[0]['qtd_letivo']
                    situacao = evento[0]['descricao']

                    if situacao == 'Reposição':
                        color = 'table-warning'
                    else:
                        color = 'table-danger'

                dias.append({'dia':j, 'semana':date_aux.strftime("%a"), 'situacao':situacao, 'color':color})

        #desc_mes = datetime(ano, i, 1)

        calendario.append({'dias':dias, 'descricao':calendar.month_name[i].title(), 'letivos':letivos_mes})

    eventos = banco.executarConsulta('select id, descricao from cat_letivo')
    instancias = banco.executarConsulta('select * from calendario_ponto order by descricao')

    return render_template('calendario.jinja', calendario=calendario, letivos=letivos, ano=ano, eventos=eventos, status=status, instancias=instancias, instancia=instancia)

if __name__ == '__main__':
    #app.run('0.0.0.0',port=80)
    #app.run(debug=True)
    app.run(debug=True, use_reloader=True, port=80)
    #serve(app, host='0.0.0.0', port=80, threads=8)