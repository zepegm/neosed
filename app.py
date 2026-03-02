#import locale
from MySQL import db
from getInfoSED import buscarCPF
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, Response
from waitress import serve
from datetime import datetime, date, timedelta
from werkzeug.utils import secure_filename
from excel import xls, open_xls
from utilitarios import converterLista, getMes, hojePorExtenso, series_fund, getSituacao, converterDataMySQL, encriptar, extrair_numeros, montar_eventos, hsl_for_key, montar_grade_prof, pastel_from_label
from flask_socketio import SocketIO, emit
from collections import defaultdict
import pandas as pd
import subprocess
import os
import csv
import json
from pyppeteer import launch
from pyppeteer import connect
import locale
import math
import calendar
from jinja_try_catch import TryCatchExtension
from PyPDF2 import PdfMerger
from decimal import Decimal, ROUND_HALF_UP
from sed_api import start_context, get_escolas, get_unidades, get_classes, get_info_aluno, get_alunos_num_classe, get_alunos_codigo, get_matriz_curricular, get_grade, get_professor_info, get_funcionario_info


locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')

UPLOAD_FOLDER = os.path.join('staticFiles', 'uploads')

# vou ver se consigo abrir certinho
app=Flask(__name__)
app.secret_key = "abc123"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'justasecretkeythatishouldputhere'
socketio = SocketIO(app, async_mode='threading')

app.jinja_env.add_extension(TryCatchExtension)

#BLOCOS_IGNORAR = {'', '-', 'ATPC', 'SLN', 'REAN', 'PATN'}
BLOCOS_IGNORAR = {'', '-'}
SEMANA_SIGLAS = ['seg', 'ter', 'qua', 'qui', 'sex', 'sáb', 'dom']  # 0=seg ... 6=dom

def ordenar_turmas(nome_turma):
    # Definimos o peso: Fundamental (º) ganha 0, Médio (ª) ganha 1
    peso_nivel = 0 if 'º' in nome_turma else 1
    
    # Extraímos apenas o número do início (ex: '6' de '6ºA')
    # Se não houver número, usamos 0 para não quebrar
    import re
    numero = re.search(r'\d+', nome_turma)
    ordem_numerica = int(numero.group()) if numero else 0
    
    # Retorna uma tupla: primeiro ordena pelo peso do nível, depois pelo número
    return (peso_nivel, ordem_numerica, nome_turma)

def ph(seq):
    """Gera '(%s,%s,%s,...)' com o tamanho certo; se vazio, retorna '(NULL)'."""
    return '(' + ','.join(['%s'] * len(seq)) + ')' if seq else '(NULL)'  

def contar_quadro_semanais(quadro):
    """Conta quantos blocos/aulas existem por dia na tabela lateral (quadro_aula)."""
    tot = {k: 0 for k in SEMANA_SIGLAS}
    for linha in (quadro or []):
        for k in SEMANA_SIGLAS:
            v = (linha.get(k) or '').strip()
            if v not in BLOCOS_IGNORAR:
                tot[k] += 1
    return tot

def render_exibicao(exibicao, inicio, fim):
    if not exibicao:
        return ''
    return (exibicao
            .replace('{inicio}', inicio.strftime('%d/%m'))
            .replace('{fim}', fim.strftime('%d/%m/%Y'))
            .replace('{ini_c}', inicio.strftime('%d/%m/%Y')))

def evento_do_dia(evt_map, instancia, d):
    for e in evt_map.get(int(instancia), []):
        if e['data_inicial'] <= d <= e['data_final']:
            return e
    return None

def licenca_do_dia(lic_map, cpf, d):
    for l in lic_map.get(int(cpf), []):
        if l['inicio'] <= d <= l['fim']:
            return l
    return None

# Função para formatar timedelta
def formatar_timedelta_hhmm(delta):
    total_segundos = int(delta.total_seconds())
    horas, resto = divmod(total_segundos, 3600)
    minutos, _ = divmod(resto, 60)
    return f"{horas:02}:{minutos:02}"

def diferenca_maior(tempo1, tempo2, minutos=40):
    # Subtrair os dois objetos timedelta
    diferenca = tempo1 - tempo2
    # Converter a diferença em minutos
    diferenca_em_minutos = diferenca.total_seconds() / 60
    # Retornar se é maior que x minutos
    return diferenca_em_minutos > minutos    

# Registrar o filtro no Jinja
app.jinja_env.filters['formatar_timedelta'] = formatar_timedelta_hhmm
app.jinja_env.filters['diferenca_maior_que_40'] = diferenca_maior


#locale.setlocale(locale.LC_ALL, "")

#banco = db({'host':"localhost", 'user':'root', 'passwd':'Yasmin', 'db':'neosed'})

#banco = db({'host':"neosed.net",    # your host, usually localhost
            #'user':"username",         # your username
            #'passwd':"password",  # your password
            #'db':"neosed"})

# Lê o arquivo JSON
with open("config_db.json") as f:
    config = json.load(f)

# configuração do server principal
banco = db(config)


home_directory = os.path.expanduser( '~' )
aux_info = None

@app.route('/', methods=['GET', 'POST'])
def index():

    msg = ""
    ano = datetime.now().year
    #ano = 2023

    if request.method == 'POST':

        if request.is_json:

            info = request.json

            if info['destino'] == 1:
                data = banco.executarConsulta(f"select distinct tipo, tipo_disc_matriz.descricao as desc_tipo, disc_disciplina as disc, disciplinas.descricao as desc_disc, area, ifnull(area_matriz.desc_curta, '-') as desc_area, qtd_aulas, minutos, ifnull(professor_livro_ponto.nome, '-') as nome, ifnull(professor_livro_ponto.cpf, 0) as cpf, ifnull(prof_ele.nome, '-') as nome_2, ifnull(prof_ele.cpf, 0) as cpf_2 from matriz_curricular inner join disciplinas on disciplinas.codigo_disciplina = disc_disciplina inner join area_matriz on area_matriz.id = area inner join tipo_disc_matriz on tipo_disc_matriz.id = tipo left join professor_livro_ponto on professor_livro_ponto.cpf = matriz_curricular.cpf_professor left join professor_livro_ponto as prof_ele on prof_ele.cpf = matriz_curricular.cpf_professor_2 where num_classe = {info['num_classe']} order by tipo, area, disc_disciplina")
            
                return jsonify(data)
            
            elif info['destino'] == 2:
                data = banco.executarConsulta(f"select TIME_FORMAT(inicio, '%H:%i') as inicio, TIME_FORMAT(fim, '%H:%i') as fim from horario_turma where num_classe = {info['num_classe']} order by pos")
            
                return jsonify(data)
        
        if 'horario' in request.form:
            horario = json.loads(request.form['horario'])
            if banco.alterarHorario(horario):
                msg = '<div class="alert alert-success alert-dismissible fade show" role="alert">' \
                        '<strong>Operação bem-sucedida!</strong> Horário alterado com sucesso!' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'
            else:
                msg = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' \
                        '<strong>Atenção!</strong> Erro ao tentar alterar horário, verifique se foi tudo digitado corretamente.' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'

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

            classe = {'num_classe':request.form['txtnumeroclasse'], 'nome_turma':"'" + request.form['txtnometurma'] + "'", 'duracao':request.form['cbduracao'], 'tipo_ensino':request.form['cbtipoensino'], 'periodo':request.form['cbperiodo'], 'ano':request.form['ano'], 'apelido':"'" + request.form['txtapelidoturma']  + "'", 'id_oculto':request.form['id_oculto']}
            
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
            classe = {'num_classe':request.form['txtnumeroclasse_edit'], 'nome_turma':"'" + request.form['txtnometurma_edit'] + "'", 'duracao':request.form['cbduracao_edit'], 'tipo_ensino':request.form['cbtipoensino_edit'], 'periodo':request.form['cbperiodo_edit'], 'apelido':f"'{request.form['txtapelidoturma_edit']}'", 'id_oculto':request.form['id_oculto']}
            
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
                turmas = banco.executarConsulta('select num_classe, nome_turma, duracao.descricao as duracao, turma.duracao as id_duracao, turma.tipo_ensino as id_ensino, periodo.descricao as periodo, turma.periodo as id_periodo, turma.apelido, ifnull(turma.id_oculto, "") as id_oculto from turma INNER JOIN duracao ON duracao.id = turma.duracao INNER JOIN periodo ON periodo.id = turma.periodo where tipo_ensino = %s and ano = %s order by duracao, nome_turma' % (item['id'], ano))
            else:
                turmas = banco.executarConsulta('select num_classe, nome_turma, duracao.descricao as duracao, turma_if.duracao as id_duracao, turma_if.tipo_ensino as id_ensino, periodo.descricao as periodo, turma_if.periodo as id_periodo, turma_if.categoria as categoria from turma_if INNER JOIN duracao ON duracao.id = turma_if.duracao INNER JOIN periodo ON periodo.id = turma_if.periodo where tipo_ensino = %s and ano = %s order by duracao, nome_turma' % (item['id'], ano))
                print('select num_classe, nome_turma, duracao.descricao as duracao, turma_if.duracao as id_duracao, turma_if.tipo_ensino as id_ensino, periodo.descricao as periodo, turma_if.periodo as id_periodo, turma_if.categoria as categoria from turma_if INNER JOIN duracao ON duracao.id = turma_if.duracao INNER JOIN periodo ON periodo.id = turma_if.periodo where tipo_ensino = %s and ano = %s order by duracao, nome_turma' % (item['id'], ano))
                color = 'table-primary'
                
            listaTurmas.append({'tipo_ensino':item, 'lista':turmas, 'color':color})


    # pegar dados para compor a matriz
    tipo_disc = banco.executarConsulta('select id, descricao from tipo_disc_matriz')
    area_conhecimento = banco.executarConsulta('select id, desc_curta from area_matriz where id > 0')
    disc = banco.executarConsulta('select codigo_disciplina, descricao from disciplinas order by codigo_disciplina')
    professores = banco.executarConsulta('select distinct nome, cpf from professor_livro_ponto where ativo = 1 order by nome')

    # gerar uma lista de meses para preencher a lista de chamada
    meses = []
    for i in range(1, 13):
        selected = ''
        if i == datetime.now().month:
            selected = 'selected'
        meses.append({'mes':getMes(i).title(), 'value':i, 'selected':selected})

    return render_template('home.jinja', tipo_ensino=tipo_ensino, calendario=calendario[0], duracao=duracao, periodo=periodo, msg=msg, listaTurmas=listaTurmas, tipo_ensino_itinerario=tipo_ensino_itinerario, cat_itinerario=cat_itinerario, anos=anos, tipo_disc=tipo_disc, area_conhecimento=area_conhecimento, disc=disc, professores=professores, meses=meses, ano=ano)

@app.route('/modulo_sed', methods=['GET', 'POST'])
def modulo_sed():

    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            auth = {'cookie_SED': banco.executarConsultaVetor("select valor from config where id_config = 'credencial'")[0]}

            try:
                context = start_context(auth)
                result_escolas = get_escolas(context)

                id_escola = result_escolas[0]['id']
                result_unidades = get_unidades(context, id_escola)
                id_unidade = result_unidades[0]['id']

                # a partir daqui será dividido as tarefas dependendo do objetivo desejado

                if data['destino'] == 'id_classe':
                    result_classes = get_classes(context, int(data['ano']), id_escola, id_unidade)
                
                    for classe in result_classes:
                        if int(classe['id_b']) == int(data['num_classe']):
                            return jsonify({'id_classe':classe['id']})

                return jsonify(False)
            except Exception as e:
                print(e)
                return jsonify(False)

@app.route('/credenciais', methods=['GET', 'POST'])
def credenciais():

    result = ''

    if request.method == 'POST':
        if 'txt_credencial' in request.form:
            cookie = request.form['txt_credencial']
            banco.executeBasicSQL("delete from config where id_config = 'credencial'")
            banco.executeBasicSQL("insert into config (id_config, valor) values ('credencial', '%s')" % cookie)

            result = '<div class="alert alert-success alert-dismissible fade show" role="alert">' \
                        '<strong>Operação bem-sucedida!</strong> Credencial salva com sucesso!' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'

    credencial = banco.executarConsultaVetor("select valor from config where  id_config = 'credencial'")

    return render_template('credenciais.jinja', result=result, credencial=credencial[0] if credencial else '')


@app.route('/salvar_grade', methods=['GET', 'POST'])
def salvar_grade():

        if request.method == 'POST':

            if request.is_json:

                data = request.get_json()

                if banco.alterarGrade(data['num_classe'], data['disciplinas']):
                    msg = '<div class="alert alert-success alert-dismissible fade show" role="alert">' \
                            '<strong>Operação bem-sucedida!</strong> Grade atualizada com sucesso!' \
                            '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                            '</div>'
                else:
                    msg = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' \
                            '<strong>Atenção!</strong> Erro ao tentar salvar grade, <strong>Contate o administrador!</strong>' \
                            '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                            '</div>'
                    
                return jsonify({'msg':msg})


@app.route('/grade', methods=['GET', 'POST'])
def grade():

    msg = ''

    anos = banco.executarConsultaVetor('select ano from calendario order by ano desc')

    ano = anos[0]

    if request.method == 'POST':
        if 'ano' in request.form:
            ano = request.form['ano']

        if 'num_classe_import_sed' in request.form:

            try:
                auth = {'cookie_SED': banco.executarConsultaVetor("select valor from config where id_config = 'credencial'")[0]}
                context = start_context(auth)

                grade = get_grade(context, request.form['num_classe_import_sed'])

                if banco.alterarGrade(request.form['num_classe_import_sed'], grade):
                    msg = '<div class="alert alert-success alert-dismissible fade show" role="alert">' \
                            '<strong>Operação bem-sucedida!</strong> Grade atualizada com sucesso!' \
                            '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                            '</div>'
                else:
                    msg = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' \
                            '<strong>Atenção!</strong> Erro ao tentar salvar grade, <strong>Contate o administrador!</strong>' \
                            '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                            '</div>'

            except Exception as e:
                msg = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' \
                        '<strong>Atenção!</strong> Erro ao tentar importar grade, <strong>Verifique as credenciais da SED!</strong>' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'
                print(e)

        if 'num_classe_import' in request.form:
            num_classe = request.form['num_classe_import']

            # pegar disciplinas da turma
            disciplinas = banco.executarConsulta('select distinct abv, codigo_disciplina from disciplinas inner join matriz_curricular on matriz_curricular.disc_disciplina = codigo_disciplina and matriz_curricular.num_classe = %s' % num_classe)

            # converter lista de disciplinas para json
            disc_dict = {}
            for item in disciplinas:
                disc_dict[item['abv']] = int(item['codigo_disciplina'])

            disc_dict['CLUBE'] = -2
            disc_dict['TUTORIA'] = -1
            disc_dict['Eletiva'] = 8465
            disc_dict['ALMOÇO'] = -3

            try:

                # importar grade
                file = request.files['file']

                if file:
                    excel = open_xls(file)

                    total_rows = excel.getTotalRows()
                    first_row = 5
                    first_col = 3

                    lista = []

                    for i in range(first_row, total_rows + 1):
                        if excel.getCell(i, first_col) not in ('Intervalo', '', None, 'Segunda-feira'):
                            linha = {}
                            linha['Seg'] = disc_dict[excel.getCell(i, first_col)]
                            linha['Ter'] = disc_dict[excel.getCell(i, first_col + 1)]
                            linha['Qua'] = disc_dict[excel.getCell(i, first_col + 2)]
                            linha['Qui'] = disc_dict[excel.getCell(i, first_col + 3)]
                            linha['Sex'] = disc_dict[excel.getCell(i, first_col + 4)]
                        
                            lista.append(linha)
                    
                    if banco.alterarGrade(num_classe, lista):
                        msg = '<div class="alert alert-success alert-dismissible fade show" role="alert">' \
                                '<strong>Operação bem-sucedida!</strong> Grade atualizada com sucesso!' \
                                '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                                '</div>'
                    else:
                        msg = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' \
                                '<strong>Atenção!</strong> Erro ao tentar salvar grade, <strong>Contate o administrador!</strong>' \
                                '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                                '</div>'
                        
            except Exception as e:
                msg = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' \
                        '<strong>Atenção!</strong> Erro ao tentar importar grade, <strong>Verifique se exportou a planilha da turma certa!</strong>' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'
                print(e)

        if 'num_classe' in request.form:
            num_classe = request.form['num_classe']

            # limpar matriz curricular
            if banco.executeBasicSQL('delete from grade where num_classe = %s' % num_classe):
                msg = '<div class="alert alert-success alert-dismissible fade show" role="alert">' \
                        '<strong>Operação bem-sucedida!</strong> Grade limpa com sucesso!' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'
            else:
                msg = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' \
                        '<strong>Atenção!</strong> Erro ao tentar limpar grade, <strong>Contate o administrador!</strong>' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'

        if request.is_json:
            num_classe = request.get_json()

            # pegar matriz curricular
            matriz = banco.executarConsulta(f'select disc_disciplina as disc, qtd_aulas - (select count(disciplina) from grade where num_classe = {num_classe} and disciplina = disc) as qtd_aulas, disciplinas.descricao as abv, tipo from matriz_curricular inner join disciplinas on disciplinas.codigo_disciplina = matriz_curricular.disc_disciplina where num_classe = {num_classe}')

            # verificar se é PEI, se for adiciona tutoria e clube
            info = banco.executarConsulta(f'select tipo_ensino, ano from turma where num_classe = {num_classe}')[0]

            #horario = banco.executarConsultaVetor(f"select CONCAT(TIME_FORMAT(inicio, '%H:%i'), ' - ', TIME_FORMAT(fim, '%H:%i')) as horario from hora_aulas where ano = {info['ano']} and tipo_ensino = {info['tipo_ensino']} order by inicio")
            horario = banco.executarConsultaVetor(f"select CONCAT(TIME_FORMAT(inicio, '%H:%i'), ' - ', TIME_FORMAT(fim, '%H:%i')) as horario from horario_turma where num_classe = {num_classe} order by pos")

            # agora verificar se já existe uma grade cadastrada, se existir criar uma tulpa
            grade_cadastrada = banco.executarConsulta(f'select pos, semana, disciplina, disciplinas.descricao as abv from grade left join disciplinas on disciplinas.codigo_disciplina = disciplina where num_classe = {num_classe} order by pos, semana')
            qtd_linhas = len(horario)

            if info['tipo_ensino'] == 1 or info['tipo_ensino'] == 3:
                matriz.append({'disc':'-1', 'qtd_aulas':3, 'abv':'TUTORIA', 'tipo':1})
                matriz.append({'disc':'-2', 'qtd_aulas':3, 'abv':'CLUBE', 'tipo':1})
                matriz.append({'disc':'-3', 'qtd_aulas':5, 'abv':'ALMOÇO', 'tipo':1})
                #qtd_linhas += 11

            #qtd_linhas = math.floor(qtd_linhas / 5)

            #if info['tipo_ensino'] in (6, 7):
                #qtd_linhas = len(horario)

            return jsonify({'matriz':matriz, 'horario':horario, 'grade':grade_cadastrada, 'qtd_linhas':qtd_linhas})

    ls_anos = []

    for a in anos:
        if int(a) == int(ano):
            ls_anos.append({'ano':a, 'selected':'selected'})
        else:
            ls_anos.append({'ano':a, 'selected':''})

    turmas = banco.executarConsulta(f'select num_classe, nome_turma, duracao.descricao as duracao from turma inner join duracao on duracao.id = turma.duracao where ano = {ano} order by turma.duracao, nome_turma')

    disciplinas = banco.executarConsultaVetor('select codigo_disciplina from disciplinas where codigo_disciplina > -3 order by codigo_disciplina')
    cores = ['#becaa8', '#d084c0', '#c8b8ea', '#d9e9ac', '#96d8ad', '#e7a6c3', '#d8d796', '#9df2f3', '#ee9dc1', '#b1aaf7', '#f9cc87', '#afb3de', '#b3e29e', '#fce5bb', '#a5d4fe', '#cedfb5', '#c3b9af', '#d98deb', '#e2d3d2', '#b9e1d8', '#b99dc2', '#b6efeb', '#d3f98f', '#bbfeb9', '#a8e5f0', '#e98dbf', '#edcd93', '#a8bcab', '#96caac', '#97c4ac', '#b7a2fa', '#c582cf', '#cd8eb9', '#8cff84', '#e5d180', '#bd8ff2', '#c98ce9', '#94fcb6', '#bcbaf9', '#b7c8a7', '#dbe7cf', '#e1d2af', '#e4cac3', '#fdb0db', '#dfad80', '#adf6eb', '#a4eebd', '#8f86b4', '#93c3ae', '#a2b5da']

    css_disc = [{'disc':'-3', 'cor':"#ff5e00"}]
    contador = 0

    for item in disciplinas:
        try:
            css_disc.append({'disc':item, 'cor':cores[contador]})
            contador += 1
        except: 
            contador = 0
            css_disc.append({'disc':item, 'cor':cores[contador]})
            contador += 1

    hoje = datetime.today().strftime("%Y-%m-%d")

    return render_template('grade.jinja', anos=ls_anos, turmas=turmas, css_disc=css_disc, msg=msg, data=hoje)


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

            if (opcao == 3):
                combo_final.append('<option value="3" selected>Lista Geral de Funcionários</option>')
            else:
                combo_final.append('<option value="3">Lista Geral de Funcionários</option>')


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

            elif (opcao == 3): #lista geral de funcionários

                titulos = ['Quadro Administrativo', 'Docentes Ativos', 'Docentes Ativos de outra UE', 'Docentes Afastados/Interrupção de Exercício']
                listas = []

                listas.append(banco.executarConsulta(r"select nome, rg, digito, cpf, di, DATE_FORMAT(nascimento, '%d/%m/%Y') as nascimento, rs, pv, FNREF, categoria_livro_ponto.letra as categoria, cargos_livro_ponto.abv from funcionario_livro_ponto inner join categoria_livro_ponto on categoria_livro_ponto.id = funcionario_livro_ponto.categoria inner join cargos_livro_ponto on cargos_livro_ponto.id = funcionario_livro_ponto.cargo where ativo = 1 order by nome"))
                listas.append(banco.executarConsulta(r"select nome, rg, digito, cpf, di, DATE_FORMAT(nascimento, '%d/%m/%Y') as nascimento, rs, pv, FNREF, categoria_livro_ponto.letra as categoria,       cargos_livro_ponto.abv from professor_livro_ponto inner join categoria_livro_ponto on categoria_livro_ponto.id = professor_livro_ponto.categoria inner join cargos_livro_ponto on cargos_livro_ponto.id = professor_livro_ponto.cargo where ativo = 1 and sede_controle_freq = 41707 and assina_livro = 1 order by nome"))
                listas.append(banco.executarConsulta(r"select nome, rg, digito, cpf, di, DATE_FORMAT(nascimento, '%d/%m/%Y') as nascimento, rs, pv, FNREF, categoria_livro_ponto.letra as categoria,       cargos_livro_ponto.abv from professor_livro_ponto inner join categoria_livro_ponto on categoria_livro_ponto.id = professor_livro_ponto.categoria inner join cargos_livro_ponto on cargos_livro_ponto.id = professor_livro_ponto.cargo where ativo = 1 and assina_livro = 1 and sede_controle_freq != 41707 order by nome"))
                listas.append(banco.executarConsulta(r"select nome, rg, digito, cpf, di, DATE_FORMAT(nascimento, '%d/%m/%Y') as nascimento, rs, pv, FNREF, categoria_livro_ponto.letra as categoria,       cargos_livro_ponto.abv from professor_livro_ponto inner join categoria_livro_ponto on categoria_livro_ponto.id = professor_livro_ponto.categoria inner join cargos_livro_ponto on cargos_livro_ponto.id = professor_livro_ponto.cargo where ativo = 1 and assina_livro = 0 order by nome"))


                for lista in listas:
                    for item in lista:
                        rg = "%08d" % int(item['rg'])
                        if (int(item['rg']) == int(item['cpf'])):
                            item['rg'] = "CIN"
                        elif item['digito'] == None:
                            item['rg'] = '%s.%s.%s' % (rg[:2], rg[2:5], rg[5:8])
                        else:
                            item['rg'] = '%s.%s.%s-%s' % (rg[:2], rg[2:5], rg[5:8], item['digito'])                            

                        cpf = "%011d" % item['cpf']
                        item['cpf'] = '%s.%s.%s-%s' % (cpf[:3], cpf[3:6], cpf[6:9], cpf[9:])

                        item['rs'] = "%08d" % item['rs']
                        item['pv'] = "%02d" % item['pv']

                return render_template('relatorios.jinja', opcao = 3, lista_final=listas, combo_final=combo_final, titulos=titulos)


    combo_final = ['<option value="0">Lista de Alunos Ativos Faltando RG ou CPF</option>', '<option value="1">Lista de Alunos Ativos Faltando RG</option>', '<option value="2">Lista de Alunos Ativos Faltando CPF</option>', '<option value="3">Lista Geral de Funcionários</option>']

    return render_template('relatorios.jinja', opcao = -1, combo_final=combo_final)

