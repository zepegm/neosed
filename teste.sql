SELECT distinct
	inicio, fim, concat(TIME_FORMAT(inicio, "%H:%i"), ' - ',  TIME_FORMAT(fim, "%H:%i")) as horario,
    CASE WHEN inicio < '12:00:00' THEN 'Manhã' WHEN inicio < '19:00:00' THEN 'Tarde' ELSE 'Noite' END as periodo,
    ifnull( (select seg from horario_livro_ponto where cpf_professor = 99474824649 and DATE_FORMAT(horario_livro_ponto.inicio, '%H:%i') = TIME_FORMAT(hora_aulas.inicio, "%H:%i")), IFNULL((SELECT turma.apelido from grade inner join matriz_curricular on matriz_curricular.disc_disciplina = grade.disciplina and (matriz_curricular.cpf_professor = 99474824649 or matriz_curricular.cpf_professor_2 = 99474824649) inner join turma on turma.num_classe = matriz_curricular.num_classe and grade.num_classe = matriz_curricular.num_classe  where grade.pos = hora_aulas.pos and semana = 2 and turma.ano = hora_aulas.ano), '')) as seg,
    ifnull( (select ter from horario_livro_ponto where cpf_professor = 99474824649 and DATE_FORMAT(horario_livro_ponto.inicio, '%H:%i') = TIME_FORMAT(hora_aulas.inicio, "%H:%i")), IFNULL((SELECT turma.apelido from grade inner join matriz_curricular on matriz_curricular.disc_disciplina = grade.disciplina and (matriz_curricular.cpf_professor = 99474824649 or matriz_curricular.cpf_professor_2 = 99474824649) inner join turma on turma.num_classe = matriz_curricular.num_classe and grade.num_classe = matriz_curricular.num_classe  where grade.pos = hora_aulas.pos and semana = 3 and turma.ano = hora_aulas.ano), '') ) as ter, 
    ifnull( (select qua from horario_livro_ponto where cpf_professor = 99474824649 and DATE_FORMAT(horario_livro_ponto.inicio, '%H:%i') = TIME_FORMAT(hora_aulas.inicio, "%H:%i")), IFNULL((SELECT turma.apelido from grade inner join matriz_curricular on matriz_curricular.disc_disciplina = grade.disciplina and (matriz_curricular.cpf_professor = 99474824649 or matriz_curricular.cpf_professor_2 = 99474824649) inner join turma on turma.num_classe = matriz_curricular.num_classe and grade.num_classe = matriz_curricular.num_classe  where grade.pos = hora_aulas.pos and semana = 4 and turma.ano = hora_aulas.ano), '') ) as qua, 
    ifnull( (select qui from horario_livro_ponto where cpf_professor = 99474824649 and DATE_FORMAT(horario_livro_ponto.inicio, '%H:%i') = TIME_FORMAT(hora_aulas.inicio, "%H:%i")), IFNULL((SELECT turma.apelido from grade inner join matriz_curricular on matriz_curricular.disc_disciplina = grade.disciplina and (matriz_curricular.cpf_professor = 99474824649 or matriz_curricular.cpf_professor_2 = 99474824649) inner join turma on turma.num_classe = matriz_curricular.num_classe and grade.num_classe = matriz_curricular.num_classe  where grade.pos = hora_aulas.pos and semana = 5 and turma.ano = hora_aulas.ano), '') ) as qui, 
    ifnull( (select sex from horario_livro_ponto where cpf_professor = 99474824649 and DATE_FORMAT(horario_livro_ponto.inicio, '%H:%i') = TIME_FORMAT(hora_aulas.inicio, "%H:%i")), IFNULL((SELECT turma.apelido from grade inner join matriz_curricular on matriz_curricular.disc_disciplina = grade.disciplina and (matriz_curricular.cpf_professor = 99474824649 or matriz_curricular.cpf_professor_2 = 99474824649) inner join turma on turma.num_classe = matriz_curricular.num_classe and grade.num_classe = matriz_curricular.num_classe  where grade.pos = hora_aulas.pos and semana = 6 and turma.ano = hora_aulas.ano), '') ) as sex, 
    ifnull( (select sab from horario_livro_ponto where cpf_professor = 99474824649 and DATE_FORMAT(horario_livro_ponto.inicio, '%H:%i') = TIME_FORMAT(hora_aulas.inicio, "%H:%i")), IFNULL((SELECT turma.apelido from grade inner join matriz_curricular on matriz_curricular.disc_disciplina = grade.disciplina and (matriz_curricular.cpf_professor = 99474824649 or matriz_curricular.cpf_professor_2 = 99474824649) inner join turma on turma.num_classe = matriz_curricular.num_classe and grade.num_classe = matriz_curricular.num_classe  where grade.pos = hora_aulas.pos and semana = 7 and turma.ano = hora_aulas.ano), '') ) as sab, 
    ifnull( (select dom from horario_livro_ponto where cpf_professor = 99474824649 and DATE_FORMAT(horario_livro_ponto.inicio, '%H:%i') = TIME_FORMAT(hora_aulas.inicio, "%H:%i")), IFNULL((SELECT turma.apelido from grade inner join matriz_curricular on matriz_curricular.disc_disciplina = grade.disciplina and (matriz_curricular.cpf_professor = 99474824649 or matriz_curricular.cpf_professor_2 = 99474824649) inner join turma on turma.num_classe = matriz_curricular.num_classe and grade.num_classe = matriz_curricular.num_classe  where grade.pos = hora_aulas.pos and semana = 1 and turma.ano = hora_aulas.ano), '') ) as dom
