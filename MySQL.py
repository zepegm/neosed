import mysql.connector

class db:
    def __init__(self, credenciais):
        self.cred = credenciais

    def executarConsultaVetor(self, sql):
        database = mysql.connector.connect(host=self.cred['host'],
                                   user=self.cred['user'],
                                   passwd=self.cred['passwd'],
                                   db=self.cred['db'])
        
        cur = database.cursor()

        cur.execute(sql)

        result = [item[0] for item in cur.fetchall()]

        database.close()

        return result        

    def executarConsulta(self, sql):
        database = mysql.connector.connect(host=self.cred['host'],
                                   user=self.cred['user'],
                                   passwd=self.cred['passwd'],
                                   db=self.cred['db'])
        
        cur = database.cursor(dictionary=True)

        cur.execute(sql)

        result = [dict(row) for row in cur.fetchall()]
        
        #for row in cur.fetchall():
            #print(row)

        database.close()

        return result
    
    def inserirNovaTurma(self, turma):   
        
        sql = "INSERT INTO turma VALUES(" + str(turma.values()).replace("'", '').replace('"', "'")[13:-2] + ")"

        try:
            database = mysql.connector.connect(host=self.cred['host'], user=self.cred['user'], passwd=self.cred['passwd'], db=self.cred['db'])
        
            cur = database.cursor()
            cur.execute(sql)
            database.commit()

            database.close()
            return True
        except Exception as error:
            print("An exception occurred:", error) # An exception occurred: division by zero
            return False
        
    def inserirNovaTurmaIf(self, turma, vinculos):   
        
        sql = "INSERT INTO turma_if VALUES(" + str(turma.values()).replace("'", '').replace('"', "'")[13:-2] + ")"

        try:
            database = mysql.connector.connect(host=self.cred['host'], user=self.cred['user'], passwd=self.cred['passwd'], db=self.cred['db'])
        
            cur = database.cursor()

            cur.execute('DELETE FROM vinculo_if WHERE num_classe_if = %s' % turma['num_classe'])
            #database.commit()
            cur.execute(sql)

            for item in vinculos:
                cur.execute('INSERT INTO vinculo_if VALUES(%s, %s)' % (turma['num_classe'], item))

            database.commit()
            database.close()
            return True
        except Exception as error:
            print("An exception occurred:", error) # An exception occurred: division by zero
            return False        
        
    def alterarTurma(self, turma):
        sql = 'UPDATE TURMA SET '

        for key, value in turma.items():
            if (key != 'num_classe'):
                sql += '%s = %s, ' % (key, value)

        sql = sql[:-2] + ' WHERE num_classe = %s' % turma['num_classe']
        
        try:
            database = mysql.connector.connect(host=self.cred['host'], user=self.cred['user'], passwd=self.cred['passwd'], db=self.cred['db'])
        
            cur = database.cursor()
            cur.execute(sql)
            database.commit()

            database.close()
            return True
        except Exception as error:
            print("An exception occurred:", error) # An exception occurred: division by zero
            return False
        
    def alterarTurmaIf(self, turma, vinculos):
        sql = 'UPDATE turma_if SET '

        for key, value in turma.items():
            if (key != 'num_classe'):
                sql += '%s = %s, ' % (key, value)

        sql = sql[:-2] + ' WHERE num_classe = %s' % turma['num_classe']
        
        try:
            database = mysql.connector.connect(host=self.cred['host'], user=self.cred['user'], passwd=self.cred['passwd'], db=self.cred['db'])
        
            cur = database.cursor()

            cur.execute('DELETE FROM vinculo_if WHERE num_classe_if = %s' % turma['num_classe'])
            #database.commit()
            cur.execute(sql)

            for item in vinculos:
                cur.execute('INSERT INTO vinculo_if VALUES(%s, %s)' % (turma['num_classe'], item))

            database.commit()
            database.close()
            return True
        except Exception as error:
            print("An exception occurred:", error) # An exception occurred: division by zero
            return False        
        
    def salvarVinculoProfs(self, info):
        try:
            database = mysql.connector.connect(host=self.cred['host'], user=self.cred['user'], passwd=self.cred['passwd'], db=self.cred['db'])
            cur = database.cursor()

            cur.execute('DELETE FROM vinculo_turma_prof WHERE id_turma = %s' % info['num_classe'])
            database.commit()

            for item in info['profs']:
                sql = "INSERT INTO vinculo_turma_prof VALUES(%s, %s)" % (info['num_classe'], item)
                cur.execute(sql)


            database.commit()
            database.close()
            return True
        except Exception as error:
            print("An exception occurred:", error) # An exception occurred: division by zero
            return False        


    def salvarNotas(self, info):
        try:
            database = mysql.connector.connect(host=self.cred['host'], user=self.cred['user'], passwd=self.cred['passwd'], db=self.cred['db'])
            cur = database.cursor()

            cur.execute('DELETE FROM vinculo_prof_disc WHERE num_classe = %s and bimestre = %s' % (info['num_classe'], info['bim']))
            database.commit()

            for item in info['vinculo']:
                sql = "INSERT INTO vinculo_prof_disc VALUES(%s, %s, %s, %s, %s)" % (info['num_classe'], item['prof'], info['bim'], item['disc'], item['AD'])
                cur.execute(sql)


            cur.execute('DELETE FROM notas WHERE num_classe = %s and bimestre = %s' % (info['num_classe'], info['bim']))
            database.commit()            

            for item in info['notas']:
                sql = "INSERT INTO notas VALUES(%s, %s, %s, %s, '%s', %s, %s)" % (info['bim'], info['num_classe'], item['ra'], item['disc'], item['N'], item['F'], item['AC'])
                cur.execute(sql)

            database.commit()
            database.close()
            return True
        except Exception as error:
            print("An exception occurred:", error) # An exception occurred: division by zero
            return False  

    def importarDadosTurma(self, turma):

        try:
            database = mysql.connector.connect(host=self.cred['host'], user=self.cred['user'], passwd=self.cred['passwd'], db=self.cred['db'])
            cur = database.cursor()

            if turma[0]['serie'] == "0":
                #print('to aqui')
                cur.execute('DELETE FROM vinculo_alunos_if WHERE num_classe_if = %s' % turma[0]['num_classe'])
                database.commit()

                for item in turma:
                    sql = "INSERT INTO aluno(ra, digito_ra, rm, nome, nascimento, sexo, rg, cpf) VALUES(%s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE rm=%s, nome=%s, nascimento=%s, sexo=%s, rg=%s, cpf=%s" % (item['ra'], item['digito'], item['rm'], item['nome'], item['nascimento'], item['sexo'], item['rg'], item['cpf'].replace(".", "").replace("-", ""), item['rm'], item['nome'], item['nascimento'], item['sexo'], item['rg'], item['cpf'].replace(".", "").replace("-", ""))                    
                    cur.execute(sql)

                    sql = "INSERT INTO vinculo_alunos_if VALUES(%s, %s, %s, %s, %s, %s)" % (item['ra'], item['num_classe'], item['num_chamada'], item['matricula'], item['fim_mat'], item['situacao'])
                    cur.execute(sql)

            else:
                cur.execute('DELETE FROM vinculo_alunos_turmas WHERE num_classe = %s' % turma[0]['num_classe'])
                database.commit()

                for item in turma:
                    sql = "INSERT INTO aluno(ra, digito_ra, rm, nome, nascimento, sexo, rg, cpf) VALUES(%s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE rm=%s, nome=%s, nascimento=%s, sexo=%s, rg=%s, cpf=%s" % (item['ra'], item['digito'], item['rm'], item['nome'], item['nascimento'], item['sexo'], item['rg'], item['cpf'].replace(".", "").replace("-", ""), item['rm'], item['nome'], item['nascimento'], item['sexo'], item['rg'], item['cpf'].replace(".", "").replace("-", ""))                
                    cur.execute(sql)

                    sql = "INSERT INTO vinculo_alunos_turmas VALUES(%s, %s, %s, %s, %s, %s, %s)" % (item['ra'], item['num_classe'], item['num_chamada'], item['serie'], item['matricula'], item['fim_mat'], item['situacao'])
                    cur.execute(sql)

            database.commit()
            database.close()
            return True
        except Exception as error:
            print("An exception occurred:", error) # An exception occurred: division by zero
            return False
        

    def insertOrUpdate(self, dados, tabela):
            
        try:
            database = mysql.connector.connect(host=self.cred['host'], user=self.cred['user'], passwd=self.cred['passwd'], db=self.cred['db'])
            cur = database.cursor()

            keys = ""
            data = ""
            update = ""

            for item in dados:
                keys += item + ", "
                data += dados[item] + ", "

                if item != 'codigo_disciplina':
                    update += item + "=" + dados[item] + ", "

            sql = "INSERT INTO " + tabela + " (" + keys[:-2] + ") VALUES(" + data[:-2] + ") ON DUPLICATE KEY UPDATE " + update[:-2]

            print(sql)

            cur.execute(sql)
            database.commit()
            database.close()

            return True

        except Exception as error:
            print("An exception occurred:", error) # An exception occurred: division by zero
            return False            


    def salvarDificuldades(self, lista):
        
        num_classe = lista[0]['num_classe']
        bimestre = lista[0]['bimestre']

        try:
            database = mysql.connector.connect(host=self.cred['host'], user=self.cred['user'], passwd=self.cred['passwd'], db=self.cred['db'])
            cur = database.cursor()        

            cur.execute('DELETE FROM alunos_dificuldades WHERE num_classe = %s and bimestre = %s' % (num_classe, bimestre))
            database.commit()

            for item in lista:
                cur.execute('INSERT INTO alunos_dificuldades VALUES(%s, %s, %s, %s)' % (item['ra'], item['item'], item['bimestre'], item['num_classe']))

            database.commit()

            return True

        except Exception as error:
            print("An exception occurred:", error) # An exception occurred: division by zero
            return False            