@app.route('/render_livro_ponto_adm',  methods=['GET', 'POST'])
def render_livro_ponto_adm():

    cpf = int(request.args.getlist('cpf')[0])
    mes = int(request.args.getlist('mes')[0])
    ano = int(request.args.getlist('ano')[0])

    dados = banco.executarConsulta("select nome, cpf, rg, digito, horario, intervalo, cargos_livro_ponto.descricao as cargo, CASE WHEN estudante = 1 THEN 'Sim' ELSE 'Não' END AS estudante, CASE WHEN plantao = 1 THEN 'Sim' ELSE 'Não' END AS plantao from funcionario_livro_ponto inner join cargos_livro_ponto on cargos_livro_ponto.id = funcionario_livro_ponto.cargo where cpf = %s" % cpf)[0]
    nome_escola = banco.executarConsultaVetor("select descricao from sede_livro_ponto where id = (select valor from config where id_config = 'ua_sede')")[0]

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

    return render_template('render_pdf/render_livro_ponto_adm.jinja', mes=getMes(mes), ano=ano, dados=dados, dias=dias_com_fim_de_semana, verso=verso_txt, afastamentos=afastamentos, nome_escola=nome_escola.upper(), banco=banco, cpf=cpf)



@app.route('/render_livro_ponto', methods=['GET', 'POST'])
def render_livro_ponto():

    # ---------- parâmetros ----------
    ano = int(request.args.getlist('ano')[0])
    mes = int(request.args.getlist('mes')[0])
    data_aux = date(ano, mes, 2)

    # UA padrão
    ua_padrao = banco.executarConsulta(
        "SELECT valor FROM config WHERE id_config = 'ua_sede'"
    )[0]['valor']

    # período letivo (duracao)
    duracao_tuple = (1, 3) if mes > 7 else (1, 2)

    # filtro individual
    professor_individual = request.args.getlist('professor')
    di_param = request.args.getlist('di')
    cond_ind = ''
    params_ind = []
    if professor_individual:
        cond_ind = " AND plp.cpf = %s AND plp.di = %s "
        params_ind = [int(professor_individual[0].replace('.', '').replace('-', '')),
                      int(di_param[0])]

    folha_extra = int(request.args.get('number', 0))

    # ---------- janelamento do mês ----------
    primeiro = date(ano, mes, 1)
    ultimo = date(ano, 12, 31) if mes == 12 else date(ano, mes + 1, 1) - timedelta(days=1)

    # ----------------------------------------------------
    # 1) Buscar lista de professores (sem subqueries correlacionadas)
    # ----------------------------------------------------
    
    ph_d = ph(duracao_tuple)  # ex.: '(%s,%s)' se tiver 2 itens
    
    
    sql_prof = f"""
    WITH
    lp_count AS (
        SELECT cpf_professor AS cpf, COUNT(*) AS aulas_lp
        FROM (
            SELECT cpf_professor, seg AS v, inicio, fim FROM horario_livro_ponto
            UNION ALL SELECT cpf_professor, ter, inicio, fim FROM horario_livro_ponto
            UNION ALL SELECT cpf_professor, qua, inicio, fim FROM horario_livro_ponto
            UNION ALL SELECT cpf_professor, qui, inicio, fim FROM horario_livro_ponto
            UNION ALL SELECT cpf_professor, sex, inicio, fim FROM horario_livro_ponto
            UNION ALL SELECT cpf_professor, sab, inicio, fim FROM horario_livro_ponto
            UNION ALL SELECT cpf_professor, dom, inicio, fim FROM horario_livro_ponto
        ) u
        WHERE u.v IS NOT NULL
            AND UPPER(u.v) NOT IN ('ATPC','SLN','REAN','PATN','INV')
        GROUP BY cpf
    ),
    mat_count AS (
      SELECT cpf, SUM(qtd) AS aulas_matriz
      FROM (
        SELECT m.cpf_professor AS cpf, COALESCE(SUM(m.qtd_aulas),0) AS qtd
        FROM matriz_curricular m
        JOIN turma t ON t.num_classe = m.num_classe
        WHERE t.ano = %s AND t.duracao IN {ph_d}
        GROUP BY m.cpf_professor
        UNION ALL
        SELECT m.cpf_professor_2 AS cpf, COALESCE(SUM(m.qtd_aulas),0) AS qtd
        FROM matriz_curricular m
        JOIN turma t ON t.num_classe = m.num_classe
        WHERE m.cpf_professor_2 IS NOT NULL
          AND t.ano = %s AND t.duracao IN {ph_d}
        GROUP BY m.cpf_professor_2
      ) x
      GROUP BY cpf
    )
    SELECT
      plp.instancia_calendario, plp.nome, IF(plp.di=0,'-',plp.di) AS di, plp.rg,
      IFNULL(plp.digito,'') AS digito, IFNULL(plp.rs,'-') AS rs, IFNULL(plp.pv,'') AS pv,
      plp.cpf, cargos_livro_ponto.descricao AS cargo,
      CONCAT(categoria_livro_ponto.letra, ' - ', categoria_livro_ponto.descricao) AS categoria,

      CASE WHEN plp.afastamento IS NULL THEN
         REPLACE(
           CONCAT('Atribuída(s) ',
                  IFNULL(lp_count.aulas_lp,0)+IFNULL(mat_count.aulas_matriz,0),
                  ' aula(s) nesta UE'),
           'Atribuída(s) 0 aula(s) nesta UE', 'Não Possui Aulas Atribuídas')
      ELSE CONCAT(afastamento_livro_ponto.prefixo, afastamento_livro_ponto.descricao)
      END AS situacao,

      IFNULL(plp.FNREF,'') AS FNREF, jornada_livro_ponto.descricao AS jornada,
      jornada_livro_ponto.qtd AS qtd_jornada,
      IFNULL(lp_count.aulas_lp,0) + IFNULL(mat_count.aulas_matriz,0) AS total_aulas,
      IFNULL(plp.afastamento,'') AS afastamento,
      IFNULL(disciplinas.descricao,'Não Possui') AS disciplina, IFNULL(plp.obs,'') AS obs,
      IFNULL(plp.aulas_outra_ue,0) AS aulas_outra_ue,
      CASE WHEN plp.atpc>0 OR plp.atpl>0 THEN CONCAT(' + ',plp.atpc,' ATPC(s) + ',plp.atpl,' ATPL(s)') ELSE '' END AS atpc,
      IFNULL(plp.atpc + plp.atpl,0) AS soma_atpc,
      plp.assina_livro,
      CONCAT(c.id,' - ',c.descricao) AS sede_c, CONCAT(f.id,' - ',f.descricao) AS sede_f
    FROM professor_livro_ponto plp
    JOIN sede_livro_ponto c ON c.id = plp.sede_classificacao
    JOIN sede_livro_ponto f ON f.id = plp.sede_controle_freq
    LEFT JOIN disciplinas ON disciplinas.codigo_disciplina = plp.disciplina
    JOIN cargos_livro_ponto ON cargos_livro_ponto.id = plp.cargo
    JOIN categoria_livro_ponto ON categoria_livro_ponto.id = plp.categoria
    LEFT JOIN afastamento_livro_ponto ON afastamento_livro_ponto.id = plp.afastamento
    JOIN jornada_livro_ponto ON jornada_livro_ponto.id = plp.jornada
    LEFT JOIN lp_count ON lp_count.cpf = plp.cpf
    LEFT JOIN mat_count ON mat_count.cpf = plp.cpf
    WHERE plp.ativo = 1
    {cond_ind}
    ORDER BY plp.rg
    """

    params_prof = [ano, *duracao_tuple, ano, *duracao_tuple] + params_ind
    professores = banco.executarConsulta(sql_prof, params_prof)


    # Lista de CPFs e instâncias (para pré-carregar tudo)
    cpfs = [int(p['cpf']) for p in professores]
    insts = list({int(p['instancia_calendario']) for p in professores}) or [1]

    # ----------------------------------------------------
    # 2) Pré-carregar aulas_outra_ue, licenças e eventos (1 consulta de cada)
    # ----------------------------------------------------
    if cpfs:
        ph_cpfs = ph(cpfs)
        sql_ue = f"""
            SELECT cpf_professor, semana, qtd
            FROM aulas_outra_ue_livro_ponto
            WHERE cpf_professor IN {ph_cpfs}
            """
        linhas_ue = banco.executarConsulta(sql_ue, [*cpfs])
    else:
        # nada a buscar
        linhas_ue = []

    mapa_ue = {}
    for r in linhas_ue:
        mapa_ue.setdefault(int(r['cpf_professor']), {})[r['semana']] = r['qtd']

    if cpfs:
        ph_cpfs = ph(cpfs)
        sql_lic = f"""
        SELECT l.cpf, l.inicio, l.fim, l.descricao,
                t.descricao AS desc_tipo, t.redline, t.exibicao
        FROM licenca_professores l
        JOIN tipo_licenca_professores t ON t.id = l.id_tipo
        WHERE l.cpf IN {ph_cpfs}
            AND NOT (l.fim < %s OR l.inicio > %s)
        """
        licencas_mes = banco.executarConsulta(sql_lic, [*cpfs, primeiro, ultimo])
    else:
        # sem CPFs, evita IN vazio
        sql_lic = """
        SELECT l.cpf, l.inicio, l.fim, l.descricao,
                t.descricao AS desc_tipo, t.redline, t.exibicao
        FROM licenca_professores l
        JOIN tipo_licenca_professores t ON t.id = l.id_tipo
        WHERE 1=0
        """
        licencas_mes = banco.executarConsulta(sql_lic)


    lic_map = {}
    for r in licencas_mes:
        lic_map.setdefault(int(r['cpf']), []).append(r)

    if insts:
        ph_insts = ph(insts)
        sql_evt = f"""
        SELECT e.instancia_calendario, e.data_inicial, e.data_final,
                cl.descricao AS cat, cl.qtd_letivo,
                e.descricao, e.evento
        FROM eventos_calendario e
        JOIN cat_letivo cl ON cl.id = e.evento
        WHERE e.instancia_calendario IN {ph_insts}
            AND NOT (e.data_final < %s OR e.data_inicial > %s)
        ORDER BY e.data_inicial
        """
        evts_mes = banco.executarConsulta(sql_evt, [*insts, primeiro, ultimo])
    else:
        evts_mes = []

    evt_map = {}
    for r in evts_mes:
        evt_map.setdefault(int(r['instancia_calendario']), []).append(r)

    # ----------------------------------------------------
    # 3) Processar cada professor (sem novas idas ao DB além da SP do quadro)
    # ----------------------------------------------------
    pos_inicial = 2278
    sumario = []
    cont_pag = 1

    for professor in professores:
        sumario.append({'professor': professor['nome'], 'pag': cont_pag})
        cont_pag += 1

        professor['pos'] = pos_inicial
        pos_inicial += 1124

        # Formatações (RG/RS/CPF) — como no seu código
        aux_rg = '%08d' % int(professor['rg'])
        professor['rg'] = aux_rg[0:2] + "." + aux_rg[2:5] + "." + aux_rg[5:]
        if professor['digito'] != '':
            professor['rg'] += "-" + professor['digito']

        aux_rs = '%08d' % int(professor['rs']) if str(professor['rs']).isdigit() else '00000000'
        professor['rs'] = aux_rs[0:2] + "." + aux_rs[2:5] + "." + aux_rs[5:]
        if professor['pv'] != '':
            professor['rs'] += " / " + '%02d' % int(professor['pv'])

        aux = '%011d' % int(professor['cpf'])
        professor['cpf'] = aux[:3] + "." + aux[3:6] + "." + aux[6:9] + "-" + aux[9:]
        cpf_int = int(aux.replace('.', '').replace('-', ''))

        # textos padrão
        professor['txt_carga'] = 'Carga Horária:'
        professor['txt_sit'] = 'Afast.:'
        professor['class_afast'] = ''
        professor['carga'] = ''

        if professor['afastamento'] == '':
            professor['txt_sit'] = 'Qtd. Aulas:'
            if professor['total_aulas'] > 0:
                professor['carga'] = f"{professor['total_aulas']} aula(s) nesta UE."
        else:
            professor['class_afast'] = 'red'

        # Jornada / carga suplementar (mesma regra)
        if professor['jornada'] != '-':
            professor['txt_carga'] = "Carga Suplementar:"
            if professor['afastamento'] == '':
                total = int(professor['total_aulas']) + int(professor['aulas_outra_ue'])
                resto = total - professor['qtd_jornada']
                professor['jornada'] = f"{professor['jornada']} - {professor['qtd_jornada']} aulas"
                if int(professor['sede_c'][:5]) != int(ua_padrao):
                    professor['carga'] = "Sede em outra UE"
                else:
                    professor['carga'] = f"{resto} aula(s)" if resto > 0 else "Não Possui"
        else:
            professor['jornada'] = 'Não Possui'


        # -------- quadro de carga -------------
        quadro = []
        if int(professor['sede_c'][:5]) == int(ua_padrao):
            # quadro estará visível somente para professores com sede aqui
            if professor['afastamento'] == '': # quadro estará visível somente para professores que não estão designados ou afastados
                if professor['total_aulas'] > 0: # quadro estará visível apenas para quem tiver aula
                    if professor['jornada'] != 'Não Possui': # para os professores que tem jornada
                        quadro.append({'col1':'<b>RESUMO (horas)</b>', 'col2':'Semanal', 'col3':'Mensal'})
                        horas_jornada = int(round((professor['qtd_jornada'] + professor['soma_atpc']) * 50 / 60, 0))
                        quadro.append({'col1':'JORNADA', 'col2':horas_jornada, 'col3':horas_jornada * 5})
                        horas_suplementar = int(round((int(professor['total_aulas']) + int(professor['aulas_outra_ue']) - professor['qtd_jornada']) * 50 / 60, 0))
                        quadro.append({'col1':'CARGA SUPLEMENTAR', 'col2':horas_suplementar, 'col3':horas_suplementar * 5})
                        quadro.append({'col1':'TOTAL', 'col2':horas_jornada + horas_suplementar, 'col3':horas_jornada * 5 + horas_suplementar * 5})
                    else: # para quem não tem jornada
                        quadro.append({'col1':'<b>RESUMO (horas)</b>', 'col2':'Semanal', 'col3':'Mensal'})
                        quadro.append({'col1':'NÃO POSSUI JORNADA', 'col2':'-', 'col3':'-'})
                        horas_carga = int(round((professor['total_aulas'] + professor['aulas_outra_ue'] + professor['soma_atpc']) * 50 / 60, 0))
                        quadro.append({'col1':'CARGA HORÁRIA', 'col2':horas_carga, 'col3':horas_carga * 5})
                        quadro.append({'col1':'TOTAL', 'col2':horas_carga, 'col3':horas_carga * 5})
                        
                        
        professor['quadro'] = quadro        

        # -------- quadro lateral (horário) via SP unificada --------
        if professor['assina_livro'] == 1:
            professor['quadro_aula'] = banco.executarConsulta(
                "CALL sp_horario_professor_v2(%s, %s, %s, %s)",
                (cpf_int, data_aux.strftime("%Y-%m-%d"), 'apelido', 1)
            )

            print("CALL sp_horario_professor_v2(%s, %s, %s, %s)", (cpf_int, data_aux.strftime("%Y-%m-%d"), 'apelido', 1))

        else:
            professor['quadro_aula'] = []

        # -------- contagem semanal (sem SQL) --------
        if professor['assina_livro'] == 0:
            qtd_semanais = {k: 0 for k in SEMANA_SIGLAS}
        elif professor['afastamento'] in ('292', '411'):
            qtd_semanais = {'seg':9, 'ter':9, 'qua':9, 'qui':9, 'sex':9, 'sáb':0, 'dom':0}
        else:
            qtd_semanais = contar_quadro_semanais(professor['quadro_aula'])
        professor['qtd_aulas_semanais'] = qtd_semanais

        # -------- aulas em outras UEs (pré-carregado) --------
        professor['aulas_ue'] = mapa_ue.get(cpf_int, {})

        # -------- total_geral (UE local + outras UEs) --------
        total_aulas_geral = {}
        for dia in SEMANA_SIGLAS:
            outras = int(professor['aulas_ue'].get(dia, 0) or 0)
            local = int(qtd_semanais.get(dia, 0) or 0)
            total = outras + local
            total_aulas_geral[dia] = '' if total < 1 else total
        professor['total_geral'] = total_aulas_geral

        # -------- dias do mês (sem SQL por dia) --------
        qtd_dias = calendar.monthrange(ano, mes)[1]
        professor['extra_red'] = ''
        cont_deixou = 0
        top_deixou = 303
        height_deixou = 0
        dias = []

        for i in range(1, qtd_dias + 1):
            d = date(ano, mes, i)
            idx = d.weekday()  # 0=seg ... 6=dom
            semana_sigla = SEMANA_SIGLAS[idx]

            lic = licenca_do_dia(lic_map, cpf_int, d)
            if lic:
                if lic['redline'] == 1:
                    if cont_deixou == 0:
                        top_deixou += ((i - 1) * 16)
                        cont_deixou = 1
                    else:
                        cont_deixou += 1
                        height_deixou = cont_deixou * 16
                        professor['extra_red'] = '<div class="red-line-extra-min" style="top: %spx; height: %spx"></div>' % (top_deixou, height_deixou)
                dias.append({
                    'dia': f'{i:02d}',
                    'Assinatura': (lic['desc_tipo'] or '').replace('Sem vínculo', ''),
                    'semana': semana_sigla,
                    'class-bg': 'gray',
                    'class-txt': 'black',
                    'evento': 11
                })
                continue

            ev = evento_do_dia(evt_map, professor['instancia_calendario'], d)
            if idx < 5:  # seg-sex
                if ev:
                    if ev['evento'] == 11:
                        professor['extra_red'] = f'<div class="red-line-extra" style="height: {i * 16}px"></div>'
                    elif ev['evento'] == 12:
                        if cont_deixou == 0:
                            top_deixou += ((i - 1) * 16)
                            cont_deixou = 1
                        else:
                            cont_deixou += 1
                            height_deixou = cont_deixou * 16
                            professor['extra_red'] = '<div class="red-line-extra-min" style="top: %spx; height: %spx"></div>' % (top_deixou, height_deixou)

                    desc = ev['cat'] or ''
                    if ev['qtd_letivo'] < 1 and (ev['evento'] < 7 or ev['evento'] > 9):
                        dias.append({'dia': f'{i:02d}', 'Assinatura': desc.replace("Sem vínculo", '').replace('Deixou de ministrar aulas nesta U.E.', ''),
                                     'semana': semana_sigla, 'class-bg': 'gray', 'class-txt': 'black', 'evento': ev['evento']})
                    else:
                        dias.append({'dia': f'{i:02d}', 'Assinatura': '', 'semana': semana_sigla,
                                     'class-bg': '', 'class-txt': 'black', 'evento': ev['evento']})
                else:
                    dias.append({'dia': f'{i:02d}', 'Assinatura': '', 'semana': semana_sigla,
                                 'class-bg': '', 'class-txt': 'black', 'evento': 0})
            else:  # sáb/dom
                if ev:
                    if ev['evento'] == 11:
                        professor['extra_red'] = f'<div class="red-line-extra" style="height: {i * 16}px"></div>'
                    elif ev['evento'] == 12:
                        if cont_deixou == 0:
                            top_deixou += ((i - 1) * 16)
                            cont_deixou = 1
                        else:
                            height_deixou = cont_deixou * 16
                            professor['extra_red'] = '<div class="red-line-extra-min" style="top: %spx; height: %spx"></div>' % (top_deixou, height_deixou)
                            cont_deixou += 1
                    desc = ev['descricao'] or ev['cat'] or ''
                    if ev['qtd_letivo'] > 0:
                        dias.append({'dia': f'{i:02d}', 'Assinatura': '', 'semana': semana_sigla,
                                     'class-bg': '', 'class-txt': 'red', 'evento': ev['evento']})
                    else:
                        dias.append({'dia': f'{i:02d}', 'Assinatura': desc.replace("Sem vínculo", '').replace('Deixou de ministrar aulas nesta U.E.', ''),
                                     'semana': semana_sigla, 'class-bg': 'gray', 'class-txt': 'red', 'evento': ev['evento']})
                else:
                    dias.append({'dia': f'{i:02d}', 'Assinatura': d.strftime("%A").title(),
                                 'semana': semana_sigla, 'class-bg': 'gray', 'class-txt': 'red', 'evento': 0})

        professor['dias'] = dias
        # mantém suas variáveis auxiliares (usadas no template)
        linhas = 5 + (30 - len(dias))

        # -------- observações (eventos/obs/licenças) --------
        licencas_txt = []
        for l in lic_map.get(cpf_int, []):
            licencas_txt.append( (render_exibicao(l['exibicao'], l['inicio'], l['fim']) + ' ' + (l['descricao'] or '')).strip() )

        # monta lista final como você fazia
        lst_final_eventos = []
        if professor['assina_livro'] == 0:
            lst_final_eventos.append("NÃO ASSINA ESTE LIVRO PONTO")

        if professor['obs']:
            lst_final_eventos.append(professor['obs'])

        lst_final_eventos.extend(licencas_txt)

        txt_eventos = ''
        for ev in evt_map.get(int(professor['instancia_calendario']), []):
            desc = ev['descricao'] or ev['cat'] or ''
            if ev['evento'] == 12:
                if txt_eventos:
                    lst_final_eventos.append(txt_eventos[:-2]); txt_eventos = ''
                txt_eventos += f"A partir de {ev['data_inicial'].strftime('%d')}: {desc}, "
            else:
                if ev['data_inicial'] == ev['data_final']:
                    txt_eventos += f"Dia {ev['data_inicial'].strftime('%d')}: {desc}, "
                else:
                    txt_eventos += f"De {ev['data_inicial'].strftime('%d/%m')} até {ev['data_final'].strftime('%d/%m/%Y')}: {desc}, "
            if len(txt_eventos) > 100:
                lst_final_eventos.append(txt_eventos[:-2]); txt_eventos = ''
        if txt_eventos:
            lst_final_eventos.append(txt_eventos[:-2])

        professor['eventos'] = lst_final_eventos

    # ----------------------------------------------------
    # 4) Assinaturas (ok manter como está)
    # ----------------------------------------------------
    info_assinatura = banco.executarConsulta(
        "SELECT "
        "(SELECT valor FROM config WHERE id_config = 'diretor_ponto') AS diretor, "
        "(SELECT valor FROM config WHERE id_config = 'rg_diretor_ponto') AS rg_diretor, "
        "(SELECT valor FROM config WHERE id_config = 'secretario_ponto') AS secretario, "
        "(SELECT valor FROM config WHERE id_config = 'rg_secretario_ponto') AS rg_secretario, "
        "(SELECT valor FROM config WHERE id_config = 'cargo_secretario_ponto') AS cargo_secretario"
    )[0]

    # sumário
    sumario.sort(key=lambda t: (locale.strxfrm(t['professor'])))

    # dias_semana para o template
    dias_semana = SEMANA_SIGLAS

    # Atenção: o template usa 'dias' e 'linhas' "globais"; passamos do último professor,
    # assim como seu código original fazia.
    return render_template(
        'render_pdf/render_livro_ponto.jinja',
        professores=professores,
        data=f'{getMes(mes)} / {ano}',
        dias=dias,
        eventos=lst_final_eventos,
        linhas=linhas,
        info_assinatura=info_assinatura,
        dias_semana=dias_semana,
        sumario=sumario,
        folha_extra=folha_extra
    )