FROM hora_aulas 
inner join grade on grade.pos = hora_aulas.pos 
inner join matriz_curricular on matriz_curricular.disc_disciplina = grade.disciplina and (matriz_curricular.cpf_professor = 99474824649 or matriz_curricular.cpf_professor_2 = 99474824649) 
WHERE grade.num_classe in (select distinct num_classe from matriz_curricular where cpf_professor = 99474824649 or cpf_professor_2 = 99474824649) and hora_aulas.tipo_ensino in (select distinct turma.tipo_ensino from matriz_curricular inner join turma on matriz_curricular.num_classe = turma.num_classe where (cpf_professor = 99474824649 or cpf_professor_2 = 99474824649))

UNION

select
	CONVERT(inicio, TIME) as inicio, CONVERT(fim, TIME) as fim,
    concat(TIME_FORMAT(inicio, "%H:%i"), ' - ',  TIME_FORMAT(fim, "%H:%i")) as horario,
    periodo_livro_ponto.descricao as periodo,
    ifnull(seg, '') as seg, ifnull(ter, '') as ter, ifnull(qua, '') as qua, ifnull(qui, '') as qui, ifnull(sex, '') as sex, ifnull(sab, '') as sáb, ifnull(dom, '') as dom 
from horario_livro_ponto
inner join periodo_livro_ponto on periodo_livro_ponto.id = horario_livro_ponto.periodo
where cpf_professor = 99474824649 and CONVERT(inicio, TIME) not in (
    select distinct 
		hora_aulas.inicio
	FROM hora_aulas
    inner join grade on grade.pos = hora_aulas.pos
    inner join matriz_curricular on matriz_curricular.disc_disciplina = grade.disciplina and (matriz_curricular.cpf_professor = 99474824649 or matriz_curricular.cpf_professor_2 = 99474824649)
    WHERE grade.num_classe in (select distinct num_classe from matriz_curricular where cpf_professor = 99474824649 or cpf_professor_2 = 99474824649) and hora_aulas.tipo_ensino in (select distinct turma.tipo_ensino from matriz_curricular inner join turma on matriz_curricular.num_classe = turma.num_classe where cpf_professor = 99474824649)
)

ORDER BY inicio