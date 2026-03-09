import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dataclasses import dataclass
import re
import json
from MySQL import db
from utilitarios import parse_dotnet_date

# Lê o arquivo JSON
with open("config_db.json") as f:
    config = json.load(f)

# configuração do server principal
banco = db(config)

@dataclass
class SEDContext:
	session: requests.Session
	request_verification_token: str = ''
	authorization: str = ''
	token_funcional: str = ''
	token_boletim: str = ''

def start_context(auth):
	session = requests.Session()
	session.cookies.set('SED', auth['cookie_SED'])

	# request_verification_token
	response = session.get('https://sed.educacao.sp.gov.br/NCA/Matricula/ConsultaMatricula/Index')
	soup = BeautifulSoup(response.text, 'html.parser')
	request_verification_token = soup.find('input', attrs={'name': '__RequestVerificationToken'})['value']	

	# Token para funcional
	response = session.get('https://sed.educacao.sp.gov.br/Funcional/Consulta/Index')
	soup = BeautifulSoup(response.text, 'html.parser')
	token_funcional = soup.find('input', attrs={'name': '__RequestVerificationToken'})['value']

	headers = {
		'X-Requested-With': 'XMLHttpRequest',
		'Referer': 'https://sed.educacao.sp.gov.br/Inicio'
	}

    # --- Boletim (NOVO)
    # tenta abrir o módulo do boletim; se a sessão tiver acesso, aqui normalmente nasce token/cookies do módulo
	response = session.get('https://sed.educacao.sp.gov.br/Boletim/BoletimAluno', headers=headers)
	soup = BeautifulSoup(response.text, 'html.parser')
	token_boletim = soup.find('input', attrs={'name': '__RequestVerificationToken'})['value']


	# authorization
	response = session.get("https://sed.educacao.sp.gov.br/NCA/FichaAluno/Consulta")

	match = re.search(r'Execute\.Init\("(.*?)"', response.text)
	authorization = match.group(1)

	return SEDContext(session=session, request_verification_token=request_verification_token, authorization=authorization, token_funcional=token_funcional, token_boletim=token_boletim)

def get_cookies(auth):
	return {
		'SED': auth['cookie_SED'],
	}

def get_escolas(context):
	response = context.session.get('https://sed.educacao.sp.gov.br/nca/Matricula/ConsultaMatricula/DropDownEscolasCIEJson')

	json = response.json()

	escolas = []
	for item in json:
		escolas.append({
			'id': item['Value'],
			'nome': item['Text'],
		})

	return escolas

def pegar_disciplina(tr, td_index):
	td = tr.find_all('td')[td_index]
	div = td.find('div')
	return div.get('data-cddisciplina') if div else 'null'