@app.route('/render_etiquetas_alunos',  methods=['GET', 'POST'])
def render_etiquetas_alunos():

    if request.method == 'GET':
        #try:
        classe = request.args.getlist('classe')[0]

        turma = banco.executarConsultaVetor(f"select nome_turma from turma where num_classe = {classe}")[0]
        alunos = banco.executarConsulta(f"select distinct aluno.nome from vinculo_alunos_turmas inner join aluno on aluno.ra = vinculo_alunos_turmas.ra_aluno where num_classe = {classe} and situacao = 1 order by nome")

        for aluno in alunos:
            aluno['nome'] = aluno['nome'].title().replace('Da ', 'da ').replace("De ", "de ").replace("Do ", 'do ').replace("Dos ", 'dos ')

        return render_template('render_pdf/render_etiqueta_aluno.jinja', turma=turma, alunos=alunos)

        #except:
            #return redirect('/')




@app.route('/render_certificados_conclusao',  methods=['GET', 'POST'])
def render_certificados_conclusao():
    if request.method == 'GET':
        classe = request.args.getlist('classe')[0]

        tipo_ensino = banco.executarConsulta('select tipo_ensino from turma where num_classe = %s' % classe)[0]['tipo_ensino']

        nome_vice = banco.executarConsultaVetor('select valor from config where id_config = "vice-regular-nome"')[0]
        rg_vice = banco.executarConsultaVetor('select valor from config where id_config = "vice-regular-rg"')[0]  


        if tipo_ensino == 1:
            modalidade = "Ensino Fundamental"
        else:
            modalidade = 'Ensino Médio'

        alunos = banco.executarConsulta(r"select aluno.nome, aluno.rg, serie, aluno.sexo, DATE_FORMAT (aluno.nascimento,'%d/%m/%Y') as nascimento, DATE_FORMAT (vinculo_alunos_turmas.fim_mat,'%d/%m/%Y') as fim from vinculo_alunos_turmas  inner join aluno on aluno.ra = vinculo_alunos_turmas.ra_aluno where num_classe = " + classe + " and situacao in (6) and serie in (3, 4, 9) order by nome")

        print(r"select aluno.nome, aluno.rg, serie, aluno.sexo, DATE_FORMAT (aluno.nascimento,'%d/%m/%Y') as nascimento, DATE_FORMAT (vinculo_alunos_turmas.fim_mat,'%d/%m/%Y') as fim from vinculo_alunos_turmas  inner join aluno on aluno.ra = vinculo_alunos_turmas.ra_aluno where num_classe = " + classe + " and situacao in (6) and serie in (3, 4, 9) order by nome")

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

        if request.args.getlist('num_classe'):
            num_classe = 'and num_classe = %s' % request.args.getlist('num_classe')[0]
        else:
            num_classe = ''

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
              "where turma.ano = %s %s %s order by tipo_ensino, nome_turma" % (ano, final, num_classe)
        
        turmas = banco.executarConsulta(sql)

        datas_limites = banco.executarConsulta('select %sbim_inicio as inicio, %sbim_fim as fim from calendario where ano = %s' % (bimestre, bimestre, ano))

        inicio = str(datas_limites[0]['inicio'])
        fim = str(datas_limites[0]['fim'])

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
            disciplinas = banco.executarConsulta('select professor.nome_ata, disciplina, disciplinas.abv as desc_disc, disciplinas.descricao as completo, aulas_dadas, matriz_curricular.tipo from vinculo_prof_disc inner join professor on professor.rg = vinculo_prof_disc.cpf_prof inner join disciplinas ON disciplinas.codigo_disciplina = vinculo_prof_disc.disciplina left join matriz_curricular on matriz_curricular.disc_disciplina = vinculo_prof_disc.disciplina and matriz_curricular.num_classe = vinculo_prof_disc.num_classe where bimestre = %s and vinculo_prof_disc.num_classe = %s order by tipo, disciplina' % (bimestre, turma['num_classe']))

            if len(disciplinas) > 15:
                turma['folha_extra'] = True
                turma['qtd_folha_1'] = sum(1 for item in disciplinas if item.get("tipo") in (1, 3))
                turma['qtd_folha_2'] = len(disciplinas) - turma['qtd_folha_1']
            else:
                turma['folha_extra'] = False
                turma['qtd_folha_1'] = len(disciplinas)
                turma['qtd_folha_2'] = 0

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

            if turma['folha_extra']:
                turma['top_extra'] = top
                top += limite

            turma['top_verso'] = top
            top += limite

            if not turma['folha_extra']:
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

                        item['conceito_final'] = {}

                        sql = 'SELECT vinculo_alunos_turmas.ra_aluno, vinculo_alunos_turmas.num_chamada as num, media '
                        sql += 'from conceito_final '
                        sql += 'inner join vinculo_alunos_turmas on vinculo_alunos_turmas.ra_aluno = conceito_final.ra_aluno and vinculo_alunos_turmas.num_classe = conceito_final.num_classe '
                        sql += 'where conceito_final.disciplina = %s and conceito_final.num_classe = %s order by num_chamada' % (item['disciplina'], turma['num_classe'])
                        
                        notas = banco.executarConsulta(sql)

                        for aluno in notas:
                            item['conceito_final'][aluno['ra_aluno']] = aluno


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

        disciplinas = banco.executarConsulta('select professor.nome_ata, disciplina, disciplinas.abv as desc_disc, disciplinas.descricao as completo, aulas_dadas from vinculo_prof_disc inner join professor on professor.rg = vinculo_prof_disc.cpf_prof inner join disciplinas ON disciplinas.codigo_disciplina = vinculo_prof_disc.disciplina  where bimestre = %s and num_classe = %s order by disciplina' % (bimestre, num_classe))

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

@app.route('/confirmar_senha', methods=['GET', 'POST'])
def confirmar_senha():

    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            senha_sha256 = encriptar(data['senha'])
            
            result = banco.executarConsultaVetor("select id_config from config where valor = '%s'" % (senha_sha256))
            
            if len(result) > 0:
                return jsonify({'status':True})
            else:
                return jsonify({'status':False})

@app.route('/atualizar_professor_matriz', methods=['GET', 'POST'])
def atualizar_professor_matriz():

    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            
            sql = 'update matriz_curricular set %s = %s where num_classe = %s and disc_disciplina = %s ' % (data['coluna'], data['cpf'], data['num_classe'], data['disc'])
            if banco.executeBasicSQL(sql):
                return jsonify({'status':True})
            else:
                return jsonify({'status':False})


