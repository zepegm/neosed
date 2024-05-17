from excel import xls
from MySQL import db

def my_sql():
    banco = db({'host':"localhost",    # your host, usually localhost
                'user':"root",         # your username
                'passwd':"Yasmin",  # your password
                'db':"neosed"})
    
    turmas_if = banco.executarConsulta('select num_classe_if from vinculo_if where num_classe_em = 280178138')

    if len(turmas_if) > 1: # implica que existe Itinerário
        print('a')

my_sql()