def get_funcionario_info(context, cpf_professor, rg_professor):

	final_data = {}

	headers = {
		'X-Requested-With': 'XMLHttpRequest'
    }

	# pegar dados básicos do professor
	response = context.session.post(
		'https://sed.educacao.sp.gov.br/Funcional/Consulta/ListarServidoresPessoal',
		data={
			'NrCpf': cpf_professor,
			'NrRg': rg_professor,
			'NmServidor': '',
			'ConsultaTipo': 'false',
			'__RequestVerificationToken': context.token_funcional  # novo token, da página correta
		},
		headers=headers
	)

	dados = response.json()
	
	final_data['nome'] = dados['ListServidores'][0]['DsNome'].title().replace('Da ', 'da ').replace("De ", "de ").replace("Do ", 'do ').replace("Dos ", 'dos ')
	final_data['cpf'] = dados['ListServidores'][0]['NrCpf']
	final_data['rg'] = dados['ListServidores'][0]['NrRg']
	final_data['digito-rg'] = dados['ListServidores'][0]['CdVerifRg']
	final_data['nascimento'] = parse_dotnet_date(dados['ListServidores'][0]['DtNascimento']).strftime('%Y-%m-%d')

	# pegar dados funcionais do funcionário
	response = context.session.post('https://sed.educacao.sp.gov.br/Funcional/Consulta/ListarDadosFuncionais',
		data={
			'NrCpf': final_data['cpf']
		},
		headers=headers
	)

	soup = BeautifulSoup(response.text, 'html.parser')
	tabela = soup.find(id='tblFuncional')
	trs = tabela.tbody.find_all('tr')
	
	dados_funcionais = []

	for tr in trs:

		json_td = json.loads(tr.find('i')['onclick'].replace('DetalharDadosFuncionais(', '')[:-1])

		try:
			info = {
				'di': tr.find_all('td')[1].get_text(strip=True),
				'vinculo': tr.find_all('td')[2].get_text(strip=True),
				'cargo': tr.find_all('td')[3].get_text(strip=True),
				'ua_classe': tr.find_all('td')[4].get_text(strip=True),
				'situacao': tr.find_all('td')[5].get_text(strip=True),
				'cod_faixa':json_td['CodigoIdentidadeReferenciaFaixa'],
				'cod_cargo': banco.executarConsulta("select id from cargos_livro_ponto where cod_sed = %s " % json_td['CdCargo'])[0]['id'] if json_td['CdCargo'] else None,
				'vinculo_cod': banco.executarConsulta("select id from categoria_livro_ponto where letra = '%s'" % json_td['CdIdentCatFunc'])[0]['id'] if 'CdIdentCatFunc' in json_td else None,
				}
		except:
			info = {
				'di': tr.find_all('td')[1].get_text(strip=True),
				'vinculo': tr.find_all('td')[2].get_text(strip=True),
				'cargo': tr.find_all('td')[3].get_text(strip=True),
				'ua_classe': tr.find_all('td')[4].get_text(strip=True),
				'situacao': tr.find_all('td')[5].get_text(strip=True),
				'cod_faixa':json_td['CodigoIdentidadeReferenciaFaixa'],
				'cod_cargo': banco.executarConsulta("select id from cargos_livro_ponto where cod_sed = %s " % json_td['CdCargo'])[0]['id'] if json_td['CdCargo'] else None,
				'vinculo_cod': None,
				}			
		
		dados_funcionais.append(info)

	final_data['dados_funcionais'] = dados_funcionais


	# pegar vínculo com a fazenda
	response = context.session.post('https://sed.educacao.sp.gov.br/Funcional/Consulta/ListarConvenioFazenda',
		data={
			'NrCpf': final_data['cpf']
		},
		headers=headers
	)

	fazenda_html = BeautifulSoup(response.text, 'html.parser')

	rs = fazenda_html.find(id="txtNrRs")['value']
	pv = '0'

	tabela_fazenda = fazenda_html.find(id="tblConvFaz")
	trs = tabela_fazenda.tbody.find_all('tr')

	for tr in trs:
		colunas = tr.find_all('td')

		if colunas[7].get_text(strip=True) in ("Ativo", "Designação"):
			pv = colunas[2].get_text(strip=True)
		else:
			print(colunas[7].get_text(strip=True))


	final_data['fazenda'] = {'rs':int(rs), 'pv':int(pv)}
	
	return final_data