@app.route('/render_lista', methods=['GET', 'POST'])
def render_lista():

    if request.method == 'GET':
        tipo = request.args.getlist('tipo')[0]
        num_classe = request.args.getlist('num_classe')[0]
        order = request.args.getlist('order')[0]

        if tipo == 'chamada':

            nome_escola = banco.executarConsultaVetor("select descricao from sede_livro_ponto where id = (select valor from config where id_config = 'ua_sede')")[0]

            dados = banco.executarConsulta(f'select ano, nome_turma from turma where num_classe = {num_classe}')[0]
            mes = request.args.getlist('mes')[0]
            cor = request.args.getlist('cor')[0]

            alunos = banco.executarConsulta(f'select num_chamada, aluno.nome from vinculo_alunos_turmas inner join aluno on aluno.ra = vinculo_alunos_turmas.ra_aluno where num_classe = {num_classe} and situacao = 1 order by nome')

            limite = 5

            if len(alunos) < 21:
                limite = 10

            for aluno in alunos:
                aluno['nome'] = aluno['nome'].title().replace('Da ', 'da ').replace("De ", "de ").replace("Do ", 'do ').replace("Dos ", 'dos ')

            colours_list = ['green', 'yellow', 'blue', 'orange']
            pointer_color = 0

            dias_uteis = []
            for dia in range(1, calendar.monthrange(dados['ano'], int(mes))[1] + 1):
                data = datetime(dados['ano'], int(mes), dia)
                if data.weekday() < 5:  # Segunda (0) a Sexta (4)
                    border = 'normal'
                    if data.weekday() == 4:
                        border = 'strong'

                    # verificar se é feriado
                    qtd_letivo = banco.executarConsulta(f"select cat_letivo.qtd_letivo from eventos_calendario inner join cat_letivo on cat_letivo.id = eventos_calendario.evento where instancia_calendario = 1 and '{dados['ano']}-{mes}-{dia}' between data_inicial and data_final")

                    if len(qtd_letivo) > 0:
                        qtd_letivo = qtd_letivo[0]['qtd_letivo']
                    else:
                        qtd_letivo = 1

                    dias_uteis.append((dia, data.strftime("%A")[0:3], border, colours_list[pointer_color], qtd_letivo))

                    if data.weekday() == 4:
                        pointer_color += 1
                        if pointer_color > 3:
                            pointer_color = 0

            return render_template('render_pdf/render_chamada.jinja', dados=dados, mes=mes, desc_mes = getMes(mes), alunos=alunos, dias_uteis=dias_uteis, limite=limite, cor=cor, nome_escola=nome_escola)
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

            tamanho_lista = 50
            if tamanho_lista < len(alunos):
                tamanho_lista = len(alunos)

            print(tamanho_lista)

            return render_template('render_pdf/render_lista.jinja', head=head, total=total, desc_total=desc_total, alunos=alunos, tamanho_lista=tamanho_lista)
        
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
            colunas = request.args.getlist('colunas')[0].split(';')

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

            return render_template('render_pdf/render_lista_assinatura.jinja', titulo=titulo, alunos=alunos, escola=escola.upper(), nome_turma=nome_turma, colunas=colunas)

        elif tipo == 'declaracao':
            global aux_info

            # definir cabeçalho
            nome_escola = banco.executarConsultaVetor("select descricao from sede_livro_ponto where id = (select valor from config where id_config = 'ua_sede')")[0]
            nome_escola = nome_escola.upper()
            endereco_escola = banco.executarConsultaVetor("select valor from config where id_config = 'endereco_sede'")[0]
            cidade_escola = banco.executarConsultaVetor("select valor from config where id_config = 'cidade_sede'")[0]

            distancia = "100px"

            #print(aux_info)

            if aux_info['assinatura'] != '0':
                decl_assinatura = banco.executarConsulta("select nome, rg, CASE WHEN digito IS NULL THEN '' ELSE CONCAT('-', digito) END AS digito, cargos_livro_ponto.descricao as cargo from funcionario_livro_ponto inner join cargos_livro_ponto on cargos_livro_ponto.id = funcionario_livro_ponto.cargo where cpf = %s" % aux_info['assinatura'])[0]
                rg = "%08d" % int(decl_assinatura['rg'])
                decl_assinatura['rg'] = 'RG: %s.%s.%s%s' % (rg[:2], rg[2:5], rg[5:8], decl_assinatura['digito'])
            else:
                decl_assinatura = False
            
            pronome = 'o'
            if aux_info['genero'] == 'f':
                pronome = 'a'

            pronome_e = 'e'
            if aux_info['genero'] == 'f':
                pronome_e = 'a'

            if (aux_info['rg'] in ('', '-', 'None') or aux_info['rg'] is None):
                texto = 'Declaro para os devidos fins que <b>' + aux_info['nome'] + '</b>, RA: ' + aux_info['ra']
            elif (aux_info['rg'] == 'CIN'):
                texto = 'Declaro para os devidos fins que <b>' + aux_info['nome'] + '</b>, CIN: ' + aux_info['cpf']
            else:
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

            elif aux_info['tipo'] == 3: # declaração de matrícula padrão sem frequência

                match (aux_info['info_classe']['tipo_ensino']):
                    case 1:
                        serie = "no <b>%sº ano do %s</b>" % (aux_info['info_classe']['serie'], aux_info['info_classe']['tipo_ensino_desc'])
                    case 3:
                        serie = "na <b>%sª série do %s</b>" % (aux_info['info_classe']['serie'], aux_info['info_classe']['tipo_ensino_desc'])
                        


                titulo = 'DECLARAÇÃO DE MATRÍCULA'
                texto += ' é alun%s regularmente matriculad%s %s.' % (pronome, pronome, serie)

            elif aux_info['tipo'] == 4: # declaração de matrícula padrão com frequência

                match (aux_info['info_classe']['tipo_ensino']):
                    case 1:
                        serie = "no <b>%sº ano do %s,</b>" % (aux_info['info_classe']['serie'], aux_info['info_classe']['tipo_ensino_desc'])
                    case 3:
                        serie = "na <b>%sª série do %s,</b>" % (aux_info['info_classe']['serie'], aux_info['info_classe']['tipo_ensino_desc'])
                        


                titulo = 'DECLARAÇÃO DE MATRÍCULA'
                if aux_info['bimestre'] > 0:
                    texto += ' é alun%s regularmente matriculad%s %s com frequência de <b>%s%s</b> registrada até o final do <b>%sº bimestre.</b>' % (pronome, pronome, serie, aux_info['percent'], r'%', aux_info['bimestre'])
                else:
                    list_serie = list(serie)
                    list_serie[-5] = '.'
                    texto += ' é alun%s regularmente matriculad%s %s' % (pronome, pronome, "".join(list_serie))

            elif aux_info['tipo'] == 5: # declaração de desistência de vaga para ensino profissionalizante para menor de idade
                titulo = 'DECLARAÇÃO DE DESISTÊNCIA – Ensino Profissionalizante'

                match (aux_info['info_classe']['tipo_ensino']):
                    case 1:
                        serie = "no <b>%sº ano do %s,</b>" % (aux_info['info_classe']['serie'], aux_info['info_classe']['tipo_ensino_desc'])
                    case 3:
                        serie = "na <b>%sª série do %s,</b>" % (aux_info['info_classe']['serie'], aux_info['info_classe']['tipo_ensino_desc'])

                texto = f"Eu, <b>{aux_info['nome_resp']}</b>, RG: {aux_info['rg_resp']}, responsável pel{pronome} estudante <b>{aux_info['nome']}</b>, RA: {aux_info['ra']}, matriculad{pronome} {serie} declaro estar <b>desistindo</b> da matrícula na classe com Itinerário Formativo Profissionalizante, ciente de que <b>não haverá a possibilidade de retorno futuro</b> a essa modalidade de atendimento e que {pronome} estudante será atendid{pronome} em classe com Itinerário Formativo propedêutico. "
                decl_assinatura = {'nome':'Assinatura do responsável'}

            elif aux_info['tipo'] == 6: # declaração de desistência de vaga para ensino profissionalizante para maior de idade
                titulo = 'DECLARAÇÃO DE DESISTÊNCIA – Ensino Profissionalizante'
                match (aux_info['info_classe']['tipo_ensino']):
                    case 1:
                        serie = "no <b>%sº ano do %s,</b>" % (aux_info['info_classe']['serie'], aux_info['info_classe']['tipo_ensino_desc'])
                    case 3:
                        serie = "na <b>%sª série do %s,</b>" % (aux_info['info_classe']['serie'], aux_info['info_classe']['tipo_ensino_desc'])

                texto = f"Eu, <b>{aux_info['nome']}</b>, RA: {aux_info['ra']}, maior de idade, matriculad{pronome} {serie} declaro estar <b>desistindo</b> da matrícula na classe com Itinerário Formativo Profissionalizante, ciente de que <b>não haverá a possibilidade de retorno futuro</b> a essa modalidade de atendimento e que serei atendid{pronome} em classe com Itinerário Formativo propedêutico. "
                decl_assinatura = {'nome':'Assinatura do responsável'}                

            elif aux_info['tipo'] == 7: # solicitação de baixa por transferência

                distancia = "40px"

                titulo = 'SOLICITAÇÃO – Baixa de Transferência'

                match (aux_info['info_classe']['tipo_ensino']):
                    case 1:
                        serie = "no <b>%sº ano do %s,</b>" % (aux_info['info_classe']['serie'], aux_info['info_classe']['tipo_ensino_desc'])
                    case 3:
                        serie = "na <b>%sª série do %s,</b>" % (aux_info['info_classe']['serie'], aux_info['info_classe']['tipo_ensino_desc'])


                texto = f"Eu, <b>{aux_info['nome_resp']}</b>, RG: {aux_info['rg_resp']}, responsável pel{pronome} estudante <b>{aux_info['nome']}</b>, RA: {aux_info['ra']}, matriculad{pronome} {serie} solicito que seja lançado o registro de <b>Baixa de Transferência</b> na sua matrícula atual, que será inativada."
                texto += '<br><br>Motivo da solicitação:<br>'
                texto += '(&nbsp;&nbsp;) mudança para outro estado/país (Qual?_______________________)<br>'
                texto += '(&nbsp;&nbsp;) mudança para escola da rede privada de ensino<br><br>'
                texto += f"Declaro estar ciente de que devo providenciar imediatamente matrícula para est{pronome_e} estudante, conforme legislação vigente. Para nova matrícula, na rede pública de ensino do Estado de São Paulo, deverei realizar inscrição solicitando o atendimento."
                decl_assinatura = {'nome':'Assinatura do responsável'}

            elif aux_info['tipo'] == 8: # solicitação de baixa por transferência

                distancia = "40px"

                titulo = 'SOLICITAÇÃO – Baixa de Transferência'

                match (aux_info['info_classe']['tipo_ensino']):
                    case 1:
                        serie = "no <b>%sº ano do %s,</b>" % (aux_info['info_classe']['serie'], aux_info['info_classe']['tipo_ensino_desc'])
                    case 3:
                        serie = "na <b>%sª série do %s,</b>" % (aux_info['info_classe']['serie'], aux_info['info_classe']['tipo_ensino_desc'])

                texto = f"Eu, <b>{aux_info['nome']}</b>, RA: {aux_info['ra']}, maior de idade, matriculad{pronome} {serie} solicito que seja lançado o registro de <b>Baixa de Transferência</b> na minha matrícula atual, que será inativada."
                texto += '<br><br>Motivo da solicitação:<br>'
                texto += '(&nbsp;&nbsp;) mudança para outro estado/país (Qual?_______________________)<br>'
                texto += '(&nbsp;&nbsp;) mudança para escola da rede privada de ensino<br><br>'
                texto += f"Declaro estar ciente que, para nova matrícula na rede pública de ensino do Estado de São Paulo, deverei realizar inscrição solicitando o atendimento."
                decl_assinatura = {'nome':'Assinatura do responsável'}    

            elif aux_info['tipo'] == 9: # declaração de matrícula com horário

                titulo = 'DECLARAÇÃO DE MATRÍCULA'

                match (aux_info['info_classe']['tipo_ensino']):
                    case 1:
                        serie = "no <b>%sº ano do %s,</b>" % (aux_info['info_classe']['serie'], aux_info['info_classe']['tipo_ensino_desc'])
                    case 3:
                        serie = "na <b>%sª série do %s,</b>" % (aux_info['info_classe']['serie'], aux_info['info_classe']['tipo_ensino_desc'])

                if aux_info['bimestre'] > 0:
                    texto += ' é alun%s regularmente matriculad%s %s com frequência de <b>%s%s</b> registrada até o final do <b>%sº bimestre.</b>' % (pronome, pronome, serie, aux_info['percent'], r'%', aux_info['bimestre'])
                else:
                    list_serie = list(serie)
                    list_serie[-5] = '.'
                    texto += ' é alun%s regularmente matriculad%s %s' % (pronome, pronome, "".join(list_serie))

                texto += "<br><br><b>Período:</b> %s" % aux_info['info_classe']['periodo']
                texto += '<br><b>Horário de aula:</b> %s às %s' % (aux_info['info_classe']['inicio'], aux_info['info_classe']['fim'])

            elif aux_info['tipo'] == 10: # declaração de conclusão de curso
                
                titulo = 'DECLARAÇÃO DE ESCOLARIDADE'

                match (aux_info['info_classe']['tipo_ensino']):
                    case 1:
                        serie = "no <b>%sº ano do %s,</b>" % (aux_info['info_classe']['serie'], aux_info['info_classe']['tipo_ensino_desc'])
                    case 3:
                        serie = "na <b>%sª série do %s,</b>" % (aux_info['info_classe']['serie'], aux_info['info_classe']['tipo_ensino_desc'])

                texto += f''' foi alun{pronome} regularmente matriculad{pronome} {serie} no ano letivo de {aux_info['info_classe']['ano']}, tendo sido considerad{pronome} <b>APROVAD{pronome.upper()}.</b>'''

            elif aux_info['tipo'] == 11: # declaração de transferência

                titulo = 'DECLARAÇÃO DE TRANSFERÊNCIA'

                match (aux_info['info_classe']['tipo_ensino']):
                    case 1:
                        serie = "no <b>%sº ano do %s.</b>" % (aux_info['info_classe']['serie'], aux_info['info_classe']['tipo_ensino_desc'])
                    case 3:
                        serie = "na <b>%sª série do %s.</b>" % (aux_info['info_classe']['serie'], aux_info['info_classe']['tipo_ensino_desc'])

                texto += f' solicitou transferência com direito a matricular-se {serie}'

            data_atual = datetime.now()
            data_formatada = data_atual.strftime("%d de %B de %Y")


            return render_template('render_pdf/render_declaracao.jinja', texto=texto, titulo=titulo, data=data_formatada, cor=num_classe, anos=aux_info['anos'], pronome=pronome, assinatura=decl_assinatura, distancia=distancia, nome_escola=nome_escola, endereco_escola=endereco_escola, cidade_escola=cidade_escola)
        
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

            return render_template('render_pdf/render_ata_final.jinja', info=info, dados=ls_final, ls_keys=ls_keys)
        
        elif tipo == 'grade':

            destino = tipo

            tipo_ensino = request.args.getlist('num_classe')[0]
            ano = request.args.getlist('order')[0]
            data_horario = request.args.getlist('data')[0]

            rows = banco.executarConsulta(f'''
                                                SELECT
                                                    t.num_classe,
                                                    COALESCE(t.apelido, t.nome_turma) AS turma,
                                                    gh.semana,
                                                    gh.inicio,
                                                    gh.fim,
                                                    gh.disc_abv,
                                                    gh.label,
                                                    gh.prof_key,
                                                    gh.prof_nome
                                                FROM grade_horario_vw gh
                                                JOIN turma t ON t.num_classe = gh.num_classe
                                                WHERE t.num_classe IN (select num_classe from turma where tipo_ensino in {tipo_ensino} and ano = {ano})
                                                ORDER BY turma, gh.semana, gh.inicio;''')

    
            data = montar_eventos(rows)
            turmas = sorted({r['turma'] for r in rows})

            axis = data['axis']
            axis_height = (axis['end'] - axis['start']) * axis['px_per_min']
            tick_step = 30  # minutos (troque para 15 se preferir)

            ticks = [
                {
                'y': (m - axis['start']) * axis['px_per_min'],
                'label': f'{m//60:02d}:{m%60:02d}'
                }
                for m in range(axis['start'], axis['end'] + 1, tick_step)
            ]  

            tipo_ensino_desc = banco.executarConsulta("select GROUP_CONCAT(descricao SEPARATOR ' + ') AS texto from tipo_ensino where id in %s" % tipo_ensino)[0]['texto']

            return render_template('render_pdf/render_horario_geral_new.jinja', axis=axis, timeline=data['timeline'], turmas=turmas, axis_height=axis_height, ticks=ticks, tipo_ensino=tipo_ensino_desc, data_horario=data_horario)
            
            #horario = banco.executarConsulta(f'''select distinct inicio, fim, concat(TIME_FORMAT(inicio, "%H:%i"), ' - ',  TIME_FORMAT(fim, "%H:%i")) as horario from hora_aulas where tipo_ensino in {tipo_ensino} and ano = {ano} order by inicio''')
            
            #if len(turmas) == 0:
                #ano = data_horario.split('/')[2]
                #calendario = banco.executarConsulta(f'''select DATE_FORMAT(1bim_inicio, '%d/%m/%Y') as inicio_1_sem, DATE_FORMAT(2bim_fim, '%d/%m/%Y') as fim_1_sem, DATE_FORMAT(3bim_inicio, '%d/%m/%Y') as inicio_2_sem, DATE_FORMAT(4bim_fim, '%d/%m/%Y') as fim_2_sem from calendario where ano = {ano}''')[0]
                #msg = f'''<p style="font-size:30px;line-height: 40px;">
                            #<b>Atenção!</b>
                            #A data escolhida não abrange nenhuma turma. Escolha uma data que esteja entre o início e o fim do bimestre.
                        #</p>
                        #<p style="font-size:30px;line-height: 40px;">
                            #Lembre-se que entre o primeiro e o segundo semestres existe um período de férias/recesso.
                        #</p>
                        #<p style="font-size:30px;line-height: 40px;">
                            #<b>Calendário Escolar de {ano}: </b>
                            #<ul>
                                #<li style="font-size:30px;margin-bottom:10px;">Início do 1º Semestre: <b>{calendario['inicio_1_sem']}</b></li>
                                #<li style="font-size:30px;margin-bottom:20px;">Fim do 1º Semestre: <b>{calendario['fim_1_sem']}</b></li>
                                #<li style="font-size:30px;margin-bottom:10px;">Início do 2º Semestre: <b>{calendario['inicio_2_sem']}</b></li>
                                #<li style="font-size:30px;margin-bottom:10px;">Fim do 2º Semestre: <b>{calendario['fim_2_sem']}</b></li>                                
                            #</ul>
                        #</p>
                        #<p style="font-size:30px;margin-top:30px;">Data escolhida: <b style="color:red;">{data_horario}</b></p>'''
                #return render_template('render_pdf/render_erro.jinja', msg=msg)

            #grade = banco.executarConsulta(f'''
                                               #SELECT DISTINCT 
                                                    #grade.num_classe, turma.nome_turma, pos, semana, grade.disciplina, disciplinas.abv, professor_livro_ponto.nome_ata as nome, matriz_curricular.cpf_professor, matriz_curricular.tipo
                                                #FROM grade
                                                #LEFT JOIN matriz_curricular ON matriz_curricular.num_classe = grade.num_classe AND matriz_curricular.disc_disciplina = grade.disciplina
                                                #LEFT JOIN professor_livro_ponto ON professor_livro_ponto.cpf = matriz_curricular.cpf_professor
                                                #INNER JOIN turma ON turma.num_classe = grade.num_classe
                                                #INNER JOIN disciplinas ON disciplinas.codigo_disciplina = grade.disciplina
                                                #WHERE turma.tipo_ensino in {tipo_ensino} AND turma.ano = {ano} 
                                                    #AND (
                                                        #CASE duracao 
                                                            #WHEN 3 THEN (SELECT 3bim_inicio FROM calendario WHERE ano = turma.ano)
                                                            #ELSE (SELECT 1bim_inicio FROM calendario WHERE ano = turma.ano)
                                                        #END) <= '{converterDataMySQL(data_horario)}'
                                                    #AND (
                                                        #CASE duracao
                                                            #WHEN 2 THEN (SELECT 2bim_fim FROM calendario WHERE ano = turma.ano)
                                                            #ELSE (SELECT 4bim_fim FROM calendario WHERE ano = turma.ano)
                                                        #END) >= '{converterDataMySQL(data_horario)}'
                                                #ORDER BY semana, pos, nome_turma''')
            
            #tipo = banco.executarConsultaVetor(f"SELECT CAST(GROUP_CONCAT(descricao SEPARATOR ' + ') AS CHAR) as texto FROM tipo_ensino where id in {tipo_ensino}")[0]
            
            #legenda = banco.executarConsulta(f'select distinct tipo, tipo_disc_matriz.desc_completa as descricao from matriz_curricular inner join tipo_disc_matriz on tipo_disc_matriz.id = matriz_curricular.tipo inner join turma on turma.num_classe = matriz_curricular.num_classe where turma.tipo_ensino in {num_classe} and turma.ano = {ano}')

            #grade_final = {}
            #semana = grade[0]['semana']
            #temp = []

            #cont = 0

            # parametrizar nomes dos professores
            #for item in grade:
                #try:
                    #item['nome'] = "(" + item['nome'] + ")"
                #except:
                    #item['nome'] = ''

                # parametrizar eletiva
                #if item['disciplina'] == 8465:
                    #item['abv'] = 'ELETIVA'
                    #item['cpf_professor'] = ''
                    #item['nome'] = ''


                #if item['semana'] != semana:
                    #grade_final[semana] = temp
                    #temp = []
                    #semana = item['semana']
            
                #temp.append(item)

            #grade_final[semana] = temp

            #horario_final = []
            #rowspan = len(horario)

            #parametrizar horário
            #for n in range(0, len(horario)):
                #try:
                    #if horario[n]['fim'] == horario[n+1]['inicio']:
                        #horario_final.append({'horario':horario[n]['horario'], 'intervalo':None})
                    #else:
                        #inicio = datetime(1, 1, 1) + horario[n+1]['inicio']
                        #fim = datetime(1, 1, 1) + horario[n]['fim']
                        #horario_final.append({'horario':horario[n]['horario'], 'intervalo':f"{fim.strftime('%H:%M')} - {inicio.strftime('%H:%M')}"})
                        #rowspan += 1
                #except:
                    #horario_final.append({'horario':horario[n]['horario'], 'intervalo':None})


            #dias_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta']

            #cores = ['#becaa8', '#d084c0', '#c8b8ea', '#d9e9ac', '#96d8ad', '#e7a6c3', '#d8d796', '#9df2f3', '#ee9dc1', '#b1aaf7', '#f9cc87', '#afb3de', '#b3e29e', '#fce5bb', '#a5d4fe', '#cedfb5', '#c3b9af', '#d98deb', '#e2d3d2', '#b9e1d8', '#b99dc2', '#b6efeb', '#d3f98f', '#bbfeb9', '#a8e5f0', '#e98dbf', '#edcd93', '#a8bcab', '#96caac', '#97c4ac', '#b7a2fa', '#c582cf', '#cd8eb9', '#8cff84', '#e5d180', '#bd8ff2', '#c98ce9', '#94fcb6', '#bcbaf9', '#b7c8a7', '#dbe7cf', '#e1d2af', '#e4cac3', '#fdb0db', '#dfad80', '#adf6eb', '#a4eebd', '#8f86b4', '#93c3ae', '#a2b5da']
            #profs = banco.executarConsulta(f'select distinct matriz_curricular.cpf_professor from grade left join matriz_curricular on matriz_curricular.num_classe = grade.num_classe and matriz_curricular.disc_disciplina = grade.disciplina left join professor_livro_ponto on professor_livro_ponto.cpf = matriz_curricular.cpf_professor inner join turma on turma.num_classe = grade.num_classe inner join disciplinas on disciplinas.codigo_disciplina = grade.disciplina where turma.tipo_ensino in {tipo_ensino} and turma.ano = {ano} and matriz_curricular.cpf_professor is not null')

            #cont = 0

            #for item in profs:
                #try:
                    #item['cor'] = cores[cont]
                    #cont += 1
                #except:
                    #cont = 0
                    #item['cor'] = cores[cont]


            #if destino == 'grade_alt':
                #return render_template('render_pdf/render_horario_geral_alt.jinja', turmas=turmas, horario=horario_final, grade=grade_final, dias_semana=dias_semana, rowspan=rowspan, tipo=tipo, legenda=legenda, data=data_horario)    
            #elif destino == 'grade_salas':
                #return render_template('render_pdf/render_horario_salas.jinja', turmas=turmas, horario=horario_final, grade=grade_final, dias_semana=dias_semana, rowspan=rowspan, tipo=tipo, legenda=legenda, data=data_horario, profs=profs)

            #return render_template('render_pdf/render_horario_geral.jinja', turmas=turmas, horario=horario_final, grade=grade_final, dias_semana=dias_semana, rowspan=rowspan, tipo=tipo, legenda=legenda, data=data_horario, profs=profs)

        elif tipo == 'grade_turma':
            num_classe = request.args.getlist('num_classe')[0]
            #ano = request.args.getlist('order')[0]

            sql = """/* Quadro semanal da turma: uma linha por período, colunas Seg..Sex
                        — agora com rótulo especial para ELETIVA: "ELE (Prof1/Prof2)" */
                        WITH
                        base AS (
                        SELECT
                            g.num_classe,
                            g.pos,
                            g.semana,                               -- 2=Seg ... 6=Sex
                            COALESCE(ht.inicio, ha.inicio) AS inicio,
                            COALESCE(ht.fim,    ha.fim)    AS fim,
                            d.abv AS disc_abv,

                            /* pegamos os 2 nomes (preferindo nome_ata) */
                            COALESCE(NULLIF(p1.nome_ata,''), p1.nome) AS prof1_nome,
                            COALESCE(NULLIF(p2.nome_ata,''), p2.nome) AS prof2_nome

                        FROM grade g
                        JOIN disciplinas d
                            ON d.codigo_disciplina = g.disciplina
                        JOIN turma t
                            ON t.num_classe = g.num_classe
                        LEFT JOIN horario_turma ht
                            ON ht.num_classe = g.num_classe
                        AND ht.pos        = g.pos
                        /* Se sua horario_turma diferencia por dia, ative a linha abaixo:
                            AND ht.semana     = g.semana
                        */
                        LEFT JOIN hora_aulas ha
                            ON ha.ano         = t.ano
                        AND ha.tipo_ensino = t.tipo_ensino
                        AND ha.pos         = g.pos
                        LEFT JOIN matriz_curricular mc
                            ON mc.num_classe       = g.num_classe
                        AND mc.disc_disciplina  = g.disciplina
                        LEFT JOIN professor_livro_ponto p1 ON p1.cpf = mc.cpf_professor
                        LEFT JOIN professor_livro_ponto p2 ON p2.cpf = mc.cpf_professor_2
                        WHERE g.num_classe = %s
                            AND g.semana BETWEEN 2 AND 6                 -- só Seg..Sex
                            AND COALESCE(ht.inicio, ha.inicio) IS NOT NULL
                            AND COALESCE(ht.fim,    ha.fim)    IS NOT NULL
                        ),
                        rotulo AS (
                        SELECT
                            num_classe, pos, semana, inicio, fim,
                            /* Se for eletiva (ABV = 'ELE'), juntar 2 profs com "/".
                            Caso contrário, usar só o principal (prof1 -> prof2). */
                            CASE
                            WHEN disc_abv = 'ELE' THEN
                                CASE
                                WHEN (prof1_nome IS NULL OR prof1_nome='') AND (prof2_nome IS NULL OR prof2_nome='') THEN 'ELE'
                                ELSE CONCAT('ELE (', CONCAT_WS(' / ', NULLIF(prof1_nome,''), NULLIF(prof2_nome,'')), ')')
                                END
                            ELSE
                                CASE
                                WHEN COALESCE(prof1_nome, prof2_nome) IS NULL OR COALESCE(prof1_nome, prof2_nome) = '' THEN disc_abv
                                ELSE CONCAT(disc_abv, ' (', COALESCE(NULLIF(prof1_nome,''), prof2_nome), ')')
                                END
                            END AS label
                        FROM base
                        )
                        SELECT
                        CONCAT(DATE_FORMAT(inicio, '%H:%i'), ' à ', DATE_FORMAT(fim, '%H:%i')) AS `Horário`,
                        MAX(CASE WHEN semana = 2 THEN label END) AS `Seg`,
                        MAX(CASE WHEN semana = 3 THEN label END) AS `Ter`,
                        MAX(CASE WHEN semana = 4 THEN label END) AS `Qua`,
                        MAX(CASE WHEN semana = 5 THEN label END) AS `Qui`,
                        MAX(CASE WHEN semana = 6 THEN label END) AS `Sex`
                        FROM rotulo
                        GROUP BY inicio, fim
                        ORDER BY inicio;"""

            rows = banco.executarConsulta(sql, [num_classe])

            print(rows)

            #cores = ['#becaa8', '#d084c0', '#c8b8ea', '#d9e9ac', '#96d8ad', '#e7a6c3', '#d8d796', '#9df2f3', '#ee9dc1', '#b1aaf7', '#f9cc87', '#afb3de', '#b3e29e', '#fce5bb', '#a5d4fe', '#cedfb5', '#c3b9af', '#d98deb', '#e2d3d2', '#b9e1d8', '#b99dc2', '#b6efeb', '#d3f98f', '#bbfeb9', '#a8e5f0', '#e98dbf', '#edcd93', '#a8bcab', '#96caac', '#97c4ac', '#b7a2fa', '#c582cf', '#cd8eb9', '#8cff84', '#e5d180', '#bd8ff2', '#c98ce9', '#94fcb6', '#bcbaf9', '#b7c8a7', '#dbe7cf', '#e1d2af', '#e4cac3', '#fdb0db', '#dfad80', '#adf6eb', '#a4eebd', '#8f86b4', '#93c3ae', '#a2b5da']
            disciplinas = banco.executarConsulta("select disciplinas.abv from matriz_curricular inner join disciplinas on disciplinas.codigo_disciplina = matriz_curricular.disc_disciplina where num_classe = %s" % num_classe)

            i = 0
            for item in disciplinas:
                item['cor'] = pastel_from_label(item['abv'])
                i += 1

            head = banco.executarConsulta('select nome_turma, tipo_ensino.descricao from turma inner join tipo_ensino on tipo_ensino.id = turma.tipo_ensino where num_classe = %s' % num_classe)[0]

            return render_template('render_pdf/render_horario_salas.jinja', dados=rows, cores=disciplinas, head=head)


        
        elif tipo == 'individual': # horário individual dos professores

            data_horario = request.args.getlist('data')[0]
            tipo_ensino = request.args.getlist('num_classe')[0]
            ano = request.args.getlist('order')[0]

            sql = """/* Horário individual: todos os professores ativos que assinam o livro */
                WITH profs AS (
                SELECT p.cpf, p.nome AS prof_nome
                FROM professor_livro_ponto p
                WHERE p.ativo = 1 AND p.assina_livro = 1
                ),
                slots AS (
                /* Aulas da grade/matriz (considerando calendário do ano) */
                SELECT
                    pr.cpf,
                    pr.prof_nome,
                    g.semana,
                    COALESCE(ht.inicio, ha.inicio) AS inicio,
                    COALESCE(ht.fim,    ha.fim)    AS fim,
                    CONCAT(t.apelido,' (', d.abv, ')') AS label
                FROM profs pr
                JOIN matriz_curricular mc
                    ON mc.cpf_professor = pr.cpf OR mc.cpf_professor_2 = pr.cpf
                JOIN turma t            ON t.num_classe = mc.num_classe
                JOIN calendario c       ON c.ano = t.ano
                JOIN disciplinas d      ON d.codigo_disciplina = mc.disc_disciplina
                JOIN grade g            ON g.num_classe = mc.num_classe AND g.disciplina = mc.disc_disciplina
                LEFT JOIN horario_turma ht ON ht.num_classe = g.num_classe AND ht.pos = g.pos
                LEFT JOIN hora_aulas ha    ON ha.ano = t.ano AND ha.tipo_ensino = t.tipo_ensino AND ha.pos = g.pos
                WHERE
                    (CASE t.duracao WHEN 3 THEN c.`3bim_inicio` ELSE c.`1bim_inicio` END) <= %s
                    AND
                    (CASE t.duracao WHEN 2 THEN c.`2bim_fim`    ELSE c.`4bim_fim`    END) >= %s
                    /* Se houver quadro manual no mesmo slot/dia, ele tem prioridade */
                    AND NOT EXISTS (
                    SELECT 1
                    FROM horario_livro_ponto h2
                    WHERE h2.cpf_professor = pr.cpf
                        AND TIME(h2.inicio) = TIME(COALESCE(ht.inicio, ha.inicio))
                        AND TIME(h2.fim)    = TIME(COALESCE(ht.fim,    ha.fim))
                        AND (
                        (g.semana=2 AND h2.seg IS NOT NULL) OR (g.semana=3 AND h2.ter IS NOT NULL) OR
                        (g.semana=4 AND h2.qua IS NOT NULL) OR (g.semana=5 AND h2.qui IS NOT NULL) OR
                        (g.semana=6 AND h2.sex IS NOT NULL) OR (g.semana=7 AND h2.sab IS NOT NULL) OR
                        (g.semana=1 AND h2.dom IS NOT NULL)
                        )
                    )

                UNION ALL

                /* Blocos do quadro manual (horario_livro_ponto) – unpivot seg..dom */
                SELECT
                    pr.cpf,
                    pr.prof_nome,
                    x.semana,
                    TIME(h.inicio) AS inicio,
                    TIME(h.fim)    AS fim,
                    CASE x.semana WHEN 2 THEN h.seg WHEN 3 THEN h.ter WHEN 4 THEN h.qua
                                    WHEN 5 THEN h.qui WHEN 6 THEN h.sex WHEN 7 THEN h.sab
                                    WHEN 1 THEN h.dom END AS label
                FROM profs pr
                JOIN horario_livro_ponto h ON h.cpf_professor = pr.cpf
                JOIN (SELECT 1 AS semana UNION ALL SELECT 2 UNION ALL SELECT 3
                        UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7) x ON 1=1
                WHERE CASE x.semana WHEN 2 THEN h.seg WHEN 3 THEN h.ter WHEN 4 THEN h.qua
                                    WHEN 5 THEN h.qui WHEN 6 THEN h.sex WHEN 7 THEN h.sab
                                    WHEN 1 THEN h.dom END IS NOT NULL
                )
                SELECT cpf, prof_nome, semana, inicio, fim, label
                FROM slots
                WHERE label IS NOT NULL
                ORDER BY prof_nome, semana, inicio;"""

            data_raw = request.args.get('data') or request.args.getlist('data')[0]
            for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
                try:
                    data_ref = datetime.strptime(data_raw, fmt).date()
                    break
                except ValueError:
                    data_ref = None
            if data_ref is None:
                return "Parâmetro 'data' inválido", 400

            rows = banco.executarConsulta(sql, (data_ref, data_ref))


            # agrupar por professor
            by_prof = defaultdict(list)
            for r in rows:
                by_prof[(r['cpf'], r['prof_nome'])].append(r)

            profs = []
            for (cpf, nome), rlist in by_prof.items():
                grid, total = montar_grade_prof(rlist)
                profs.append({'cpf': cpf, 'nome': nome, 'grid': grid, 'total': total})

            profs.sort(key=lambda x: x['nome'])

            return render_template(
                'render_pdf/render_horario_individual.jinja',
                profs=profs
            )                

