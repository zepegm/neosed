from datetime import datetime, time, timedelta
from hashlib import sha256, md5

meses = ['JANEIRO', 'FEVEREIRO', 'MARÇO', 'ABRIL', 'MAIO', 'JUNHO', 'JULHO', 'AGOSTO', 'SETEMBRO', 'OUTUBRO', 'NOVEMBRO', 'DEZEMBRO']
series_fund = {9:'6º ano', 10:'7º ano', 11:'8º ano', 12:'9º ano'}
situacoes = {'ATIVO':1, 'BXTR':2, 'TRAN':2, 'REMA':3, 'NCFP':5, 'NCOM':5, 'CONCL':8, 'APROVADO':6, 'RETIDO FREQ.':10, 'RETIDO REND.':10, 'RECL':15, 'ENCERRADA':16}

def fmt_hhmm(x):
    if x is None:
        return ''
    if isinstance(x, timedelta):
        total = int(x.total_seconds())
        h = (total // 3600) % 24
        m = (total % 3600) // 60
        return f'{h:02d}:{m:02d}'
    if isinstance(x, time):
        return f'{x.hour:02d}:{x.minute:02d}'
    if isinstance(x, datetime):
        return x.strftime('%H:%M')
    if isinstance(x, str):
        h, m, *_ = x.split(':')
        return f'{int(h):02d}:{int(m):02d}'
    raise TypeError(f'Tipo não suportado: {type(x)}')

def hsl_for_key(key, sat=70, light_bg=88, light_bd=50):
    """gera bg e border em HSL a partir de uma chave estável (cpf ou cpf/cpf)"""
    h = int(md5(str(key).encode()).hexdigest(), 16) % 360
    return {
        'bg': f'hsl({h}, {sat}%, {light_bg}%)',
        'bd': f'hsl({h}, {sat-10}%, {light_bd}%)'
    }

def to_minutes(t):
    """Aceita datetime.time, datetime.timedelta ou 'HH:MM[:SS]' e devolve minutos inteiros."""
    if t is None:
        return None
    if isinstance(t, timedelta):
        return int(t.total_seconds() // 60)
    if isinstance(t, time):
        return t.hour * 60 + t.minute
    if isinstance(t, str):
        h, m, *_ = t.split(':')
        return int(h) * 60 + int(m)
    raise TypeError(f"Tipo de hora não suportado: {type(t)} {t!r}")


def montar_grade_prof(rows):
    # slots únicos e ordenados
    slots = sorted({ (r['inicio'], r['fim']) for r in rows }, key=lambda t: (t[0], t[1]))
    dias = [2,3,4,5,6]  # Seg..Sex (ajuste se quiser dom/sáb)
    grid = []
    for ini, fim in slots:
        linha = {'horario': f"{fmt_hhmm(ini)} - {fmt_hhmm(fim)}"}
        for s in dias:
            lbl = next((r['label'] for r in rows
                        if r['inicio']==ini and r['fim']==fim and r['semana']==s), '')
            linha[s] = lbl or '-'
        grid.append(linha)
    # total de aulas (conta células com label diferente de vazio/“-”)
    total = sum(1 for r in rows if r['label'] and r['label'] not in ('-', 'Atpc', 'SLN', 'REAN', 'PATN'))
    return grid, total

def montar_eventos(rows):
    # exemplo de preparo dos blocos
    PX_PER_MIN = 1.6  # 60 minutos = 72px (ajuste a gosto)

    mins = [to_minutes(r['inicio']) for r in rows if r.get('inicio') is not None]
    maxs = [to_minutes(r['fim'])    for r in rows if r.get('fim')    is not None]

    day_start = min(mins) if mins else 7*60
    day_end   = max(maxs) if maxs else 16*60

    #dias = {2:'Seg',3:'Ter',4:'Qua',5:'Qui',6:'Sex',7:'Sáb',1:'Dom'}
    dias = {2:'Segunda-feira',3:'Terça-feira',4:'Quarta-feira',5:'Quinta-feira',6:'Sexta-feira'}
    timeline = {d:{} for d in dias.values()}

    # depois de buscar 'rows' do banco:
    keys = {r['prof_key'] for r in rows if r['prof_key']}
    palette = {k: hsl_for_key(k) for k in keys}
    default_color = {'bg': "#f8ffa6", 'bd': "#C9AB00"}  # quando não houver professor

    for r in rows:
        ini = to_minutes(r['inicio']); fim = to_minutes(r['fim'])
        if ini is None or fim is None or fim <= ini: continue
        dia = dias[r['semana']]; turma = r['turma']
        top = (ini - day_start) * PX_PER_MIN; height = (fim - ini) * PX_PER_MIN
        col = palette.get(r['prof_key'], default_color)
        timeline[dia].setdefault(turma, []).append({
            'label': r['label'],               # "TEC (Fernando)" ou "TEC"
            'title': r.get('prof_nome') or '', # tooltip
            'top': round(top,1),
            'height': round(height,1),
            'bg': col['bg'],
            'bd': col['bd'],
            'inicio': fmt_hhmm(r['inicio']) if r.get('inicio') else '',
            'fim': fmt_hhmm(r['fim']) if r.get('fim') else '',
        })

    # (opcional) legenda por professor
    legend = []
    seen = set()
    for r in rows:
        k = r['prof_key']
        if not k or k in seen: continue
        seen.add(k)
        legend.append({'name': r['prof_nome'], 'bg': palette[k]['bg'], 'bd': palette[k]['bd']})        

    return {'timeline': timeline, 'legenda': legend,
            'axis': {'start': day_start, 'end': day_end, 'px_per_min': PX_PER_MIN}}

def getSituacao(descricao):
    return situacoes[descricao]

def converterLista(lista):
    texto = ""
    aux = 0
    on = False

    for item in lista:
        if (texto == ''):
            texto += str(item)
            aux = int(item)
        else:
            if (on):
                if (int(item) != (aux + 1)):
                    on = False
                    texto += str(aux) + "," + str(item)
            else:
                if (int(item) == (aux + 1)):
                    on = True
                    texto += "-"
                else:
                    texto += "," + str(item)

            aux = int(item)

    if (on):
        texto += str(aux)

    return texto

def getMes(mes):
    id = int(mes) - 1
    return meses[id]


def hojePorExtenso():
    hoje = datetime.today()

    return "%s de %s de %s" % (hoje.day, meses[hoje.month - 1].lower(), hoje.year)

def getAnoFund(serie):
    return series_fund[serie]

def converterDataMySQL(data_original):
    return data_original[-4:] + '-' + data_original[3:5] + '-' +  data_original[:2]

def encriptar(value):
    return sha256(value.encode('utf-8')).hexdigest()

def extrair_numeros(string):
    return ''.join([char for char in string if char.isdigit()])