def get_professor_info(context, cpf_professor, rg_professor):

	final_data = {}

	headers = {
		'X-Requested-With': 'XMLHttpRequest'
    }

	# pegar dados básicos do professor
	response = context.session.post(
		'https://sed.educacao.sp.gov.br/Funcional/Consulta/ListarServidoresPessoal',
		data={
			'NrCpf': cpf_professor,
			'NrRg': rg_professor,
			'NmServidor': '',
			'ConsultaTipo': 'false',
			'__RequestVerificationToken': context.token_funcional  # novo token, da página correta
		},
		headers=headers
	)

	dados = response.json()
	
	final_data['nome'] = dados['ListServidores'][0]['DsNome'].title().replace('Da ', 'da ').replace("De ", "de ").replace("Do ", 'do ').replace("Dos ", 'dos ')
	final_data['cpf'] = dados['ListServidores'][0]['NrCpf']
	final_data['rg'] = dados['ListServidores'][0]['NrRg']
	final_data['digito-rg'] = dados['ListServidores'][0]['CdVerifRg']
	final_data['nascimento'] = parse_dotnet_date(dados['ListServidores'][0]['DtNascimento']).strftime('%Y-%m-%d')

	# pegar dados funcionais do professor
	response = context.session.post('https://sed.educacao.sp.gov.br/Funcional/Consulta/ListarDadosFuncionais',
		data={
			'NrCpf': final_data['cpf']
		},
		headers=headers
	)

	soup = BeautifulSoup(response.text, 'html.parser')
	tabela = soup.find(id='tblFuncional')
	trs = tabela.tbody.find_all('tr')
	
	dados_funcionais = []

	for tr in trs:

		json_td = json.loads(tr.find('i')['onclick'].replace('DetalharDadosFuncionais(', '')[:-1])
		cod_jornada = banco.executarConsulta("select id from jornada_livro_ponto where letra = '%s'" % json_td['CdJornada'])
		cd_disciplina = banco.executarConsulta(f'''select codigo_disciplina from disciplinas where descricao like "{json_td['NmDisciplina']}"''')

		info = {
			'di': tr.find_all('td')[1].get_text(strip=True),
			'vinculo': tr.find_all('td')[2].get_text(strip=True),
			'cargo': tr.find_all('td')[3].get_text(strip=True),
			'ua_classe': tr.find_all('td')[4].get_text(strip=True),
			'situacao': tr.find_all('td')[5].get_text(strip=True),
			'cod_faixa':json_td['CodigoIdentidadeReferenciaFaixa'],
			'disciplina': json_td['NmDisciplina'],
			'cod_disciplina': cd_disciplina[0]['codigo_disciplina'] if len(cd_disciplina) > 0 else "null",
			'cod_cargo': banco.executarConsulta("select id from cargos_livro_ponto where cod_sed = %s " % json_td['CdCargo'])[0]['id'] if json_td['CdCargo'] else None,
			'cod_jornada': cod_jornada[0]['id'] if len(cod_jornada) > 0 else 1,
			'CdAfastamento': json_td['DsMotAfast'].split(' - ')[0] if json_td['DsMotAfast'].split(' - ')[0] != "" else "null",
			'vinculo_cod': banco.executarConsulta("select id from categoria_livro_ponto where letra = '%s'" % json_td['CdIdentCatFunc'])[0]['id'] if 'CdIdentCatFunc' in json_td else None,
			}
		
		dados_funcionais.append(info)

	final_data['dados_funcionais'] = dados_funcionais
	
	return final_data


def get_grade(context, num_classe):
	response = context.session.post('https://sed.educacao.sp.gov.br/GradeHoraria/Pesquisar',
		data={
			'nrClasse': num_classe,
			'cdEscola':0,
			'anoLetivo': 0,
			'cdTurma': 0,
			'periodoUc7': 0,
			'__RequestVerificationToken': context.request_verification_token,
		})

	soup = BeautifulSoup(response.text, 'html.parser')
	trs = soup.tbody.findAll('tr')

	grade = []

	for tr in trs:
		seg = pegar_disciplina(tr, 1)
		ter = pegar_disciplina(tr, 2)
		qua = pegar_disciplina(tr, 3)
		qui = pegar_disciplina(tr, 4)
		sex = pegar_disciplina(tr, 5)

		if seg == 'null' and ter == 'null' and qua == 'null' and qui == 'null' and sex == 'null':
			continue

		grade.append({'Seg': seg, 'Ter': ter, 'Qua': qua, 'Qui': qui, 'Sex': sex})

	return grade