@app.route('/atualizar_matriz_auto', methods=['GET', 'POST'])
async def atualizar_matriz_auto():

    info = request.json
    num_classe = info['num_classe']
    ano_letivo = banco.executarConsultaVetor(f"select ano from turma where num_classe = '{num_classe}'")[0]
    auth = {'cookie_SED': banco.executarConsultaVetor("select valor from config where id_config = 'credencial'")[0]}
    context = start_context(auth)
    lista_matriz = get_matriz_curricular(context, ano_letivo, num_classe)

    print(lista_matriz)

    lista = []

    for item in lista_matriz:
        try:
            tipo = banco.executarConsultaVetor(f"select id from tipo_disc_matriz where desc_completa like '{item['classificacao']}'")[0]
            disc = item['componente'].split(' - ')[0]
            area = banco.executarConsultaVetor(f'select area from matriz_curricular where disc_disciplina = {disc} order by area desc limit 1')[0]
            qtd = item['carga_horária']

            lista.append({'num_classe':num_classe, 'tipo':tipo, 'disc':disc, 'area':area, 'qtd':qtd, 'minutos':info['minutos']})
        except Exception as error:
            print("An exception occurred:", error) # An exception occurred: division by zero

    return jsonify(lista)


@app.route('/atualizar_lista_auto', methods=['GET', 'POST'])
async def atualizar_lista_auto():

    ano = request.json
    print(ano)

    # primeiro verificar se as turmas tem id_oculto
    id_oculto = banco.executarConsulta('select id_oculto from turma where ano = %s and id_oculto is null' % ano)

    if len(id_oculto) < 1: # significa que todas as turmas tem um id_oculto e por conta disso a busca iniciará pela SED
        socketio.emit('update_info', '<b>Iniciando atualização automática das listas de alunos (%s)... utilizando credenciais da sed...</b>' % ano)

        try:
            auth = {'cookie_SED': banco.executarConsultaVetor("select valor from config where id_config = 'credencial'")[0]}

            context = start_context(auth)
            result_escolas = get_escolas(context)

            id_escola = result_escolas[0]['id']

            turmas = banco.executarConsulta('select num_classe, id_oculto, nome_turma, duracao.descricao as desc_duracao from turma inner join duracao on duracao.id = turma.duracao where ano = %s order by duracao, tipo_ensino, nome_turma' % ano)
            for turma in turmas:
                #socketio.emit('update_info', '<b>Atualizando dados da %s - %s (%s)</b>' % (turma['nome_turma'], turma['desc_duracao'], ano))
                result = get_alunos_num_classe(context, ano, id_escola, turma['id_oculto'])

                lista = []

                for item in result:
                    aluno = {'ra':int(item['ra']), 'digito':"'" + item['ra_dígito'] + "'", 'nome':'"' + item['nome'] + '"', 'nascimento':"'" + item['nascimento_data'].strftime("%Y-%m-%d") + "'", 'matricula':"'" + item['inicio_matricula'].strftime("%Y-%m-%d") + "'", 'num_chamada':item['numero'], 'serie':item['serie'], 'situacao':getSituacao(item['situação']), 'fim_mat':"'" + item['fim_matricula'].strftime("%Y-%m-%d") + "'", 'num_classe':turma['num_classe']}
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

            return jsonify(True)
        except Exception as error:
            print("An exception occurred:", error) # An exception occurred: division by zero
            socketio.emit('update_info', '<b>Erro ao tentar puxar os dados pelas credenciais, mudando para busca automatizada usando um navegador</b>')


    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    user_data_dir = r"C:\temp\chrome-playwright"

    subprocess.Popen([
        chrome_path,
        "--remote-debugging-port=9222",
        f"--user-data-dir={user_data_dir}"
    ])

    browser = await connect({
        'browserURL': 'http://localhost:9222',  # Porta que o Chrome abriu
        'defaultViewport': None
    })

    page = await browser.newPage()

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

    elif info['destino'] == 3: # declaração de matrícula normal

        pdf_path = 'static/docs/declaracao_mat.pdf'
        
        try:
            aluno = banco.executarConsulta('select nome, rg, sexo, concat(LPAD(SUBSTR(ra, -9, 1), 1, 0), SUBSTR(ra, -8, 2), ".", substr(ra, -6, 3), ".", substr(ra, -3, 3), "-", aluno.digito_ra) as ra,' + " ifnull(concat(LPAD(SUBSTR(cpf, -11, 1), 1, 0), SUBSTR(cpf, -10, 2), '.', substr(cpf, -8, 3), '.', substr(cpf, -5, 3), '-', substr(cpf, -2, 2)), '-') as cpf from aluno where ra = %s" % info['ra'].replace('.', '')[:9])[0]
            info_classe = banco.executarConsulta('select turma.num_classe, serie, tipo_ensino, tipo_ensino.descricao as tipo_ensino_desc from turma inner join vinculo_alunos_turmas on vinculo_alunos_turmas.num_classe = turma.num_classe inner join tipo_ensino on tipo_ensino.id = turma.tipo_ensino where ra_aluno = %s and situacao = 1 and tipo_ensino in (1, 3)' % info['ra'].replace('.', '')[:9])[0]
        

            sql = 'SELECT '
            sql += '(select sum(falta) - sum(ac) from notas inner join vinculo_alunos_turmas on vinculo_alunos_turmas.ra_aluno = notas.ra_aluno and vinculo_alunos_turmas.situacao = 1 left join vinculo_alunos_if on vinculo_alunos_if.ra_aluno = notas.ra_aluno and vinculo_alunos_if.situacao = 1 where notas.ra_aluno = %s and (notas.num_classe = vinculo_alunos_turmas.num_classe or notas.num_classe = vinculo_alunos_if.num_classe_if)) as faltas,' % info['ra'].replace('.', '')[:9]
            sql += '(select sum(aulas_dadas) from vinculo_prof_disc inner join vinculo_alunos_turmas on vinculo_alunos_turmas.situacao = 1 and vinculo_alunos_turmas.ra_aluno = %s left join vinculo_alunos_if on vinculo_alunos_if.situacao = 1 and vinculo_alunos_if.ra_aluno = %s where vinculo_prof_disc.num_classe = vinculo_alunos_turmas.num_classe or vinculo_prof_disc.num_classe = vinculo_alunos_if.num_classe_if) as aulas_dadas,' % (info['ra'].replace('.', '')[:9], info['ra'].replace('.', '')[:9])
            sql += '(select max(bimestre) from notas inner join turma on turma.num_classe = notas.num_classe where ra_aluno = %s and turma.ano = YEAR(CURDATE())) as bimestre' % info['ra'].replace('.', '')[:9]

            aux_info = {'nome':aluno['nome'], 'rg':aluno['rg'], 'ra':aluno['ra'], 'cpf':aluno['cpf'], 'genero':aluno['sexo'].lower(), 'tipo':3, 'info_classe':info_classe, 'assinatura':info['assinatura'], 'anos':None}
        except:
            aux_info = info


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
        await page.goto('http://localhost/render_conselho_bimestre_all?bimestre=%s&num_classe=%s&order=0&ano=%s' % (info['bimestre'], info['num_classe'], info['ano']), {'waitUntil':'networkidle2'})
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
        await page.goto('http://localhost/render_livro_ponto?mes=%s&ano=%s&order=0' % (info['mes'], info['ano']), {'waitUntil':'load', 'timeout':60000})
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

            chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            user_data_dir = r"C:\temp\chrome-playwright"

            subprocess.Popen([
                chrome_path,
                "--remote-debugging-port=9222",
                f"--user-data-dir={user_data_dir}"
            ])

            browser = await connect({
                'browserURL': 'http://localhost:9222',  # Porta que o Chrome abriu
                'defaultViewport': None
            })

            page = await browser.newPage()

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
        
        aluno = banco.executarConsulta('select nome, rg, sexo, concat(LPAD(SUBSTR(ra, -9, 1), 1, 0), SUBSTR(ra, -8, 2), ".", substr(ra, -6, 3), ".", substr(ra, -3, 3), "-", aluno.digito_ra) as ra,' + " ifnull(concat(LPAD(SUBSTR(cpf, -11, 1), 1, 0), SUBSTR(cpf, -10, 2), '.', substr(cpf, -8, 3), '.', substr(cpf, -5, 3), '-', substr(cpf, -2, 2)), '-') as cpf from aluno where ra = %s" % info['ra'].replace('.', '')[:9])[0]
        
        info_classe = banco.executarConsulta('select turma.num_classe, serie, tipo_ensino, tipo_ensino.descricao as tipo_ensino_desc from turma inner join vinculo_alunos_turmas on vinculo_alunos_turmas.num_classe = turma.num_classe inner join tipo_ensino on tipo_ensino.id = turma.tipo_ensino where ra_aluno = %s and situacao = 1 and tipo_ensino in (1, 3)' % info['ra'].replace('.', '')[:9])[0]

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

        aux_info = {'nome':aluno['nome'], 'rg':aluno['rg'], 'ra':aluno['ra'], 'cpf':aluno['cpf'], 'genero':aluno['sexo'].lower(), 'tipo':4, 'info_classe':info_classe, 'percent':freq_percent, 'bimestre':bimestre, 'anos':None, 'assinatura':info['assinatura']}

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
        
        aluno = banco.executarConsulta('select nome, rg, sexo, concat(LPAD(SUBSTR(ra, -9, 1), 1, 0), SUBSTR(ra, -8, 2), ".", substr(ra, -6, 3), ".", substr(ra, -3, 3), "-", aluno.digito_ra) as ra' + " ifnull(concat(LPAD(SUBSTR(cpf, -11, 1), 1, 0), SUBSTR(cpf, -10, 2), '.', substr(cpf, -8, 3), '.', substr(cpf, -5, 3), '-', substr(cpf, -2, 2)), '-') as cpf from aluno where ra = %s" % info['ra'].replace('.', '')[:9])[0]
        
        info_classe = banco.executarConsulta('select turma.num_classe, serie, tipo_ensino, tipo_ensino.descricao as tipo_ensino_desc from turma inner join vinculo_alunos_turmas on vinculo_alunos_turmas.num_classe = turma.num_classe inner join tipo_ensino on tipo_ensino.id = turma.tipo_ensino where ra_aluno = %s and situacao = 1 and tipo_ensino in (1, 3)' % info['ra'].replace('.', '')[:9])[0]

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

        aux_info = {'nome':aluno['nome'], 'rg':aluno['rg'], 'ra':aluno['ra'], 'cpf':aluno['cpf'], 'genero':aluno['sexo'].lower(), 'tipo':4, 'info_classe':info_classe, 'percent':freq_percent, 'bimestre':bimestre, 'anos':info['anos']}

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

    elif info['destino'] == 15: #horário geral com legenda ou individual
        pdf_path_1 = 'static/docs/horario_horizontal.pdf'
        pdf_path_2 = 'static/docs/horario_turmas.pdf'
        pdf_path = 'static/docs/horario_geral.pdf'

        ano = info['ano']
        estilo = info['estilo']
        ensino = info['ensino']
        data = info['data']

        if ensino == 'individual':
            estilo = 'individual'

        if ensino == 'individual_salas':
            estilo = 'individual_salas'

        browser = await launch(
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False,
        )

        print('http://localhost/render_lista?tipo=%s&num_classe=%s&order=%s&data=%s' % (estilo, ensino, ano, data))

        page = await browser.newPage()
        await page.goto('http://localhost/render_lista?tipo=%s&num_classe=%s&order=%s&data=%s' % (estilo, ensino, ano, data), {'waitUntil':'networkidle2'})
        await page.pdf({'path': pdf_path, 'format':'A4', 'scale':1, 'printBackground':True, 'margin': {'top': '10mm', 'right': '10mm', 'bottom': '9mm', 'left': '10mm'}})

        if (estilo == 'individual'):
            await browser.close()
            return jsonify(pdf_path)

        #await page.goto('http://localhost/render_lista?tipo=grade_salas&num_classe=%s&order=%s&data=%s' % (ensino, ano, data), {'waitUntil':'networkidle2'})
        #await page.pdf({'path': pdf_path_2, 'format':'A4', 'landscape': True, 'scale':1, 'printBackground':True, 'margin': {'top': '10mm', 'right': '10mm', 'bottom': '10mm', 'left': '10mm'}})

        await browser.close()

        # Mesclar os PDFs
        #merger = PdfMerger()
        #merger.append(pdf_path_1)
        #merger.append(pdf_path_2)
        #merger.write(pdf_path)
        #merger.close()        

        return jsonify(pdf_path)

    elif info['destino'] == 16: # lista de chamada
        pdf_path = 'static/docs/chamada.pdf'

        mes = info['mes']
        order = info['order']
        num_classe = info['turma']
        cor = info['cor'].replace("#", '')


        browser = await launch(
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False
        )        

        page = await browser.newPage()
        await page.goto('http://localhost/render_lista?tipo=chamada&num_classe=%s&order=%s&mes=%s&cor=%s' % (num_classe, order, mes, cor), {'waitUntil':'networkidle2'})
        await page.pdf({'path': pdf_path, 'format':'A4', 'landscape':True, 'scale':1, 'printBackground':True})
        await browser.close()

        return jsonify(pdf_path)

    elif info['destino'] == 17:
        pdf_path = 'static/docs/assinatura.pdf'

        num_classe = info['turma']
        tipo = info['tipo']
        order = info['order']
        titulo = info['titulo']
        colunas = info['colunas']

        browser = await launch(
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False
        )        

        page = await browser.newPage()
        await page.goto('http://localhost/render_lista?tipo=%s&num_classe=%s&order=%s&titulo=%s&colunas=%s' % (tipo, num_classe, order, titulo, colunas), {'waitUntil':'networkidle2'})
        await page.pdf({'path': pdf_path, 'format':'A4', 'scale':1, 'printBackground':True})
        await browser.close()

        return jsonify(pdf_path)    

    elif info['destino'] == 18: # declaração de transferência
        pdf_path = 'static/docs/declaracao.pdf'

        aluno = banco.executarConsulta('select nome, rg, sexo, concat(LPAD(SUBSTR(ra, -9, 1), 1, 0), SUBSTR(ra, -8, 2), ".", substr(ra, -6, 3), ".", substr(ra, -3, 3), "-", aluno.digito_ra) as ra,' + " ifnull(concat(LPAD(SUBSTR(cpf, -11, 1), 1, 0), SUBSTR(cpf, -10, 2), '.', substr(cpf, -8, 3), '.', substr(cpf, -5, 3), '-', substr(cpf, -2, 2)), '-') as cpf from aluno where ra = %s" % info['ra'].replace('.', '')[:9])[0]
        
        info_classe = banco.executarConsulta('select turma.num_classe, serie, tipo_ensino, tipo_ensino.descricao as tipo_ensino_desc from turma inner join vinculo_alunos_turmas on vinculo_alunos_turmas.num_classe = turma.num_classe inner join tipo_ensino on tipo_ensino.id = turma.tipo_ensino where ra_aluno = %s and tipo_ensino in (1, 3) order by vinculo_alunos_turmas.fim_mat desc limit 1' % info['ra'].replace('.', '')[:9])[0]

        aux_info = {'tipo':info['tipo'], 'ra':info['ra'], 'nome':aluno['nome'], 'rg':aluno['rg'], 'cpf':aluno['cpf'], 'genero':aluno['sexo'].lower(), 'anos':None, 'assinatura':info['assinatura'], 'info_classe':info_classe, 'nome_resp':info['nome_resp'], 'rg_resp':info['rg_resp']}

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

    elif info['destino'] == 19: # declaração de matrícula com horário
        
        pdf_path = 'static/docs/declaracao_horario.pdf'
        
        aluno = banco.executarConsulta('select nome, rg, sexo, concat(LPAD(SUBSTR(ra, -9, 1), 1, 0), SUBSTR(ra, -8, 2), ".", substr(ra, -6, 3), ".", substr(ra, -3, 3), "-", aluno.digito_ra) as ra,' + " ifnull(concat(LPAD(SUBSTR(cpf, -11, 1), 1, 0), SUBSTR(cpf, -10, 2), '.', substr(cpf, -8, 3), '.', substr(cpf, -5, 3), '-', substr(cpf, -2, 2)), '-') as cpf from aluno where ra = %s" % info['ra'].replace('.', '')[:9])[0]
        
        info_classe = banco.executarConsulta(r'select turma.num_classe, serie, tipo_ensino, tipo_ensino.descricao as tipo_ensino_desc, periodo.descricao as periodo, TIME_FORMAT(periodo.horario_inicio, "%Hh%i") as inicio, TIME_FORMAT(periodo.horario_fim, "%Hh%i") as fim from turma inner join periodo on periodo.id = turma.periodo inner join vinculo_alunos_turmas on vinculo_alunos_turmas.num_classe = turma.num_classe inner join tipo_ensino on tipo_ensino.id = turma.tipo_ensino where ra_aluno = ' + '%s and situacao = 1 and tipo_ensino in (1, 3)' % info['ra'].replace('.', '')[:9])[0]

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

        aux_info = {'nome':aluno['nome'], 'rg':aluno['rg'], 'ra':aluno['ra'], 'cpf':aluno['cpf'], 'genero':aluno['sexo'].lower(), 'tipo':9, 'info_classe':info_classe, 'percent':freq_percent, 'bimestre':bimestre, 'anos':None, 'assinatura':info['assinatura']}

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

    
    elif info['destino'] == 20: # declaração de conclusão
        pdf_path = 'static/docs/declaracao_conclusao.pdf'

        aluno = banco.executarConsulta('select nome, rg, sexo, concat(LPAD(SUBSTR(ra, -9, 1), 1, 0), SUBSTR(ra, -8, 2), ".", substr(ra, -6, 3), ".", substr(ra, -3, 3), "-", aluno.digito_ra) as ra,' + " ifnull(concat(LPAD(SUBSTR(cpf, -11, 1), 1, 0), SUBSTR(cpf, -10, 2), '.', substr(cpf, -8, 3), '.', substr(cpf, -5, 3), '-', substr(cpf, -2, 2)), '-') as cpf from aluno where ra = %s" % info['ra'].replace('.', '')[:9])[0]

        query = r'''SELECT
	                turma.num_classe,
                    turma.ano,
                    serie, 
                    tipo_ensino, 
                    tipo_ensino.descricao AS tipo_ensino_desc, 
                    periodo.descricao AS periodo, 
                    TIME_FORMAT(periodo.horario_inicio, "%Hh%i") AS inicio, 
                    TIME_FORMAT(periodo.horario_fim, "%Hh%i") AS fim 
                FROM turma 
                INNER JOIN periodo ON periodo.id = turma.periodo 
                INNER JOIN vinculo_alunos_turmas ON vinculo_alunos_turmas.num_classe = turma.num_classe 
                INNER JOIN tipo_ensino ON tipo_ensino.id = turma.tipo_ensino 
                WHERE ra_aluno = ''' + info['ra'].replace('.', '')[:9] + ''' and situacao = 6 and tipo_ensino in (1, 3)
                ORDER BY ano DESC LIMIT 1'''
        
        print(query)

        info_classe = banco.executarConsulta(query)[0]

        aux_info = {'nome':aluno['nome'], 'rg':aluno['rg'], 'ra':aluno['ra'], 'cpf':aluno['cpf'], 'genero':aluno['sexo'].lower(), 'tipo':10, 'info_classe':info_classe, 'anos':None, 'assinatura':info['assinatura']}

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
    
    elif info['destino'] == 21:
        pdf_path = 'static/docs/etiqueta.pdf'

        num_classe = info['turma']

        browser = await launch(
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False
        )        

        page = await browser.newPage()
        await page.goto('http://localhost/render_etiquetas_alunos?classe=%s' % (num_classe), {'waitUntil':'networkidle2'})
        await page.pdf({'path': pdf_path, 'format':'A4', 'scale':1, 'printBackground':True, 'margin': {'top': '10mm', 'right': '10mm', 'bottom': '10mm', 'left': '10mm'}})
        await browser.close()

        return jsonify(pdf_path)

    elif info['destino'] == 22:
        pdf_path = 'static/docs/horario_turma.pdf'

        num_classe = info['num_classe']

        browser = await launch(
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False
        )        

        page = await browser.newPage()
        await page.goto('http://localhost/render_lista?tipo=grade_turma&num_classe=%s&order=0&ano=0' % (num_classe), {'waitUntil':'networkidle2'})
        await page.pdf({'path': pdf_path, 'format':'A4', 'landscape':True, 'scale':1, 'printBackground':True, 'margin': {'top': '10mm', 'right': '10mm', 'bottom': '10mm', 'left': '10mm'}})
        await browser.close()

        return jsonify(pdf_path)

    elif info['destino'] == 23:
        pdf_path = 'static/docs/relatorio.pdf'

        browser = await launch(
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False
        )        

        page = await browser.newPage()
        await page.goto('http://localhost/render_relatorio_funcionarios_geral', {'waitUntil':'networkidle2'})
        await page.pdf({'path': pdf_path, 'format':'A4', 'landscape':True, 'scale':1, 'printBackground':True, 'margin': {'top': '10mm', 'right': '10mm', 'bottom': '10mm', 'left': '10mm'}})
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

            disciplinas = banco.executarConsulta('select professor.nome_ata, disciplina, disciplinas.abv as desc_disc, disciplinas.descricao as completo from vinculo_prof_disc inner join professor on professor.rg = vinculo_prof_disc.cpf_prof inner join disciplinas ON disciplinas.codigo_disciplina = vinculo_prof_disc.disciplina  where bimestre = %s and num_classe = %s order by disciplina' % (info['bimestre'], info['num_classe']))

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

    funcionarios = banco.executarConsulta('select cpf, nome from funcionario_livro_ponto where ativo = 1 order by nome')

    return render_template('declaracoes.jinja', funcionarios=funcionarios)

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

            disciplinas = banco.executarConsulta('select professor.nome_ata, disciplina, disciplinas.abv as desc_disc, disciplinas.descricao as completo, aulas_dadas from vinculo_prof_disc inner join professor on professor.rg = vinculo_prof_disc.cpf_prof inner join disciplinas ON disciplinas.codigo_disciplina = vinculo_prof_disc.disciplina  where bimestre = %s and num_classe = %s order by disciplina' % (info['bimestre'], info['num_classe']))

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

            total_habilitados_certificado = banco.executarConsultaVetor('select count(*) as total from vinculo_alunos_turmas where num_classe = %s and situacao in (6) and serie in (3, 4, 9)' % num_classe)[0]
            
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
            
            chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            user_data_dir = r"C:\temp\chrome-playwright"

            subprocess.Popen([
                chrome_path,
                "--remote-debugging-port=9222",
                f"--user-data-dir={user_data_dir}"
            ])

            browser = await connect({
                'browserURL': 'http://localhost:9222',  # Porta que o Chrome abriu
                'defaultViewport': None
            })

            page = await browser.newPage()

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
        info = banco.executarConsulta('select num_classe, nome_turma, duracao.descricao as duracao, periodo.descricao as periodo, tipo_ensino.descricao as tipo_ensino, id_oculto from turma INNER JOIN duracao ON duracao.id = turma.duracao INNER JOIN periodo ON periodo.id = turma.periodo INNER JOIN tipo_ensino ON tipo_ensino.id = turma.tipo_ensino WHERE num_classe = %s' % classe)
        if (info == []):
            info = banco.executarConsulta('select num_classe, nome_turma, duracao.descricao as duracao, periodo.descricao as periodo, tipo_ensino.descricao as tipo_ensino from turma_if as turma INNER JOIN duracao ON duracao.id = turma.duracao INNER JOIN periodo ON periodo.id = turma.periodo INNER JOIN tipo_ensino ON tipo_ensino.id = turma.tipo_ensino WHERE num_classe = %s' % classe)

    if request.method == "POST":

        #print(request.form)
        info = banco.executarConsulta('select num_classe, nome_turma, turma.ano, duracao.descricao as duracao, periodo.descricao as periodo, tipo_ensino.descricao as tipo_ensino, id_oculto from turma INNER JOIN duracao ON duracao.id = turma.duracao INNER JOIN periodo ON periodo.id = turma.periodo INNER JOIN tipo_ensino ON tipo_ensino.id = turma.tipo_ensino WHERE num_classe = %s' % request.form.get('classe'))
        if (info == []):
            info = banco.executarConsulta('select num_classe, nome_turma, turma.ano, duracao.descricao as duracao, periodo.descricao as periodo, tipo_ensino.descricao as tipo_ensino from turma_if as turma INNER JOIN duracao ON duracao.id = turma.duracao INNER JOIN periodo ON periodo.id = turma.periodo INNER JOIN tipo_ensino ON tipo_ensino.id = turma.tipo_ensino WHERE num_classe = %s' % request.form.get('classe'))

        print(request.form.get('id_oculto'))

        # localizando o ID oculto fará uma pesquisa na API do SED para pegar os alunos direto da SED
        if 'id_oculto' in request.form:
            auth = {'cookie_SED': banco.executarConsultaVetor("select valor from config where id_config = 'credencial'")[0]}

            #try:
            context = start_context(auth)
            result_escolas = get_escolas(context)

            id_escola = result_escolas[0]['id']
            print(id_escola)

            # a partir daqui será dividido as tarefas dependendo do objetivo desejado
            lista = []
            alunos = get_alunos_num_classe(context, info[0]['ano'], id_escola, request.form.get('id_oculto'))
            codigos_alunos = get_alunos_codigo(context, info[0]['ano'], id_escola, request.form.get('id_oculto'))
            print(codigos_alunos)
            
            for aluno in alunos:
                    sit = 0

                    if aluno['situação'] == "ATIVO":
                        sit = 1
                    elif aluno['situação'] == 'BXTR' or aluno['situação'] == 'TRAN':
                        sit = 2
                    elif aluno['situação'] == "REMA":
                        sit = 3
                    elif aluno['situação'] == "NCFP" or aluno['situação'] == "NCOM":
                        sit = 5
                    elif aluno['situação'] == "CONCL":
                        sit = 8
                    elif aluno['situação'] == "APROVADO":
                        sit = 6
                    elif aluno['situação'] == "RETIDO FREQ." or aluno['situação'] == 'RETIDO REND.':
                        sit = 10
                    elif aluno['situação'] == 'RECL':
                        sit = 15
                    elif aluno['situação'] == 'ENCERRADA':
                        sit = 16    

                    aluno_add = {'id':codigos_alunos[aluno['ra']], 'ra':aluno['ra'], 'digito':aluno['ra_dígito'], 'nome':aluno['nome'], 'nascimento':aluno['nascimento_data'].strftime("%d/%m/%Y"), 'matricula':aluno['inicio_matricula'].strftime("%d/%m/%Y"), 'num_chamada':aluno['numero'], 'serie':aluno['serie'], 'desc_sit':aluno['situação'], 'situacao':sit, 'fim_mat':aluno['fim_matricula'].strftime("%d/%m/%Y"), 'sexo':'M', 'rg':'', 'cpf':'', 'rm':''}

                    # procurar por informações adicionais do aluno na SED e depois o RM no banco
                    info_aluno = get_info_aluno(context, aluno_add['id'])
                    aluno_add['sexo'] = info_aluno['sexo'][0]
                    aluno_add['cpf'] = info_aluno['cpf']

                    if info_aluno['cin']:
                        aluno_add['rg'] = 'CIN'
                    elif info_aluno['rg_uf'] is not None:
                        if (info_aluno['rg_uf'] == 'SP'):
                            aluno_add['rg'] = info_aluno['rg'][6:8] + '.' + info_aluno['rg'][8:11] + '.' + info_aluno['rg'][11:] + '-' + info_aluno['rg_dígito']
                        else:
                            aluno_add['rg'] = info_aluno['rg'] + '-' + info_aluno['rg_dígito'] + '/' + info_aluno['rg_uf']

                        if aluno_add['rg'] == '-/':
                            aluno_add['rg'] = ''

                    consulta_rm = banco.executarConsultaVetor("select ifnull(rm, '') as rm from aluno where ra = '%s'" % aluno_add['ra'])
                    if len(consulta_rm) > 0:
                        aluno_add['rm'] = consulta_rm[0]

                    lista.append(aluno_add)

            return render_template('upload_turma.jinja', lista=lista, info=info)
            #except Exception as e:
                #print(e)
                #return render_template('upload_turma.jinja', lista=[], info=info)



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

    funcionarios = banco.executarConsulta('select cpf, nome, rg, digito, cargos_livro_ponto.descricao as cargo from funcionario_livro_ponto inner join cargos_livro_ponto on cargos_livro_ponto.id = funcionario_livro_ponto.cargo where ativo = 1 order by nome')
    for funcionario in funcionarios:
        rg = "%08d" % int(funcionario['rg'])
        funcionario['rg'] = '%s.%s.%s-%s' % (rg[:2], rg[2:5], rg[5:8], funcionario['digito'])

    return render_template('alunos.jinja', lista=lista, funcionarios=funcionarios)


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
                #print('aqui?')
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

                professores = banco.executarConsulta('select professor_livro_ponto.nome_ata, vinculo_prof_disc.disciplina, disciplinas.abv as desc_disc, aulas_dadas from vinculo_prof_disc inner join professor_livro_ponto on professor_livro_ponto.cpf = vinculo_prof_disc.cpf_prof inner join disciplinas ON disciplinas.codigo_disciplina = vinculo_prof_disc.disciplina  where bimestre = %s and num_classe = %s order by vinculo_prof_disc.disciplina' % (info['bimestre'], info['num_classe']))

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

                professores = banco.executarConsulta('select professor_livro_ponto.nome_ata, vinculo_prof_disc.disciplina, disciplinas.abv as desc_disc, aulas_dadas from vinculo_prof_disc inner join professor_livro_ponto on professor_livro_ponto.cpf = vinculo_prof_disc.cpf_prof inner join disciplinas ON disciplinas.codigo_disciplina = vinculo_prof_disc.disciplina  where num_classe = %s order by vinculo_prof_disc.disciplina' % info['num_classe'])
                #professores = banco.executarConsulta(sql)
                print(professores)

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
            file_extension = os.path.splitext(isthisFile.filename)[1]
            file_dir = os.path.join(app.config['UPLOAD_FOLDER'], f'mapao{file_extension}')
            isthisFile.save(file_dir)

            if file_extension == '.xlsx':
                excel = open_xls(file_dir)
            else:
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

            if request.form.getlist('duracao')[0] == '1º Semestre':
                bimestre_final = 2
            else:
                bimestre_final = 4

            lista = []

            if file_extension == '.xlsx':

                total_linha = excel.getTotalRows()
                total_coluna = int(excel.getTotalColumns() / 4)
                linha_inicial = 11
                coluna_inicial = 3


                # caso seja Conselho Final (Quinto Conceito)
                if excel.getCell(7, 2) == "Conselho Final (QUINTO CONCEITO)":
                    total_coluna = int(excel.getTotalColumns() / 2)
                    #print(total_coluna)
                    #print(excel.getTotalColumns())

                    for i in range(1, total_coluna + 1):
                        #print(excel.getCell(linha_inicial, coluna_inicial))
                        try:
                            item = {'disc': extrair_numeros(excel.getCell(linha_inicial, coluna_inicial))}
                            
                            if item['disc'].isnumeric():
                                professor = banco.executarConsulta('select professor_livro_ponto.nome_ata, professor_livro_ponto.cpf from matriz_curricular inner join professor_livro_ponto on matriz_curricular.cpf_professor = professor_livro_ponto.cpf where num_classe = %s and disc_disciplina = %s' % (request.form.getlist('num_classe')[0], item['disc']))

                                print(professor)
                                if len(professor) > 0:
                                    item['abv'] = banco.executarConsulta('select abv from disciplinas where codigo_disciplina = %s' % item['disc'])[0]['abv']
                                    
                                    medias = {}
                                    
                                    for j in range(linha_inicial + 2, total_linha):
                                        medias[str(excel.getCell(j, coluna_inicial)).zfill(2)] = {'M':excel.getCell(j, coluna_inicial + 1)}

                                    item['medias'] = medias
                                    item['professor'] = professor[0]['nome_ata']

                                    lista.append(item)

                                coluna_inicial += 2
                        except Exception as e:
                            print(f"Erro ao processar disciplina: {e}")
                            coluna_inicial += 2
                            continue

                    print(lista)

                else:
                    for i in range(1, total_coluna + 1):
                        print(excel.getCell(linha_inicial, coluna_inicial))
                        item = {'disc': extrair_numeros(excel.getCell(linha_inicial, coluna_inicial))}
                    
                        if item['disc'].isnumeric():
                            print(total_linha)
                            ad = int(excel.getCell(total_linha, coluna_inicial).replace('Aulas Dadas: ', ''))
                            professor = banco.executarConsulta('select professor_livro_ponto.nome_ata, professor_livro_ponto.cpf from matriz_curricular inner join professor_livro_ponto on matriz_curricular.cpf_professor = professor_livro_ponto.cpf where num_classe = %s and disc_disciplina = %s' % (request.form.getlist('num_classe')[0], item['disc']))
                            item['professor'] = professor[0]['nome_ata'] if len(professor) > 0 else '---'
                            item['professor_cpf'] = professor[0]['cpf'] if len(professor) > 0 else 'null'

                            if ad > 0:
                                item['AD'] = excel.getCell(total_linha, coluna_inicial).replace('Aulas Dadas: ', '')

                                # percorrer a lista
                                notas = {}
                            
                                for j in range(linha_inicial + 2, total_linha):
                                    notas[str(excel.getCell(j, coluna_inicial)).zfill(2)] = {'N':excel.getCell(j, coluna_inicial + 1), 'F':excel.getCell(j, coluna_inicial + 2), 'AC':excel.getCell(j, coluna_inicial + 3)} 

                                item['notas'] = notas

                                item['abv'] = banco.executarConsulta('select abv from disciplinas where codigo_disciplina = %s' % item['disc'])[0]['abv']
                            
                                lista.append(item)

                        coluna_inicial += 4

            else:
                for i in range(0, int(math.ceil(total))):
                    item = {'disc':data[0][coluna][12]}
                    print(item)
                    
                    if str(item['disc']).isnumeric():

                        if data[0][31][6] == "Tipo de Fechamento: CONSELHO FINAL (QUINTO CONCEITO)":

                            professor = item['professor'] = banco.executarConsulta('select professor.nome_ata as nome from vinculo_prof_disc inner join professor ON professor.rg = vinculo_prof_disc.cpf_prof where num_classe = %s and bimestre = %s and disciplina = %s' % (request.form.getlist('num_classe')[0], bimestre_final, item['disc']))
                            item['professor_cpf'] = professor[0]['cpf'] if len(professor) > 0 else 'null'

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

            #verificar se já existe professores vinculados a disciplina e se existir criar uma lista
            professores_atuais = banco.executarConsulta('select cpf_prof, disciplina from vinculo_prof_disc where bimestre = %s and num_classe = %s' % (request.form.getlist('bimestre')[0], request.form.getlist('num_classe')[0]))
            dict_aux = {}
            for item in professores_atuais:
                dict_aux[item['disciplina']] = item['cpf_prof']

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

@app.route('/render_quadro_professor', methods=['GET', 'POST'])
def render_quadro_professor():
    ano = request.args.getlist('ano')[0]
    
    query = """
        SELECT p.nome, d.descricao, t.apelido, m.qtd_aulas
        FROM matriz_curricular m
        JOIN turma t ON m.num_classe = t.num_classe
        JOIN disciplinas d ON m.disc_disciplina = d.codigo_disciplina
        JOIN professor_livro_ponto p ON p.cpf in  (m.cpf_professor, m.cpf_professor_2) 
        WHERE t.ano = """ + ano + " AND t.tipo_ensino in (1, 3) ORDER BY p.nome, d.descricao;"
    
    resultados = banco.executarConsultaBasic(query)

    mapa = {}
    todas_turmas = set()

    for prof, disc, turma, qtd in resultados:
        todas_turmas.add(turma)
        if prof not in mapa:
            mapa[prof] = {"nome": prof, "disciplinas": {}, "total": 0}
        
        if disc not in mapa[prof]["disciplinas"]:
            mapa[prof]["disciplinas"][disc] = {}
            
        mapa[prof]["disciplinas"][disc][turma] = qtd
        mapa[prof]["total"] += qtd

    # Ordena as turmas (ex: 6ºA antes de 7ºA)
    lista_turmas_ordenada = sorted(list(todas_turmas), key=ordenar_turmas)
    
    return render_template('render_pdf/render_quadro_professor.jinja', profs=mapa.values(), lista_turmas=lista_turmas_ordenada)