def get_matriz_curricular(context, ano_letivo, num_classe):
	response = context.session.post('https://sed.educacao.sp.gov.br/NCA/ColetaTurma/TurmaClasse/Pesquisar',
		data={
			'tipoPesquisa':1,
			'anoLetivo': ano_letivo,
			'codigoDiretoria':20202,
			'codigoMunicipio':9087,
			'codigoEscolaCIE':0,
			'numeroClasse': num_classe,
			'situacaoEscola':1,
			'ejaEad':'false',
			'__RequestVerificationToken': context.request_verification_token,

		})

	soup = BeautifulSoup(response.text, 'html.parser')

	find_a = soup.find('a')['onclick']

	codigoTurmaClasse = find_a.split('(')[1].split(')')[0].split(', ')[1]
	codigoQuadroResumo = find_a.split('(')[1].split(')')[0].split(', ')[2]
	codigoOperacao = find_a.split('(')[1].split(')')[0].split(', ')[3]
	codigoEscola = soup.find(id='txtCodigoEscola')['value']

	response = context.session.post('https://sed.educacao.sp.gov.br/NCA/ColetaTurma/TurmaClasseEstadual/VisualizarTurmaClasse',
		data={
			'anoLetivo': ano_letivo,
			'ceeja': 'false',
			'codigoTurmaClasse': codigoTurmaClasse,
			'codigoQuadroResumo': codigoQuadroResumo,
			'codigoOperacao': codigoOperacao,
			'ejaEad': 'false',
			'__RequestVerificationToken': context.request_verification_token,
		})
	
	soup = BeautifulSoup(response.text, 'html.parser')

	codigoFundamentoLegal = soup.find(id='hfdCodigoFundamentoLegal')['value']
	codigoFundamentoTurma = soup.find(id='hfdCodigoFundamentoTurma')['value']
	NumeroSerie = soup.find(id='hfdNumeroSerie')['value']
	codigoTipoTurno = soup.find(id='hfdCodigoTipoTurno')['value']
	codigoTurno = soup.find(id='hfdCodigoTipoEnsinoTurno')['value']
	codigoTipoClasse = soup.find(id='CodigoTipoClasse').select_one('option[selected]')['value']
	tipoEnsino = soup.find(id='hfdCodigoTipoEnsino')['value']

	print(codigoFundamentoLegal, '-', codigoFundamentoTurma, '-', NumeroSerie, '-', codigoEscola, '-', codigoTipoTurno, '-', codigoTurno, '-', codigoTipoClasse)

	response = context.session.post('https://sed.educacao.sp.gov.br/NCA/ColetaTurma/TurmaClasseEstadual/VisualizarFundamentoLegal',
		data={
			'CodigoFundamentoLegal': codigoFundamentoLegal,
			'CodigoFundamentoTurma': codigoFundamentoTurma,
			'NumeroSerie': NumeroSerie,
			'Semestre':0,
			'CodigoEscola': codigoEscola,
			'AnoLetivo':ano_letivo,
			'CodigoTipoTurno':codigoTipoTurno,
			'CodigoTurno':codigoTurno,
			'CodigoTipoClasse':codigoTipoClasse,
			'TipoEnsino':tipoEnsino,
			'__RequestVerificationToken': context.request_verification_token,
		})
	
	soup = BeautifulSoup(response.text, 'html.parser')

	trs = soup.tbody.findAll('tr')
	matriz = []
	for tr in trs:
		try:
			matriz.append({
				'componente': str(tr.findAll('td')[0].get_text(strip=True)),
				'classificacao': str(tr.findAll('td')[1].get_text(strip=True)),
				'carga_horária': str(tr.findAll('td')[2].get_text(strip=True)),
			})
		except Exception as e:
			print(f'Erro ao processar linha da matriz curricular: {e}')
			continue

	return matriz

def get_unidades(context, escola_id):
	response = context.session.get('https://sed.educacao.sp.gov.br/nca/Matricula/ConsultaMatricula/DropDownUnidadesJson',
		params=(
			('escola', escola_id),
		))

	json = response.json()

	unidades = []
	for item in json:
		unidades.append({
			'id': item['Value'],
			'nome': item['Text'],
		})

	return unidades

def get_classes(context, ano_letivo, escola_id, unidade_id):
	response = context.session.post('https://sed.educacao.sp.gov.br/NCA/matricula/ConsultaMatricula/Pesquisar',
		data={
			'__RequestVerificationToken': context.request_verification_token,
			'anoLetivo': ano_letivo,
			'codigoEscolaCIE': escola_id,
			'codigoUnidadeCIE': unidade_id,
			'tipoConsulta': 2,
		})

	soup = BeautifulSoup(response.text, 'html.parser')

	trs = soup.tbody.findAll('tr')

	classes = []
	for tr in trs:
		onclick = tr.find('a')['onclick']

		classes.append({
			# VisualizarClasse(<ano_letivo>, <escola_id>, <classe_id>)
			'id': onclick.split('(')[1].split(')')[0].split(', ')[2],
			'id_b': str(tr.find(class_='colnrClasse').string),
			'descrição': str(tr.find(class_='colTurmaDes').string),
		})

	return classes