@app.route('/render_relatorio_funcionarios_geral', methods=['GET', 'POST'])
def render_relatorio_funcionarios_geral():
                titulos = ['Quadro Administrativo', 'Docentes Ativos', 'Docentes Ativos de outra UE', 'Docentes Afastados/Interrupção de Exercício']
                listas = []

                listas.append(banco.executarConsulta(r"select nome, rg, digito, cpf, di, DATE_FORMAT(nascimento, '%d/%m/%Y') as nascimento, rs, pv, FNREF, categoria_livro_ponto.letra as categoria, cargos_livro_ponto.abv from funcionario_livro_ponto inner join categoria_livro_ponto on categoria_livro_ponto.id = funcionario_livro_ponto.categoria inner join cargos_livro_ponto on cargos_livro_ponto.id = funcionario_livro_ponto.cargo where ativo = 1 order by nome"))
                listas.append(banco.executarConsulta(r"select nome, rg, digito, cpf, di, DATE_FORMAT(nascimento, '%d/%m/%Y') as nascimento, rs, pv, FNREF, categoria_livro_ponto.letra as categoria,       cargos_livro_ponto.abv from professor_livro_ponto inner join categoria_livro_ponto on categoria_livro_ponto.id = professor_livro_ponto.categoria inner join cargos_livro_ponto on cargos_livro_ponto.id = professor_livro_ponto.cargo where ativo = 1 and sede_controle_freq = 41707 and assina_livro = 1 order by nome"))
                listas.append(banco.executarConsulta(r"select nome, rg, digito, cpf, di, DATE_FORMAT(nascimento, '%d/%m/%Y') as nascimento, rs, pv, FNREF, categoria_livro_ponto.letra as categoria,       cargos_livro_ponto.abv from professor_livro_ponto inner join categoria_livro_ponto on categoria_livro_ponto.id = professor_livro_ponto.categoria inner join cargos_livro_ponto on cargos_livro_ponto.id = professor_livro_ponto.cargo where ativo = 1 and assina_livro = 1 and sede_controle_freq != 41707 order by nome"))
                listas.append(banco.executarConsulta(r"select nome, rg, digito, cpf, di, DATE_FORMAT(nascimento, '%d/%m/%Y') as nascimento, rs, pv, FNREF, categoria_livro_ponto.letra as categoria,       cargos_livro_ponto.abv from professor_livro_ponto inner join categoria_livro_ponto on categoria_livro_ponto.id = professor_livro_ponto.categoria inner join cargos_livro_ponto on cargos_livro_ponto.id = professor_livro_ponto.cargo where ativo = 1 and assina_livro = 0 order by nome"))


                for lista in listas:
                    for item in lista:
                        rg = "%08d" % int(item['rg'])
                        if (int(item['rg']) == int(item['cpf'])):
                            item['rg'] = "CIN"
                        elif item['digito'] == None:
                            item['rg'] = '%s.%s.%s' % (rg[:2], rg[2:5], rg[5:8])
                        else:
                            item['rg'] = '%s.%s.%s-%s' % (rg[:2], rg[2:5], rg[5:8], item['digito'])                            

                        cpf = "%011d" % item['cpf']
                        item['cpf'] = '%s.%s.%s-%s' % (cpf[:3], cpf[3:6], cpf[6:9], cpf[9:])

                        item['rs'] = "%08d" % item['rs']
                        item['pv'] = "%02d" % item['pv']

                return render_template('render_pdf/render_funcionarios_geral.jinja', opcao = 3, lista_final=listas, titulos=titulos)

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
    alunos = banco.executarConsulta('select ra_aluno, nome, situacao.descricao as situacao from vinculo_alunos_turmas inner join aluno on aluno.ra = vinculo_alunos_turmas.ra_aluno inner join situacao on vinculo_alunos_turmas.situacao = situacao.id where num_classe = %s and situacao in (1, 6, 7, 8, 10, 16) order by nome' % num_classe)

    print(alunos)

    # pegar as disciplinas das turmas
    disciplinas = banco.executarConsulta('select disciplinas.descricao as disc, notas.disciplina, disciplinas.classificacao from notas inner join disciplinas on disciplinas.codigo_disciplina = notas.disciplina where num_classe = %s group by disciplina order by classificacao, disciplina' % num_classe)

    # pegar a informação da classe
    info_classe = banco.executarConsulta('select nome_turma, tipo_ensino.descricao as tipo_ensino from turma inner join tipo_ensino on tipo_ensino.id = turma.tipo_ensino where num_classe = %s' % num_classe)[0]

    # correr a lista dos alunos e buscar a nota
    for aluno in alunos:

        #if aluno['ra_aluno'] == 112523955: # aluno de teste
            #print('select bimestre, nota, falta, ac, disciplinas.descricao as disc, disciplinas.codigo_disciplina from notas inner join disciplinas on disciplinas.codigo_disciplina = notas.disciplina inner join turma on turma.ano = %s and turma.duracao = %s and turma.num_classe = notas.num_classe where ra_aluno = %s order by disc, bimestre' % (ano, duracao, aluno['ra_aluno']))

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

        # pegar total de aulas dadas por bimestre
        sql = f'''SELECT 
              ifnull((select sum(aulas_dadas) from vinculo_prof_disc where bimestre = 1 and num_classe = (select distinct notas.num_classe from notas left join turma on turma.num_classe = notas.num_classe left join turma_if on turma_if.num_classe = notas.num_classe where ra_aluno = {aluno['ra_aluno']} and bimestre = 1 and (turma.ano = {ano} or turma_if.ano = {ano}) and (turma.duracao = {duracao} or turma_if.duracao = {duracao}) and turma.tipo_ensino in (1, 3))), 0) as 1bim, 
              ifnull((select sum(aulas_dadas) from vinculo_prof_disc where bimestre = 2 and num_classe = (select distinct notas.num_classe from notas left join turma on turma.num_classe = notas.num_classe left join turma_if on turma_if.num_classe = notas.num_classe where ra_aluno = {aluno['ra_aluno']} and bimestre = 2 and (turma.ano = {ano} or turma_if.ano = {ano}) and (turma.duracao = {duracao} or turma_if.duracao = {duracao}) and turma.tipo_ensino in (1, 3))), 0) as 2bim, 
              ifnull((select sum(aulas_dadas) from vinculo_prof_disc where bimestre = 3 and num_classe = (select distinct notas.num_classe from notas left join turma on turma.num_classe = notas.num_classe left join turma_if on turma_if.num_classe = notas.num_classe where ra_aluno = {aluno['ra_aluno']} and bimestre = 3 and (turma.ano = {ano} or turma_if.ano = {ano}) and (turma.duracao = {duracao} or turma_if.duracao = {duracao}) and turma.tipo_ensino in (1, 3))), 0) as 3bim,
              ifnull((select sum(aulas_dadas) from vinculo_prof_disc where bimestre = 4 and num_classe = (select distinct notas.num_classe from notas left join turma on turma.num_classe = notas.num_classe left join turma_if on turma_if.num_classe = notas.num_classe where ra_aluno = {aluno['ra_aluno']} and bimestre = 4 and (turma.ano = {ano} or turma_if.ano = {ano}) and (turma.duracao = {duracao} or turma_if.duracao = {duracao}) and turma.tipo_ensino in (1, 3))), 0) as 4bim'''
    
        aluno['aulas_dadas'] = banco.executarConsulta(sql)[0]

        # pegar o total de faltas e ac por bimestre
        sql = f'''SELECT
                    IFNULL((SELECT SUM(falta) FROM notas WHERE ra_aluno = {aluno['ra_aluno']} and bimestre = 1 AND num_classe = (select distinct notas.num_classe from notas left join turma on turma.num_classe = notas.num_classe left join turma_if on turma_if.num_classe = notas.num_classe where ra_aluno = {aluno['ra_aluno']} and bimestre = 1 and (turma.ano = {ano} or turma_if.ano = {ano}) and (turma.duracao = {duracao} or turma_if.duracao = {duracao}) and turma.tipo_ensino in (1, 3))), 0) AS falta_1bim, 
                    IFNULL((SELECT SUM(ac) FROM notas WHERE ra_aluno = {aluno['ra_aluno']} and bimestre = 1 AND num_classe = (select distinct notas.num_classe from notas left join turma on turma.num_classe = notas.num_classe left join turma_if on turma_if.num_classe = notas.num_classe where ra_aluno = {aluno['ra_aluno']} and bimestre = 1 and (turma.ano = {ano} or turma_if.ano = {ano}) and (turma.duracao = {duracao} or turma_if.duracao = {duracao}) and turma.tipo_ensino in (1, 3))), 0) AS ac_1bim, 
                    IFNULL((SELECT SUM(falta) FROM notas WHERE ra_aluno = {aluno['ra_aluno']} and bimestre = 2 AND num_classe = (select distinct notas.num_classe from notas left join turma on turma.num_classe = notas.num_classe left join turma_if on turma_if.num_classe = notas.num_classe where ra_aluno = {aluno['ra_aluno']} and bimestre = 2 and (turma.ano = {ano} or turma_if.ano = {ano}) and (turma.duracao = {duracao} or turma_if.duracao = {duracao}) and turma.tipo_ensino in (1, 3))), 0) AS falta_2bim, 
                    IFNULL((SELECT SUM(ac) FROM notas WHERE ra_aluno = {aluno['ra_aluno']} and bimestre = 2 AND num_classe = (select distinct notas.num_classe from notas left join turma on turma.num_classe = notas.num_classe left join turma_if on turma_if.num_classe = notas.num_classe where ra_aluno = {aluno['ra_aluno']} and bimestre = 2 and (turma.ano = {ano} or turma_if.ano = {ano}) and (turma.duracao = {duracao} or turma_if.duracao = {duracao}) and turma.tipo_ensino in (1, 3))), 0) AS ac_2bim, 
                    IFNULL((SELECT SUM(falta) FROM notas WHERE ra_aluno = {aluno['ra_aluno']} and bimestre = 3 AND num_classe = (select distinct notas.num_classe from notas left join turma on turma.num_classe = notas.num_classe left join turma_if on turma_if.num_classe = notas.num_classe where ra_aluno = {aluno['ra_aluno']} and bimestre = 3 and (turma.ano = {ano} or turma_if.ano = {ano}) and (turma.duracao = {duracao} or turma_if.duracao = {duracao}) and turma.tipo_ensino in (1, 3))), 0) AS falta_3bim, 
                    IFNULL((SELECT SUM(ac) FROM notas WHERE ra_aluno = {aluno['ra_aluno']} and bimestre = 3 AND num_classe = (select distinct notas.num_classe from notas left join turma on turma.num_classe = notas.num_classe left join turma_if on turma_if.num_classe = notas.num_classe where ra_aluno = {aluno['ra_aluno']} and bimestre = 3 and (turma.ano = {ano} or turma_if.ano = {ano}) and (turma.duracao = {duracao} or turma_if.duracao = {duracao}) and turma.tipo_ensino in (1, 3))), 0) AS ac_3bim, 
                    IFNULL((SELECT SUM(falta) FROM notas WHERE ra_aluno = {aluno['ra_aluno']} and bimestre = 4 AND num_classe = (select distinct notas.num_classe from notas left join turma on turma.num_classe = notas.num_classe left join turma_if on turma_if.num_classe = notas.num_classe where ra_aluno = {aluno['ra_aluno']} and bimestre = 4 and (turma.ano = {ano} or turma_if.ano = {ano}) and (turma.duracao = {duracao} or turma_if.duracao = {duracao}) and turma.tipo_ensino in (1, 3))), 0) AS falta_4bim, 
                    IFNULL((SELECT SUM(ac) FROM notas WHERE ra_aluno = {aluno['ra_aluno']} and bimestre = 4 AND num_classe = (select distinct notas.num_classe from notas left join turma on turma.num_classe = notas.num_classe left join turma_if on turma_if.num_classe = notas.num_classe where ra_aluno = {aluno['ra_aluno']} and bimestre = 4 and (turma.ano = {ano} or turma_if.ano = {ano}) and (turma.duracao = {duracao} or turma_if.duracao = {duracao}) and turma.tipo_ensino in (1, 3))), 0) AS ac_4bim'''

        aluno['total_faltas'] = banco.executarConsulta(sql)[0]

        # calcular frequência total - não fazer consulta no banco, pois já temos as aulas dadas e faltas
        freq_1bim = 100 - ((aluno['total_faltas']['falta_1bim'] - aluno['total_faltas']['ac_1bim']) * 100 / aluno['aulas_dadas']['1bim']) if aluno['aulas_dadas']['1bim'] > 0 else '-'
        freq_2bim = 100 - ((aluno['total_faltas']['falta_2bim'] - aluno['total_faltas']['ac_2bim']) * 100 / aluno['aulas_dadas']['2bim']) if aluno['aulas_dadas']['2bim'] > 0 else '-'
        freq_3bim = 100 - ((aluno['total_faltas']['falta_3bim'] - aluno['total_faltas']['ac_3bim']) * 100 / aluno['aulas_dadas']['3bim']) if aluno['aulas_dadas']['3bim'] > 0 else '-'
        freq_4bim = 100 - ((aluno['total_faltas']['falta_4bim'] - aluno['total_faltas']['ac_4bim']) * 100 / aluno['aulas_dadas']['4bim']) if aluno['aulas_dadas']['4bim'] > 0 else '-'

        total_aulas_dadas = aluno['aulas_dadas']['1bim'] + aluno['aulas_dadas']['2bim'] + aluno['aulas_dadas']['3bim'] + aluno['aulas_dadas']['4bim']
        total_faltas = aluno['total_faltas']['falta_1bim'] + aluno['total_faltas']['falta_2bim'] + aluno['total_faltas']['falta_3bim'] + aluno['total_faltas']['falta_4bim']
        total_ac = aluno['total_faltas']['ac_1bim'] + aluno['total_faltas']['ac_2bim'] + aluno['total_faltas']['ac_3bim'] + aluno['total_faltas']['ac_4bim']
        if total_aulas_dadas > 0:
            frequencia_final = 100 - ((total_faltas - total_ac) * 100 / total_aulas_dadas)
        else:
            frequencia_final = '-'


        aluno['freq_total'] = {
            '1bim': freq_1bim.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP) if isinstance(freq_1bim, Decimal) else freq_1bim,
            '2bim': freq_2bim.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP) if isinstance(freq_2bim, Decimal) else freq_2bim,
            '3bim': freq_3bim.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP) if isinstance(freq_3bim, Decimal) else freq_3bim,
            '4bim': freq_4bim.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP) if isinstance(freq_4bim, Decimal) else freq_4bim,
            'total':frequencia_final.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP) if isinstance(frequencia_final, Decimal) else frequencia_final}

        # obter frequência por disciplina
        sql = 'select disciplina, sum(falta) - sum(ac) as faltas from notas left join turma on turma.num_classe = notas.num_classe left join turma_if on turma_if.num_classe = notas.num_classe where ra_aluno = %s and (turma.ano = %s or turma_if.ano = %s) group by disciplina ' % (aluno['ra_aluno'], ano, ano)
        #print(sql)
        freq_disciplinas = banco.executarConsulta(sql)
        
        freq_final = {}
        conceito_final = {}

        for disc in freq_disciplinas:
            sql = 'select '
            sql += 'ifnull((select aulas_dadas from vinculo_prof_disc where bimestre = 1 and disciplina = %s and num_classe = (select notas.num_classe from notas left join turma on turma.num_classe = notas.num_classe left join turma_if on turma_if.num_classe = notas.num_classe where disciplina = %s and ra_aluno = %s and bimestre = 1 and (turma.ano = %s or turma_if.ano = %s) and (turma.duracao = %s or turma_if.duracao = %s))), 0) as 1bim, ' % (disc['disciplina'], disc['disciplina'], aluno['ra_aluno'], ano, ano, duracao, duracao)
            sql += 'ifnull((select aulas_dadas from vinculo_prof_disc where bimestre = 2 and disciplina = %s and num_classe = (select notas.num_classe from notas left join turma on turma.num_classe = notas.num_classe left join turma_if on turma_if.num_classe = notas.num_classe where disciplina = %s and ra_aluno = %s and bimestre = 2 and (turma.ano = %s or turma_if.ano = %s) and (turma.duracao = %s or turma_if.duracao = %s))), 0) as 2bim, ' % (disc['disciplina'], disc['disciplina'], aluno['ra_aluno'], ano, ano, duracao, duracao)
            sql += 'ifnull((select aulas_dadas from vinculo_prof_disc where bimestre = 3 and disciplina = %s and num_classe = (select notas.num_classe from notas left join turma on turma.num_classe = notas.num_classe left join turma_if on turma_if.num_classe = notas.num_classe where disciplina = %s and ra_aluno = %s and bimestre = 3 and (turma.ano = %s or turma_if.ano = %s) and (turma.duracao = %s or turma_if.duracao = %s))), 0) as 3bim, ' % (disc['disciplina'], disc['disciplina'], aluno['ra_aluno'], ano, ano, duracao, duracao)
            sql += 'ifnull((select aulas_dadas from vinculo_prof_disc where bimestre = 4 and disciplina = %s and num_classe = (select notas.num_classe from notas left join turma on turma.num_classe = notas.num_classe left join turma_if on turma_if.num_classe = notas.num_classe where disciplina = %s and ra_aluno = %s and bimestre = 4 and (turma.ano = %s or turma_if.ano = %s) and (turma.duracao = %s or turma_if.duracao = %s))), 0) as 4bim ' % (disc['disciplina'], disc['disciplina'], aluno['ra_aluno'], ano, ano, duracao, duracao)

            aulas_dadas = banco.executarConsulta(sql)[0]
            total_aulas = aulas_dadas['1bim'] + aulas_dadas['2bim'] + aulas_dadas['3bim'] + aulas_dadas['4bim']

            try:
                freq_calc = 100 - (disc['faltas'] * 100 / total_aulas)
                freq_final[disc['disciplina']] = round(freq_calc, 1)
            except:
                freq_final[disc['disciplina']] = ''

            media = banco.executarConsultaVetor("select ifnull(media, '-') from conceito_final inner join turma on turma.num_classe = conceito_final.num_classe and turma.ano = %s where disciplina = %s and ra_aluno = %s and conceito_final.num_classe = %s" % (ano, disc['disciplina'], aluno['ra_aluno'], num_classe))
            if len(media) > 0:
                conceito_final[disc['disciplina']] = media[0]
            else:
                # verificar se é nota de if
                media = banco.executarConsultaVetor("select ifnull(media, '-') from conceito_final inner join turma_if on turma_if.num_classe = conceito_final.num_classe and turma_if.ano = %s where disciplina = %s and ra_aluno = %s" % (ano, disc['disciplina'], aluno['ra_aluno']))
                if len(media) > 0:
                    conceito_final[disc['disciplina']] = media[0]
                else:
                    conceito_final[disc['disciplina']] = 'null'


        aluno['freq'] = freq_final
        aluno['final'] = conceito_final

        print('cheguei aqui?')


    return render_template('render_pdf/render_boletim.jinja', alunos=alunos, disciplinas=disciplinas, info_classe=info_classe, duracao=duracao, ano=ano, desc_duracao=desc_duracao)


@app.route('/ponto_adm', methods=['GET', 'POST'])
def ponto_adm():
    
    msg=''

    if request.method == 'POST': # houve envio de formulário

        if request.is_json:
            info = request.json

            if info['destino'] == 0: # pegar os dados do professor para editar no formulário
                detalhes = banco.executarConsulta(r"select cpf, nome, rg, ifnull(digito, '') as digito, cargo, plantao, estudante, horario, intervalo, di, categoria, DATE_FORMAT(nascimento, '%Y-%m-%d') as nascimento, rs, pv, FNREF from funcionario_livro_ponto WHERE cpf = " + info['cpf'])[0]
                return jsonify(detalhes)
            
            elif info['destino'] == 1: # quadro de afastamentos
                lista = banco.executarConsulta(r"SELECT cpf, DATE_FORMAT(inicio,'%d/%m/%Y') as dt_inicio, DATE_FORMAT(fim,'%d/%m/%Y') as dt_fim, descricao FROM afastamentos_ponto_adm WHERE cpf = " + str(info['cpf']) + ' and year(fim) = year(current_date) order by inicio')
                return jsonify(lista)

            elif info['destino'] == 2: # puxa os dados da SED
                auth = {'cookie_SED': banco.executarConsultaVetor("select valor from config where id_config = 'credencial'")[0]}
                context = start_context(auth)

                return jsonify({'dados':get_funcionario_info(context, info['cpf'], info['rg']), 'result': True})
              

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
            dados['di'] = request.form['di']
            dados['categoria'] = request.form['categoria']
            dados['nascimento'] = "'%s'" % request.form['nascimento']
            dados['rs'] = request.form['rs']
            dados['pv'] = request.form['pv']
            dados['FNREF'] = "'%s'" % request.form['fnref']

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
    categorias = banco.executarConsulta('select * from categoria_livro_ponto where id < 4')

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

    return render_template('livro_ponto_admin.jinja', meses=meses, ano=data_atual.strftime("%Y"), cargos=cargos, msg=msg, funcionarios=funcionarios, desativados=desativados, categorias=categorias)

@app.route('/ponto', methods=['GET', 'POST'])
def ponto():

    msg = ''

    if request.method == 'POST': # houve envio de formulário

        if request.is_json: # enviado por ajax
            info = request.json

            if info['destino'] == 0: # pegar os dados do professor para editar no formulário
                detalhes = banco.executarConsulta("select instancia_calendario, cpf, nome, nome_ata, rg, ifnull(digito, '') as digito, ifnull(rs, '') as rs, ifnull(pv, '') as pv, cargo, categoria, jornada, sede_classificacao, sede_controle_freq, ifnull(di, '') as di, ifnull(disciplina, 'null') as disciplina, ifnull(afastamento, 'null') as afastamento, assina_livro, ifnull(FNREF, '') as FNREF, ifnull(obs, '') as obs, ifnull(atpc, '') as atpc, ifnull(atpl, '') as atpl, ifnull(aulas_outra_ue, '') as aulas_outra_ue, " + r"DATE_FORMAT(nascimento, '%Y-%m-%d') as nascimento" + " from professor_livro_ponto WHERE cpf = %s and di = %s" % (info['cpf'], info['di']))[0]
                return jsonify(detalhes)
            
            elif info['destino'] == 1: # pegar quadro aula
                quadro = banco.executarConsulta(r"select periodo,  DATE_FORMAT(inicio, '%H:%i') as inicio, DATE_FORMAT(fim, '%H:%i') as fim, ifnull(seg, '') as seg, ifnull(ter, '') as ter, ifnull(qua, '') as qua, ifnull(qui, '') as qui, ifnull(sex, '') as sex, ifnull(sab, '') as sab, ifnull(dom, '') as dom from horario_livro_ponto where cpf_professor = " + info['cpf'] + ' ORDER BY inicio')

                aulas_ue = banco.executarConsulta('select * from aulas_outra_ue_livro_ponto where cpf_professor = %s' % info['cpf'])
                aulas = {}

                for aula in aulas_ue:
                    aulas[aula['semana']] = aula['qtd']

                return jsonify({'quadro':quadro, 'aulas_ue':aulas})
            
            elif info['destino'] == 2: # pegar os dado do professor para exibir no formulário

                sql = "SELECT nome, rg, ifnull(digito, '') as digito, ifnull(rs, '') as rs, ifnull(pv, '') as pv, cargos_livro_ponto.descricao as cargo, concat(categoria_livro_ponto.letra, ' - ', categoria_livro_ponto.descricao) as categoria, " + \
                      r"DATE_FORMAT(nascimento, '%Y-%m-%d') as nascimento, " + \
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

                eventos_funcionais = banco.executarConsulta('select * from eventos_funcionais order by descricao')
                tabela_eventos = banco.executarConsulta(f"select id_evento, vigencia, DATE_FORMAT(vigencia, '%Y-%m-%d') AS vigencia_format, cpf_professor, DATE_FORMAT(vigencia, '%d/%m/%Y') as vigencia_view, DATE_FORMAT(DATE_ADD(vigencia, INTERVAL qtd_dias_proximo DAY), '%d/%m/%Y') as proximo from vinculo_professor_eventos_funcionais where cpf_professor = {info['cpf']} and id_evento = {eventos_funcionais[0]['id']} order by vigencia")

                return jsonify({'quadro':quadro, 'detalhes':detalhes, 'eventos_funcionais':eventos_funcionais, 'tabela_eventos':tabela_eventos})

            elif info['destino'] == 3: # listar as licenças
                licencas = banco.executarConsulta(r'SELECT DATE_FORMAT(inicio, "%d/%m/%Y") as inicio, DATE_FORMAT(fim, "%d/%m/%Y") as fim, id_tipo, tipo_licenca_professores.descricao as desc_tipo, licenca_professores.descricao from licenca_professores inner join tipo_licenca_professores on tipo_licenca_professores.id = licenca_professores.id_tipo where cpf = ' + info['cpf'])
                return jsonify(licencas)

            elif info['destino'] == 4: # importar os dados pela SED
                try:
                    auth = {'cookie_SED': banco.executarConsultaVetor("select valor from config where id_config = 'credencial'")[0]}
                    context = start_context(auth)

                    return jsonify({'dados':get_professor_info(context, info['cpf'], info['rg']), 'result': True})
                except Exception as e:
                    print(e)
                    return jsonify({'error': str(e), 'result': False})

            elif info['destino'] == 5: # consultar eventos funcionais
                eventos = banco.executarConsulta(f"select id_evento, vigencia, DATE_FORMAT(vigencia, '%Y-%m-%d') AS vigencia_format, cpf_professor, DATE_FORMAT(vigencia, '%d/%m/%Y') as vigencia_view, DATE_FORMAT(DATE_ADD(vigencia, INTERVAL qtd_dias_proximo DAY), '%d/%m/%Y') as proximo from vinculo_professor_eventos_funcionais where cpf_professor = {info['cpf']} and id_evento = {info['evento']} order by vigencia")
                return jsonify(eventos)

        if 'cpf_delete_quadro' in request.form: # é pra deletar o quadro de aulas do professor
            cpf = request.form['cpf_delete_quadro']

            if banco.excluirQuadro(cpf):
                msg = '<div class="alert alert-success alert-dismissible fade show" role="alert">' \
                        '<strong>Operação realizada com sucesso!</strong> Quadro de aulas do professor excluído com sucesso!' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'
            else:
                msg = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' \
                        '<strong>Atenção!</strong> Erro ao tentar excluir quadro de aulas do professor no banco de dados!' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'
        
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
            dados['nome_ata'] = 'null' if request.form['nome_ata'] == '' else "'%s'" % request.form['nome_ata']
            dados['nascimento'] = "'%s'" % request.form['nascimento']

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

        if 'info_afs' in request.form: # é pra criar a lista de licenças

            lista = json.loads(request.form['info_afs'])
            cpf = int(request.form['cpf'])

            print(lista)

            if banco.inserirLicenca(cpf, lista):
                msg = '<div class="alert alert-success alert-dismissible fade show" role="alert">' \
                        '<strong>Operação realizada com sucesso!</strong> Lista de Afastamentos registrados com sucesso!' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'    

            else:
                msg = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' \
                        '<strong>Atenção!</strong> Erro ao tentar inserir dados no banco de dados! Verifique se as datas não batem!' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'  

        if 'evento_funcional' in request.form: # é pra cadastrar novo evento funcional

            id_evento_funcional = request.form['evento_funcional']
            vigencia = request.form['vigencia_evento']
            qtd_dias_proximo = request.form['qtd_dias_evento']
            cpf_professor = request.form['cpf_professor']

            if banco.executeBasicSQL(f"INSERT INTO vinculo_professor_eventos_funcionais VALUES({cpf_professor}, {id_evento_funcional}, '{vigencia}', {qtd_dias_proximo})"):
                msg = '<div class="alert alert-success alert-dismissible fade show" role="alert">' \
                        '<strong>Operação realizada com sucesso!</strong> Novo Evento Funcional Cadastrado com Sucesso!' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'    

            else:
                msg = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' \
                        '<strong>Atenção!</strong> Erro ao tentar inserir dados! Verifique se esse evento já não foi cadastrado com essa vigência!' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>' 

        if 'id_evento_funcional' in request.form: # é pra deletar evento funcional

            id_evento_funcional = request.form['id_evento_funcional']
            vigencia = request.form['vigencia_evento_funcional']
            cpf_professor = request.form['cpf_professor_evento_funcional']

            if banco.executeBasicSQL(f"DELETE FROM vinculo_professor_eventos_funcionais WHERE cpf_professor = {cpf_professor} AND id_evento = {id_evento_funcional} AND vigencia = '{vigencia}'"):
                msg = '<div class="alert alert-success alert-dismissible fade show" role="alert">' \
                        '<strong>Operação realizada com sucesso!</strong> Evento Funcional deletado com sucesso!' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>'    

            else:
                msg = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' \
                        '<strong>Atenção!</strong> Erro ao tentar inserir dados! Contate o Administrador!' \
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' \
                        '</div>' 


    cargos = banco.executarConsulta('select * from cargos_livro_ponto where tipo = 1')
    categorias = banco.executarConsulta('select * from categoria_livro_ponto')
    jornadas = banco.executarConsulta('select * from jornada_livro_ponto')
    escolas = banco.executarConsulta("select id, concat('UA: ', id, ' - ', descricao) as descricao from sede_livro_ponto order by id")
    disciplinas = banco.executarConsulta('select codigo_disciplina as id, descricao from disciplinas where classificacao = 1 order by descricao')
    afastamentos = banco.executarConsulta("select id, concat(id, ' - ', descricao) as desc_longo from afastamento_livro_ponto order by descricao")
    licencas = banco.executarConsulta("select id, descricao from tipo_licenca_professores order by descricao")

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

    return render_template('livro_ponto.jinja', cargos=cargos, categorias=categorias, jornadas=jornadas, escolas=escolas, disciplinas=disciplinas, afastamentos=afastamentos, msg=msg, professores=professores, desativados=desativados, periodos=periodos, meses=meses, ano=data_atual.strftime("%Y"), instancias=instancias, licencas=licencas)


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

@app.route('/historicos', methods=['GET', 'POST'])
def historicos():

    anos = banco.executarConsulta('select distinct ano from turma inner join vinculo_alunos_turmas on vinculo_alunos_turmas.num_classe = turma.num_classe where situacao in (6) and serie in (3, 4, 9) order by ano desc')

    if len(anos) > 0:
        ano_selecionado = anos[0]['ano']
        result = ''

        fundamental = banco.executarConsulta('select ra_aluno, aluno.nome from vinculo_alunos_turmas inner join aluno on aluno.ra = vinculo_alunos_turmas.ra_aluno inner join turma on turma.num_classe = vinculo_alunos_turmas.num_classe where ano = %s and situacao = 6 and serie = 9 order by nome' % ano_selecionado)
        medio = banco.executarConsulta('select ra_aluno, aluno.nome from vinculo_alunos_turmas inner join aluno on aluno.ra = vinculo_alunos_turmas.ra_aluno inner join turma on turma.num_classe = vinculo_alunos_turmas.num_classe where ano = %s and situacao = 6 and serie = 3 order by nome' % ano_selecionado)
    
        return render_template('historicos.jinja', anos=anos, fundamental=fundamental, medio=medio, ano_selecionado=ano_selecionado, result=result)
    else:
        return redirect('/')

if __name__ == '__main__':
    #app.run('0.0.0.0',port=80)
    #app.run(debug=True)
    app.run(debug=True, use_reloader=True, port=5000)
    #serve(app, host='0.0.0.0', port=80, threads=8)