def get_alunos_num_classe(context, ano_letivo, escola_id, classe_id):
	#print('cheguei aqui')
	response = context.session.post('https://sed.educacao.sp.gov.br/NCA/RelacaoAlunosClasse/Visualizar',
		data={
			'anoLetivo': ano_letivo,
			'codigoEscola': escola_id,
			'codigoTurma': classe_id,
			'matricula': 'false',
			'visualizar': 'true',
		})

	soup = BeautifulSoup(response.text, 'html.parser')
	trs = soup.tbody.findAll('tr')

	alunos = []
	for tr in trs:
		try:
			alunos.append({
				# movimentacaoMatricula(aluno_id, ano_letivo, classe_id, matricula_id)
				'id': str(tr['id']),
				'nome': str(tr.findAll('td')[3].get_text(strip=True)),
				'ra': str(tr.findAll('td')[4].get_text(strip=True)),
				'ra_dígito': str(tr.findAll('td')[5].get_text(strip=True)),
				'nascimento_data': datetime.strptime(str(tr.findAll('td')[7].get_text(strip=True)), "%d/%m/%Y"),
				'numero': str(tr.findAll('td')[2].get_text(strip=True)),
				'serie': str(tr.findAll('td')[1].get_text(strip=True)),
				'inicio_matricula': datetime.strptime(str(tr.findAll('td')[9].get_text(strip=True)), "%d/%m/%Y"),
				'fim_matricula': datetime.strptime(str(tr.findAll('td')[10].get_text(strip=True)), "%d/%m/%Y"),
				'situação': str(tr.findAll('td')[11].get_text(strip=True))
			})
		except Exception as e:
			print(f'Erro ao processar aluno na classe {classe_id}: {e}')
			print(tr)
			continue

	return alunos

def consulta_ficha_aluno(context, num_classe):
	response = context.session.post('https://sed.educacao.sp.gov.br/NCA/FichaAluno/ListaFichaAlunoParcial',	
		data={
			'__RequestVerificationToken': context.request_verification_token,
			'anoLetivo': 0,
			'tipoConsultaFichaAluno': 5, # 5 = Consulta por número de classe
			'numeroClasse': num_classe})
	
	soup = BeautifulSoup(response.text, 'html.parser')
	trs = soup.tbody.findAll('tr')
	codigos_alunos = {}
	for tr in trs:
		codigo_aluno = tr.findAll('a')[1]['id'].split('_')[1]
		ra_aluno = tr.findAll('td')[2].get_text(strip=True)
		codigos_alunos[ra_aluno] = codigo_aluno

	return codigos_alunos

def get_alunos_codigo(context, ano_letivo, escola_id, classe_id):
	response = context.session.post('https://sed.educacao.sp.gov.br/NCA/Matricula/ConsultaMatricula/Visualizar',
		data={
			'anoLetivo': ano_letivo,
			'codigoEscola': escola_id,
			'codigoTurma': classe_id,
			'codigoRedeEnsino':'',
			'matricula': 'true',
			'visualizar': 'false',
		})
	
	soup = BeautifulSoup(response.text, 'html.parser')
	trs = soup.tbody.findAll('tr')

	codigos_alunos = {}
	for tr in trs:
		ra_aluno = tr.findAll('td')[4].get_text(strip=True)
		codigo_aluno = tr.findAll('td')[14].find('a')['onclick'].split('(')[1].split(',')[0]
		codigos_alunos[ra_aluno] = codigo_aluno

	return codigos_alunos
		

def get_alunos(context, ano_letivo, escola_id, classe_id):
	response = context.session.post('https://sed.educacao.sp.gov.br/NCA/Matricula/ConsultaMatricula/Visualizar',
		data={
			'anoLetivo': ano_letivo,
			'codigoEscola': escola_id,
			'codigoTurma': classe_id,
			'matricula': 'true',
			'visualizar': 'false',
		})

	soup = BeautifulSoup(response.text, 'html.parser')
	trs = soup.tbody.findAll('tr')

	alunos = []
	for tr in trs:
		a = tr.select('td > a[onclick^="movimentacaoMatricula"]')[0] # ^= is starts with
		onclick = a['onclick']

		alunos.append({
			# movimentacaoMatricula(aluno_id, ano_letivo, classe_id, matricula_id)
			'id': str(onclick.split('(')[1].split(',')[0]),
			'nome': str(tr.findAll('td')[3].string.strip()),
			'ra': str(tr.findAll('td')[4].string),
			'ra_dígito': str(tr.findAll('td')[5].string),
			'nascimento_data': datetime.strptime(str(tr.findAll('td')[7].string), "%d/%m/%Y"),
			'numero': str(tr.findAll('td')[2].string),
		})

	return alunos

def get_info_aluno(context, aluno_id):

	headers = {
		'X-Requested-With': 'XMLHttpRequest',
		'Referer': 'https://sed.educacao.sp.gov.br/NCA/FichaAluno/Index'
	}

	response = context.session.post('https://sed.educacao.sp.gov.br/NCA/FichaAluno/FichaAluno',
		data={
			'codigoAluno': aluno_id,
			'editar':'false',
			'ConsultaProgramas':'False',
			'alunoCeeja':'',
			'tipoTelaCEEJA':'0'
		},
		headers=headers)

	soup = BeautifulSoup(response.text, 'html.parser')

	print('Bugado: -------------------------')
	print(soup)
	print('-------------------------')

	#print(soup.prettify())

	def achar_value(id):
		e = soup.find(id=id)
		return str(e['value']) if e else None

	def achar_checkbox(id):
		return True if soup.find(id=id, checked=True) else False

	def achar_data(id):
		v = soup.find(id=id)['value']
		return datetime.strptime(str(v[:10]), "%d/%m/%Y") if v != '' else None

	aluno = {
		'nome': achar_value("NomeAluno"),
		'nome_social': achar_value("NomeSocial"),
		'nome_afetivo': achar_value("NomeAfetivo"),
		'ra': achar_value("nrRA"),
		'ra_dígito': achar_value("nrDigRa"),
		'nascimento_data': achar_data("DtNascimento"),
		'sexo': achar_value("Sexo"),
		'raça_cor': achar_value("DescricaoRacaCor"),
		'tipo_sanguíneo': achar_value("TipoSanguineo"),
		'falecimento': achar_checkbox("Falecimento"),
		'email': achar_value("Email"),
		'email_google': achar_value("EmailGoogle"),
		'email_microsoft': achar_value("EmailMicrosoft"),
		'nome_mãe': achar_value("NomeMae"),
		'nome_pai': achar_value("NomePai"),
		'bolsa_família': achar_checkbox("BolsaFamilia"),
		'identificação_única_educacenso': achar_value("idAlunoMec"),
		'nacionalidade': achar_value("CodigoNacionalidade"),
		'nascimento_cidade': achar_value("CidadeNascimento"),
		'nascimento_uf': achar_value("UFNascimento"),
		'nascimento_país': achar_value("CodigoPaisNascimento"),
		'quilombola': achar_checkbox("Quilombo"),
		'possui_internet': achar_checkbox("INTERNETSIM"),
		'possui_computador': achar_checkbox("SmartPessoalSIM"),
		'cpf': achar_value("CpfAluno"),
		'rg': achar_value("RgAluno"),
		'rg_dígito': achar_value("DigRgAluno"),
		'rg_uf': achar_value("sgUfRg"),
		'rg_data': achar_data("dtEmisRg"),
		'cin_data': achar_data("DataEmissaoCarteiraIdentidadeNacional"),
		'rg_militar': achar_value("RgMilitarAluno"),
		'rg_militar_dígito': achar_value("DigRgMilitarAluno"),
		'nis': achar_value("NIS"),
		'sus': achar_value("NumeroCNS"),
		'entrada_no_brasil_data': achar_data("dtEntradaBrasil"),
		'certidão_data': achar_data("dtEmisRegNasc"),
		'certidão_número': achar_value("NumeroCertidaoNova"),
		'deficiente': achar_checkbox("Deficiente"),
		'endereço_cep': achar_value("EnderecoCEP"),
		'endereço_tipo': achar_value("TipoLogradouro"),
		'endereço_diferenciado': achar_value("LocalizacaoDiferenciada"),
		'endereço': achar_value("Endereco"),
		'endereço_número': achar_value("EnderecoNR"),
		'endereço_complemento': achar_value("EnderecoComplemento"),
		'endereço_bairro': achar_value("EnderecoBairro"),
		'endereço_cidade': achar_value("EnderecoCidade"),
		'endereço_uf': achar_value("EnderecoUF"),
		'endereço_latitude': achar_value("Latitude"),
		'endereço_longitude': achar_value("Longitude"),
		'cin': achar_checkbox("FlCarteiraIdentidadeNacional")
	}

	return aluno

def get_matriculas(context, aluno_id):
	response = context.session.post('https://sed.educacao.sp.gov.br/NCA/FichaAluno/ConsultarMatriculaFichaAluno',
		data={
			'codigoAluno': aluno_id,
			# consultaProgramas: "False",
			# Editar: "false",
		})

	soup = BeautifulSoup(response.text, 'html.parser')

	trs = soup.find(id="tabelaDadosMatricula").tbody.findAll('tr')

	matriculas = []
	for tr in trs:
		tds = tr.findAll('td')

		matriculas.append({
			'id': str(tds[4].string),
			# 'ano': str(tds[0].string),
			'diretoria': str(tds[1].string),
			'município': str(tds[2].string),
			'rede': str(tds[3].string),
			'escola_id': str(tds[5].string),
			'escola_nome': str(tds[6].string),
			'turno': str(tds[7].string),
			'tipo': str(tds[8].string),
			'habilidade': str(tds[9].string),
			'série': str(tds[10].string),
			'turma': str(tds[11].string),
			'data_início': datetime.strptime(str(tds[12].string.strip()[:10]), "%d/%m/%Y"),
			'data_fim': datetime.strptime(str(tds[13].string.strip()[:10]), "%d/%m/%Y"),
			'classe_id': str(tds[14].text.strip()),
			'número': str(tds[15].string) if tds[15].string.isnumeric() else "0",
			'situação': str(tds[16].string),
		})

	return matriculas

def get_transporte_indicação(context, aluno_id):
	response = context.session.post('https://sed.educacao.sp.gov.br/geo/fichaaluno/indicacao/listar',
		headers = {
			'Authorization': context.authorization,
		},
		data={
			'codigo': aluno_id,
			'editar': 'true',
			'__RequestVerificationToken': context.request_verification_token,
		})

	with open('debug.html', 'w') as f: f.write(response.text)

	json = response.json()

	return json['data'][0]['StatusTransporte'] if len(json['data']) != 0 else None

def get_info_boletim(context, aluno_ra, digito_ra, ano):
    
	headers = {
		'X-Requested-With': 'XMLHttpRequest',
		'Referer': 'https://sed.educacao.sp.gov.br/Boletim/BoletimAluno'
	}

	# pegar dados básicos do professor
	response = context.session.post(
		'https://sed.educacao.sp.gov.br/Boletim/GerarBoletimUnificado',
		data={
			'__RequestVerificationToken': context.token_boletim,
			'nrRa': str(aluno_ra),
			'nrDigRa': str(digito_ra),
			'dsUfRa': 'SP',
			'nrAnoLetivo': str(ano),
			'ehCEEJA': 'false',
		},
		headers=headers
	)
	
	try:
		with open('debug.html', 'w') as f: f.write(response.text)
		return response.json()
	except:
		print('erro!')
		print(response.text)
		print(response)
		with open('debug.html', 'w') as f: f.write(response.text)
		return 'erro!'

def get_all_matriculas(context, ano_letivo, callback=None):
	result_escolas = get_escolas(context)
	for escola in result_escolas:
		result_unidades = get_unidades(context, escola['id'])
		for unidade in result_unidades:
			result_classes = get_classes(context, ano_letivo, escola['id'], unidade['id'])
			for classe in result_classes:
				result_alunos = get_alunos(context, ano_letivo, escola['id'], classe['id'])
				for aluno in result_alunos:
					result_aluno = get_info_aluno(context, aluno['id'])
					result_matriculas = get_matriculas(context, aluno['id'])
					result_transporte_indicação = get_transporte_indicação(context, aluno['id'])

					for matricula in result_matriculas:
						final_escola = dict(escola)
						final_escola['escola_id'] = final_escola.pop('id')
						final_escola['escola_nome'] = final_escola.pop('nome')

						final_unidade = dict(unidade)
						final_unidade['unidade_id'] = final_unidade.pop('id')
						final_unidade['unidade_nome'] = final_unidade.pop('nome')

						final_classe = dict(classe)
						final_classe['classe_id'] = final_classe.pop('id')
						final_classe['classe_id_b'] = final_classe.pop('id_b')
						final_classe['classe_descrição'] = final_classe.pop('descrição')

						final_aluno = dict(aluno)
						final_aluno['aluno_id'] = final_aluno.pop('id')

						final_matricula = dict(matricula)
						final_matricula['matricula_id'] = final_matricula.pop('id')

						yield {
							**final_escola,
							**final_unidade,
							**final_classe,
							**final_aluno,
							**result_aluno,
							**final_matricula,
							'transporte_indicação': result_transporte_indicação,
						}

def get_matriz_curricular_new(context, ano_letivo, num_classe, codigo_ensino):
	response = context.session.post('https://sed.educacao.sp.gov.br/NCA/MatrizCurricular/RelatorioAcompanhamentoMatrizCurricular/PesquisarTurmasComQuadroAulas',
	data={
		'anoLetivo': ano_letivo,
		'codigoDiretoria': 20202,
		'codigoEscola': 12361,
		'codigoTipoEnsino': codigo_ensino
	})

	soup = BeautifulSoup(response.text, 'html.parser')

	trs = soup.find(id="tbRelatorio").tbody.findAll('tr')
	
	for tr in trs:
		tds = tr.findAll('td')
		if num_classe == int(tds[5].text):
			comando = tds[15].find('i')['onclick']

			parametros = re.findall(r'\d+', comando)
			#print(parametros)

			response = context.session.post('https://sed.educacao.sp.gov.br/NCA/MatrizCurricular/RelatorioAcompanhamentoMatrizCurricular/ListarQuadroAulas',
			data={
				'codigoFundamentoTurma': parametros[0],
				'codigoTurma': parametros[1]
			})

			soup_matriz = BeautifulSoup(response.text, 'html.parser')

			matriz = []

			linhas = soup_matriz.find(id="tbListaQuadroAulas").tbody.findAll('tr')
			for linha in linhas:
				colunas = linha.findAll('td')
				info = {'codigo':colunas[0].text, 'quantidade':colunas[3].text}
				matriz.append(info)

			return matriz

def forcarCadastroAtribuicao(context, info):
	response = context.session.post('https://sed.educacao.sp.gov.br/SedAtribuicao/AssociacaoProfessorClasse/Cadastrar',
	data={'__RequestVerificationToken': context.request_verification_token,
            'NumeroAnoLetivo':2026,
            'Professor.NumeroCpf':41817519883,
            'Professor.NumeroDi':1,
            'Professor.CodigoCategoria':'O',
            'Professor.CodigoCargo':5774,
            'tabelaQuadroAulas_length':10,
            'SelecaoQuadroAula':'false',
            'SelecaoQuadroAula':'false',
            'SelecaoQuadroAula':'false',
            'SelecaoQuadroAula':'true',
            'SelecaoQuadroAula':'false',
            'FlagSuplementarPei':'false',
            'FlagSubstituicao':'false',
            'CodigoTipoAtribuicaoProfessor':'Responsavel',
            'CodigoEtapaFase':6,
            'DataInicioVigencia':'2026-02-02',
            'DataFimVigencia':'2027-01-31',
            'QuadroAulasJson':'[{"CodigoQuadroAula":760685031,"CodigoDiretoria":20202,"CodigoEscola":12361,"CodigoTurma":40967493,"CodigoDisciplina":8465,"QuantidadeAulas":2}]'
	})

	soup = BeautifulSoup(response.text, 'html.parser')

	return soup