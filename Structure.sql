-- MySQL dump 10.13  Distrib 8.0.43, for Win64 (x86_64)
--
-- Host: localhost    Database: neosed
-- ------------------------------------------------------
-- Server version	8.0.43

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `afastamento_livro_ponto`
--

DROP TABLE IF EXISTS `afastamento_livro_ponto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `afastamento_livro_ponto` (
  `id` int NOT NULL,
  `descricao` varchar(100) NOT NULL,
  `prefixo` varchar(45) DEFAULT NULL,
  `ua` tinyint DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `afastamentos_ponto_adm`
--

DROP TABLE IF EXISTS `afastamentos_ponto_adm`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `afastamentos_ponto_adm` (
  `cpf` bigint NOT NULL,
  `inicio` date NOT NULL,
  `fim` date NOT NULL,
  `descricao` varchar(100) NOT NULL,
  PRIMARY KEY (`cpf`,`fim`,`inicio`),
  CONSTRAINT `cpf_afs` FOREIGN KEY (`cpf`) REFERENCES `funcionario_livro_ponto` (`cpf`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `aluno`
--

DROP TABLE IF EXISTS `aluno`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `aluno` (
  `ra` int NOT NULL,
  `digito_ra` char(1) NOT NULL,
  `rm` smallint DEFAULT NULL,
  `nome` varchar(200) NOT NULL,
  `nascimento` date NOT NULL,
  `sexo` char(1) NOT NULL,
  `rg` varchar(45) DEFAULT NULL,
  `cpf` bigint DEFAULT NULL,
  PRIMARY KEY (`ra`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `alunos_dificuldades`
--

DROP TABLE IF EXISTS `alunos_dificuldades`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alunos_dificuldades` (
  `ra` int NOT NULL,
  `dificuldade` int NOT NULL,
  `bimestre` smallint NOT NULL,
  `num_classe` int NOT NULL,
  KEY `ra_dificuldad_idx` (`ra`),
  KEY `dificuldade_idx` (`dificuldade`),
  KEY `classe_dif_idx` (`num_classe`),
  CONSTRAINT `classe_dif` FOREIGN KEY (`num_classe`) REFERENCES `turma` (`num_classe`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `dificuldade` FOREIGN KEY (`dificuldade`) REFERENCES `dificuldades` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `ra_dificuldade` FOREIGN KEY (`ra`) REFERENCES `aluno` (`ra`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `area_matriz`
--

DROP TABLE IF EXISTS `area_matriz`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `area_matriz` (
  `id` smallint NOT NULL AUTO_INCREMENT,
  `descricao` varchar(45) DEFAULT NULL,
  `desc_curta` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `aulas_outra_ue_livro_ponto`
--

DROP TABLE IF EXISTS `aulas_outra_ue_livro_ponto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `aulas_outra_ue_livro_ponto` (
  `cpf_professor` bigint NOT NULL,
  `semana` varchar(3) NOT NULL,
  `qtd` tinyint NOT NULL,
  PRIMARY KEY (`semana`,`cpf_professor`),
  KEY `professor_outras_idx` (`cpf_professor`),
  CONSTRAINT `cpf_professor_outra_ue` FOREIGN KEY (`cpf_professor`) REFERENCES `professor_livro_ponto` (`cpf`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `calendario`
--

DROP TABLE IF EXISTS `calendario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `calendario` (
  `ano` int NOT NULL,
  `1bim_inicio` date DEFAULT NULL,
  `1bim_fim` date DEFAULT NULL,
  `2bim_inicio` date DEFAULT NULL,
  `2bim_fim` date DEFAULT NULL,
  `3bim_inicio` date DEFAULT NULL,
  `3bim_fim` date DEFAULT NULL,
  `4bim_inicio` date DEFAULT NULL,
  `4bim_fim` date DEFAULT NULL,
  PRIMARY KEY (`ano`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `calendario_ponto`
--

DROP TABLE IF EXISTS `calendario_ponto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `calendario_ponto` (
  `id` int NOT NULL AUTO_INCREMENT,
  `descricao` varchar(45) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cargos_livro_ponto`
--

DROP TABLE IF EXISTS `cargos_livro_ponto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cargos_livro_ponto` (
  `id` int NOT NULL AUTO_INCREMENT,
  `descricao` varchar(45) NOT NULL,
  `tipo` smallint DEFAULT '1',
  `cod_sed` int DEFAULT NULL,
  `abv` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cat_letivo`
--

DROP TABLE IF EXISTS `cat_letivo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cat_letivo` (
  `id` int NOT NULL AUTO_INCREMENT,
  `descricao` varchar(45) DEFAULT NULL,
  `qtd_letivo` smallint DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `categoria_itinerario`
--

DROP TABLE IF EXISTS `categoria_itinerario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `categoria_itinerario` (
  `id` int NOT NULL AUTO_INCREMENT,
  `descricao` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `categoria_livro_ponto`
--

DROP TABLE IF EXISTS `categoria_livro_ponto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `categoria_livro_ponto` (
  `id` int NOT NULL AUTO_INCREMENT,
  `descricao` varchar(45) NOT NULL,
  `letra` varchar(1) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `classificacao`
--

DROP TABLE IF EXISTS `classificacao`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `classificacao` (
  `id` int NOT NULL,
  `descricao` varchar(45) NOT NULL,
  `abv` varchar(45) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `conceito_final`
--

DROP TABLE IF EXISTS `conceito_final`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `conceito_final` (
  `num_classe` int NOT NULL,
  `ra_aluno` int NOT NULL,
  `disciplina` int NOT NULL,
  `media` varchar(2) NOT NULL,
  PRIMARY KEY (`ra_aluno`,`disciplina`,`num_classe`),
  KEY `disc_final_idx` (`disciplina`),
  CONSTRAINT `disc_final` FOREIGN KEY (`disciplina`) REFERENCES `disciplinas` (`codigo_disciplina`),
  CONSTRAINT `ra_aluno_final` FOREIGN KEY (`ra_aluno`) REFERENCES `aluno` (`ra`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `config`
--

DROP TABLE IF EXISTS `config`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `config` (
  `id_config` varchar(100) NOT NULL,
  `valor` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id_config`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dificuldades`
--

DROP TABLE IF EXISTS `dificuldades`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dificuldades` (
  `id` int NOT NULL AUTO_INCREMENT,
  `descricao` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `disciplinas`
--

DROP TABLE IF EXISTS `disciplinas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `disciplinas` (
  `codigo_disciplina` int NOT NULL,
  `descricao` varchar(100) NOT NULL,
  `abv` varchar(45) NOT NULL,
  `classificacao` int NOT NULL,
  PRIMARY KEY (`codigo_disciplina`),
  KEY `classificacao_idx` (`classificacao`),
  CONSTRAINT `classificacao` FOREIGN KEY (`classificacao`) REFERENCES `classificacao` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `duracao`
--

DROP TABLE IF EXISTS `duracao`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `duracao` (
  `id` int NOT NULL AUTO_INCREMENT,
  `descricao` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `eventos_calendario`
--

DROP TABLE IF EXISTS `eventos_calendario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `eventos_calendario` (
  `data_inicial` date NOT NULL,
  `data_final` date NOT NULL,
  `evento` int NOT NULL,
  `descricao` varchar(100) DEFAULT NULL,
  `instancia_calendario` int NOT NULL DEFAULT '1',
  KEY `evento_dia_idx` (`evento`),
  KEY `calendario_inst_idx` (`instancia_calendario`),
  KEY `ix_eventos_inst_data` (`instancia_calendario`,`data_inicial`,`data_final`),
  CONSTRAINT `calendario_inst` FOREIGN KEY (`instancia_calendario`) REFERENCES `calendario_ponto` (`id`),
  CONSTRAINT `evento_dia` FOREIGN KEY (`evento`) REFERENCES `cat_letivo` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `eventos_funcionais`
--

DROP TABLE IF EXISTS `eventos_funcionais`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `eventos_funcionais` (
  `id` smallint NOT NULL AUTO_INCREMENT,
  `descricao` varchar(45) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `frequencia`
--

DROP TABLE IF EXISTS `frequencia`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `frequencia` (
  `ra_aluno` int NOT NULL,
  `date` date NOT NULL,
  `freq` tinyint NOT NULL,
  PRIMARY KEY (`ra_aluno`,`date`),
  CONSTRAINT `ra_aluno_freq` FOREIGN KEY (`ra_aluno`) REFERENCES `aluno` (`ra`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `funcionario_livro_ponto`
--

DROP TABLE IF EXISTS `funcionario_livro_ponto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `funcionario_livro_ponto` (
  `cpf` bigint NOT NULL,
  `nome` varchar(200) NOT NULL,
  `rg` varchar(45) NOT NULL,
  `digito` varchar(1) DEFAULT NULL,
  `cargo` int NOT NULL,
  `horario` varchar(100) NOT NULL,
  `intervalo` varchar(100) NOT NULL,
  `estudante` tinyint NOT NULL,
  `plantao` tinyint NOT NULL,
  `ativo` tinyint DEFAULT '1',
  `di` smallint DEFAULT NULL,
  `categoria` int DEFAULT NULL,
  `nascimento` date DEFAULT NULL,
  `rs` int DEFAULT NULL,
  `pv` smallint DEFAULT NULL,
  `FNREF` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`cpf`),
  KEY `cargo_idx_adm` (`cargo`),
  KEY `categoria_adm_idx` (`categoria`),
  CONSTRAINT `cargo_adm` FOREIGN KEY (`cargo`) REFERENCES `cargos_livro_ponto` (`id`),
  CONSTRAINT `categoria_adm` FOREIGN KEY (`categoria`) REFERENCES `categoria_livro_ponto` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `grade`
--

DROP TABLE IF EXISTS `grade`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `grade` (
  `num_classe` int NOT NULL,
  `pos` smallint NOT NULL,
  `semana` smallint NOT NULL,
  `disciplina` int DEFAULT NULL,
  PRIMARY KEY (`num_classe`,`pos`,`semana`),
  KEY `disc_idx` (`disciplina`),
  KEY `ix_grade_classe` (`num_classe`,`semana`,`pos`,`disciplina`),
  KEY `idx_grade_turma_pos` (`num_classe`,`pos`),
  KEY `idx_grade_turma_sem` (`num_classe`,`semana`,`pos`),
  KEY `idx_grade_turma_sem_pos` (`num_classe`,`semana`,`pos`),
  CONSTRAINT `disc_grade` FOREIGN KEY (`disciplina`) REFERENCES `disciplinas` (`codigo_disciplina`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `num_classe_grade` FOREIGN KEY (`num_classe`) REFERENCES `turma` (`num_classe`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Temporary view structure for view `grade_horario_vw`
--

DROP TABLE IF EXISTS `grade_horario_vw`;
/*!50001 DROP VIEW IF EXISTS `grade_horario_vw`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `grade_horario_vw` AS SELECT 
 1 AS `num_classe`,
 1 AS `semana`,
 1 AS `pos`,
 1 AS `disc_abv`,
 1 AS `inicio`,
 1 AS `fim`,
 1 AS `prof_nome`,
 1 AS `prof_key`,
 1 AS `label`*/;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `hora_aulas`
--

DROP TABLE IF EXISTS `hora_aulas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `hora_aulas` (
  `ano` int NOT NULL,
  `tipo_ensino` int NOT NULL,
  `pos` smallint DEFAULT NULL,
  `inicio` time DEFAULT NULL,
  `fim` time DEFAULT NULL,
  UNIQUE KEY `uq_hora_aulas_pos` (`ano`,`tipo_ensino`,`pos`),
  KEY `horario_tipo_ensino_idx` (`tipo_ensino`),
  KEY `ix_hora_aulas` (`ano`,`tipo_ensino`,`pos`,`inicio`),
  CONSTRAINT `horario_tipo_ensino` FOREIGN KEY (`tipo_ensino`) REFERENCES `tipo_ensino` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `horario_livro_ponto`
--

DROP TABLE IF EXISTS `horario_livro_ponto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `horario_livro_ponto` (
  `cpf_professor` bigint NOT NULL,
  `periodo` int NOT NULL,
  `inicio` datetime NOT NULL,
  `fim` datetime NOT NULL,
  `seg` varchar(4) DEFAULT NULL,
  `ter` varchar(4) DEFAULT NULL,
  `qua` varchar(4) DEFAULT NULL,
  `qui` varchar(4) DEFAULT NULL,
  `sex` varchar(4) DEFAULT NULL,
  `sab` varchar(4) DEFAULT NULL,
  `dom` varchar(4) DEFAULT NULL,
  PRIMARY KEY (`cpf_professor`,`periodo`,`inicio`,`fim`),
  KEY `periodo_idx` (`periodo`),
  CONSTRAINT `periodo` FOREIGN KEY (`periodo`) REFERENCES `periodo_livro_ponto` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `horario_turma`
--

DROP TABLE IF EXISTS `horario_turma`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `horario_turma` (
  `num_classe` int NOT NULL,
  `pos` smallint NOT NULL,
  `inicio` time NOT NULL,
  `fim` time NOT NULL,
  PRIMARY KEY (`num_classe`,`pos`),
  KEY `idx_ht_turma_pos` (`num_classe`,`pos`),
  CONSTRAINT `fk_ht_turma` FOREIGN KEY (`num_classe`) REFERENCES `turma` (`num_classe`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `jornada_livro_ponto`
--

DROP TABLE IF EXISTS `jornada_livro_ponto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `jornada_livro_ponto` (
  `id` int NOT NULL AUTO_INCREMENT,
  `descricao` varchar(45) NOT NULL,
  `qtd` tinyint DEFAULT NULL,
  `letra` char(1) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `licenca_professores`
--

DROP TABLE IF EXISTS `licenca_professores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `licenca_professores` (
  `cpf` bigint NOT NULL,
  `inicio` date NOT NULL,
  `fim` date NOT NULL,
  `descricao` varchar(200) NOT NULL,
  `id_tipo` int NOT NULL,
  PRIMARY KEY (`cpf`,`inicio`,`fim`),
  KEY `id_tipo_licenca_idx` (`id_tipo`),
  CONSTRAINT `id_tipo_licenca` FOREIGN KEY (`id_tipo`) REFERENCES `tipo_licenca_professores` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `matriz_curricular`
--

DROP TABLE IF EXISTS `matriz_curricular`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `matriz_curricular` (
  `num_classe` int NOT NULL,
  `disc_disciplina` int NOT NULL,
  `area` smallint NOT NULL,
  `tipo` smallint NOT NULL,
  `qtd_aulas` smallint DEFAULT NULL,
  `minutos` smallint DEFAULT NULL,
  `cpf_professor` bigint DEFAULT NULL,
  `cpf_professor_2` bigint DEFAULT NULL,
  PRIMARY KEY (`num_classe`,`disc_disciplina`,`area`,`tipo`),
  KEY `disc_disciplina_idx` (`disc_disciplina`),
  KEY `area_matriz_idx` (`area`),
  KEY `tipo_matriz_idx` (`tipo`),
  KEY `cpf_professor_matriz_idx` (`cpf_professor`),
  KEY `cpf_professor_matriz_2_idx` (`cpf_professor_2`),
  KEY `ix_matriz_prof` (`cpf_professor`,`cpf_professor_2`,`num_classe`,`disc_disciplina`),
  KEY `idx_mc_nclasse_disc` (`num_classe`,`disc_disciplina`),
  CONSTRAINT `area_matriz` FOREIGN KEY (`area`) REFERENCES `area_matriz` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `cpf_professor_matriz` FOREIGN KEY (`cpf_professor`) REFERENCES `professor_livro_ponto` (`cpf`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `cpf_professor_matriz_2` FOREIGN KEY (`cpf_professor_2`) REFERENCES `professor_livro_ponto` (`cpf`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `disc_disciplina_matriz` FOREIGN KEY (`disc_disciplina`) REFERENCES `disciplinas` (`codigo_disciplina`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `matriz_num_classe` FOREIGN KEY (`num_classe`) REFERENCES `turma` (`num_classe`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `tipo_matriz` FOREIGN KEY (`tipo`) REFERENCES `tipo_disc_matriz` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `notas`
--

DROP TABLE IF EXISTS `notas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notas` (
  `bimestre` int NOT NULL,
  `num_classe` int NOT NULL,
  `ra_aluno` int NOT NULL,
  `disciplina` int NOT NULL,
  `nota` varchar(2) DEFAULT NULL,
  `falta` smallint DEFAULT NULL,
  `ac` smallint DEFAULT NULL,
  PRIMARY KEY (`bimestre`,`num_classe`,`ra_aluno`,`disciplina`),
  KEY `ra_aluno_idx` (`ra_aluno`),
  KEY `disc_idx` (`disciplina`),
  CONSTRAINT `disc` FOREIGN KEY (`disciplina`) REFERENCES `disciplinas` (`codigo_disciplina`),
  CONSTRAINT `ra_aluno` FOREIGN KEY (`ra_aluno`) REFERENCES `aluno` (`ra`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `periodo`
--

DROP TABLE IF EXISTS `periodo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `periodo` (
  `id` int NOT NULL AUTO_INCREMENT,
  `descricao` varchar(45) DEFAULT NULL,
  `horario_inicio` time DEFAULT NULL,
  `horario_fim` time DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `periodo_livro_ponto`
--

DROP TABLE IF EXISTS `periodo_livro_ponto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `periodo_livro_ponto` (
  `id` int NOT NULL AUTO_INCREMENT,
  `descricao` varchar(45) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `professor`
--

DROP TABLE IF EXISTS `professor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `professor` (
  `rg` bigint NOT NULL,
  `nome` varchar(200) NOT NULL,
  `nome_ata` varchar(45) NOT NULL,
  PRIMARY KEY (`rg`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `professor_livro_ponto`
--

DROP TABLE IF EXISTS `professor_livro_ponto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `professor_livro_ponto` (
  `cpf` bigint NOT NULL,
  `nome` varchar(200) NOT NULL,
  `rg` varchar(45) NOT NULL,
  `digito` varchar(1) DEFAULT NULL,
  `rs` int DEFAULT NULL,
  `pv` tinyint DEFAULT NULL,
  `cargo` int NOT NULL,
  `categoria` int NOT NULL,
  `jornada` int NOT NULL,
  `sede_classificacao` int NOT NULL,
  `sede_controle_freq` int NOT NULL,
  `di` tinyint NOT NULL,
  `disciplina` int DEFAULT NULL,
  `afastamento` int DEFAULT NULL,
  `assina_livro` tinyint DEFAULT NULL,
  `FNREF` varchar(10) DEFAULT NULL,
  `ativo` tinyint DEFAULT '1',
  `obs` text,
  `atpc` tinyint DEFAULT NULL,
  `atpl` tinyint DEFAULT NULL,
  `aulas_outra_ue` tinyint DEFAULT NULL,
  `instancia_calendario` int NOT NULL DEFAULT '1',
  `nome_ata` varchar(45) DEFAULT NULL,
  `nascimento` date DEFAULT NULL,
  PRIMARY KEY (`cpf`,`di`),
  KEY `cargo_idx` (`cargo`),
  KEY `categoria_idx` (`categoria`),
  KEY `jornada_idx` (`jornada`),
  KEY `sede_classificacao_idx` (`sede_classificacao`),
  KEY `sede_freq_idx` (`sede_controle_freq`),
  KEY `disciplina_lp_idx` (`disciplina`),
  KEY `afastamento_idx` (`afastamento`),
  KEY `inst_calendario_idx` (`instancia_calendario`),
  KEY `idx_plp_cpf` (`cpf`),
  CONSTRAINT `afastamento` FOREIGN KEY (`afastamento`) REFERENCES `afastamento_livro_ponto` (`id`),
  CONSTRAINT `cargo` FOREIGN KEY (`cargo`) REFERENCES `cargos_livro_ponto` (`id`),
  CONSTRAINT `categoria_lp` FOREIGN KEY (`categoria`) REFERENCES `categoria_livro_ponto` (`id`),
  CONSTRAINT `disciplina_lp` FOREIGN KEY (`disciplina`) REFERENCES `disciplinas` (`codigo_disciplina`),
  CONSTRAINT `inst_calendario` FOREIGN KEY (`instancia_calendario`) REFERENCES `calendario_ponto` (`id`),
  CONSTRAINT `jornada` FOREIGN KEY (`jornada`) REFERENCES `jornada_livro_ponto` (`id`),
  CONSTRAINT `sede_classificacao` FOREIGN KEY (`sede_classificacao`) REFERENCES `sede_livro_ponto` (`id`),
  CONSTRAINT `sede_freq` FOREIGN KEY (`sede_controle_freq`) REFERENCES `sede_livro_ponto` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sede_livro_ponto`
--

DROP TABLE IF EXISTS `sede_livro_ponto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sede_livro_ponto` (
  `id` int NOT NULL AUTO_INCREMENT,
  `descricao` varchar(200) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=73343 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `situacao`
--

DROP TABLE IF EXISTS `situacao`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `situacao` (
  `id` int NOT NULL AUTO_INCREMENT,
  `descricao` varchar(45) DEFAULT NULL,
  `desc_fem` varchar(45) DEFAULT NULL,
  `abv1` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tipo_disc_matriz`
--

DROP TABLE IF EXISTS `tipo_disc_matriz`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tipo_disc_matriz` (
  `id` smallint NOT NULL AUTO_INCREMENT,
  `descricao` varchar(45) DEFAULT NULL,
  `desc_completa` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tipo_ensino`
--

DROP TABLE IF EXISTS `tipo_ensino`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tipo_ensino` (
  `id` int NOT NULL AUTO_INCREMENT,
  `descricao` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tipo_licenca_professores`
--

DROP TABLE IF EXISTS `tipo_licenca_professores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tipo_licenca_professores` (
  `id` int NOT NULL AUTO_INCREMENT,
  `descricao` varchar(45) DEFAULT NULL,
  `exibicao` varchar(45) DEFAULT NULL,
  `redline` tinyint DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `turma`
--

DROP TABLE IF EXISTS `turma`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `turma` (
  `num_classe` int NOT NULL,
  `nome_turma` varchar(100) NOT NULL,
  `duracao` int NOT NULL,
  `tipo_ensino` int NOT NULL,
  `periodo` int NOT NULL,
  `ano` smallint NOT NULL,
  `apelido` varchar(3) DEFAULT NULL,
  `id_oculto` bigint DEFAULT NULL,
  PRIMARY KEY (`num_classe`),
  KEY `duracao_idx` (`duracao`),
  KEY `tipo_ensino_idx` (`tipo_ensino`),
  KEY `peirodo_idx` (`periodo`),
  KEY `ix_turma_base` (`num_classe`,`ano`,`tipo_ensino`,`duracao`),
  CONSTRAINT `duracao` FOREIGN KEY (`duracao`) REFERENCES `duracao` (`id`),
  CONSTRAINT `peirodo` FOREIGN KEY (`periodo`) REFERENCES `periodo` (`id`),
  CONSTRAINT `tipo_ensino` FOREIGN KEY (`tipo_ensino`) REFERENCES `tipo_ensino` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `turma_if`
--

DROP TABLE IF EXISTS `turma_if`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `turma_if` (
  `num_classe` int NOT NULL,
  `nome_turma` varchar(100) NOT NULL,
  `duracao` int NOT NULL,
  `tipo_ensino` int NOT NULL,
  `categoria` int NOT NULL,
  `periodo` int NOT NULL,
  `ano` int NOT NULL,
  PRIMARY KEY (`num_classe`),
  KEY `categoria_idx` (`categoria`),
  KEY `tipo_ensino_idx` (`tipo_ensino`),
  KEY `duracao_if_idx` (`duracao`),
  KEY `periodo_if_idx` (`periodo`),
  CONSTRAINT `categoria` FOREIGN KEY (`categoria`) REFERENCES `categoria_itinerario` (`id`),
  CONSTRAINT `duracao_if` FOREIGN KEY (`duracao`) REFERENCES `duracao` (`id`),
  CONSTRAINT `periodo_if` FOREIGN KEY (`periodo`) REFERENCES `periodo` (`id`),
  CONSTRAINT `tipo_ensino_if` FOREIGN KEY (`tipo_ensino`) REFERENCES `tipo_ensino` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vinculo_alunos_if`
--

DROP TABLE IF EXISTS `vinculo_alunos_if`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vinculo_alunos_if` (
  `ra_aluno` int NOT NULL,
  `num_classe_if` int NOT NULL,
  `num_chamada` int NOT NULL,
  `matricula` date NOT NULL,
  `fim_mat` date NOT NULL,
  `situacao` int NOT NULL,
  PRIMARY KEY (`ra_aluno`,`num_classe_if`,`num_chamada`),
  KEY `num_classe_vinc_if_idx` (`num_classe_if`),
  KEY `situacao_vinc_if_idx` (`situacao`),
  CONSTRAINT `num_classe_vinc_if` FOREIGN KEY (`num_classe_if`) REFERENCES `turma_if` (`num_classe`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `ra_aluno_if` FOREIGN KEY (`ra_aluno`) REFERENCES `aluno` (`ra`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `situacao_vinc_if` FOREIGN KEY (`situacao`) REFERENCES `situacao` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vinculo_alunos_turmas`
--

DROP TABLE IF EXISTS `vinculo_alunos_turmas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vinculo_alunos_turmas` (
  `ra_aluno` int NOT NULL,
  `num_classe` int NOT NULL,
  `num_chamada` smallint NOT NULL,
  `serie` smallint NOT NULL,
  `matricula` date NOT NULL,
  `fim_mat` date NOT NULL,
  `situacao` int NOT NULL,
  PRIMARY KEY (`ra_aluno`,`num_classe`,`num_chamada`),
  KEY `num_classe_idx` (`num_classe`),
  KEY `situacao_idx` (`situacao`),
  CONSTRAINT `num_classe` FOREIGN KEY (`num_classe`) REFERENCES `turma` (`num_classe`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `ra` FOREIGN KEY (`ra_aluno`) REFERENCES `aluno` (`ra`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `situacao` FOREIGN KEY (`situacao`) REFERENCES `situacao` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vinculo_if`
--

DROP TABLE IF EXISTS `vinculo_if`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vinculo_if` (
  `num_classe_if` int NOT NULL,
  `num_classe_em` int NOT NULL,
  PRIMARY KEY (`num_classe_if`,`num_classe_em`),
  KEY `num_classe_if_em_idx` (`num_classe_em`),
  CONSTRAINT `num_classe_if_em` FOREIGN KEY (`num_classe_em`) REFERENCES `turma` (`num_classe`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `num_classe_if_vinculo` FOREIGN KEY (`num_classe_if`) REFERENCES `turma_if` (`num_classe`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vinculo_prof_disc`
--

DROP TABLE IF EXISTS `vinculo_prof_disc`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vinculo_prof_disc` (
  `num_classe` int NOT NULL,
  `cpf_prof` bigint NOT NULL,
  `bimestre` smallint NOT NULL,
  `disciplina` int NOT NULL,
  `aulas_dadas` smallint DEFAULT NULL,
  PRIMARY KEY (`num_classe`,`cpf_prof`,`bimestre`,`disciplina`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vinculo_professor_eventos_funcionais`
--

DROP TABLE IF EXISTS `vinculo_professor_eventos_funcionais`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vinculo_professor_eventos_funcionais` (
  `cpf_professor` bigint NOT NULL,
  `id_evento` smallint NOT NULL,
  `vigencia` date NOT NULL,
  `qtd_dias_proximo` int NOT NULL,
  PRIMARY KEY (`cpf_professor`,`id_evento`,`vigencia`),
  KEY `id_evento_funcional_idx` (`id_evento`),
  CONSTRAINT `cpf_professor_evento` FOREIGN KEY (`cpf_professor`) REFERENCES `professor_livro_ponto` (`cpf`),
  CONSTRAINT `id_evento_funcional` FOREIGN KEY (`id_evento`) REFERENCES `eventos_funcionais` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vinculo_turma_prof`
--

DROP TABLE IF EXISTS `vinculo_turma_prof`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vinculo_turma_prof` (
  `id_turma` int NOT NULL,
  `rg_prof` bigint NOT NULL,
  PRIMARY KEY (`id_turma`,`rg_prof`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Final view structure for view `grade_horario_vw`
--

/*!50001 DROP VIEW IF EXISTS `grade_horario_vw`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `grade_horario_vw` AS select `g`.`num_classe` AS `num_classe`,`g`.`semana` AS `semana`,`g`.`pos` AS `pos`,`d`.`abv` AS `disc_abv`,coalesce(`ht`.`inicio`,`ha`.`inicio`) AS `inicio`,coalesce(`ht`.`fim`,`ha`.`fim`) AS `fim`,nullif(trim(concat_ws(' / ',`p1`.`nome_ata`,`p2`.`nome_ata`,`p1`.`nome`,`p2`.`nome`)),'') AS `prof_nome`,(case when ((`p1`.`cpf` is null) and (`p2`.`cpf` is null)) then NULL when (`p1`.`cpf` is null) then cast(`p2`.`cpf` as char charset utf8mb4) when (`p2`.`cpf` is null) then cast(`p1`.`cpf` as char charset utf8mb4) else concat(least(`p1`.`cpf`,`p2`.`cpf`),'/',greatest(`p1`.`cpf`,`p2`.`cpf`)) end) AS `prof_key`,concat(`d`.`abv`,if((nullif(trim(concat_ws(' / ',`p1`.`nome_ata`,`p2`.`nome_ata`)),'') is null),'',concat(' (',nullif(trim(concat_ws(' / ',`p1`.`nome_ata`,`p2`.`nome_ata`)),''),')'))) AS `label` from (((((((`grade` `g` join `turma` `t` on((`t`.`num_classe` = `g`.`num_classe`))) left join `horario_turma` `ht` on(((`ht`.`num_classe` = `g`.`num_classe`) and (`ht`.`pos` = `g`.`pos`)))) left join `hora_aulas` `ha` on(((`ha`.`ano` = `t`.`ano`) and (`ha`.`tipo_ensino` = `t`.`tipo_ensino`) and (`ha`.`pos` = `g`.`pos`)))) left join `disciplinas` `d` on((`d`.`codigo_disciplina` = `g`.`disciplina`))) left join `matriz_curricular` `m` on(((`m`.`num_classe` = `g`.`num_classe`) and (`m`.`disc_disciplina` = `g`.`disciplina`)))) left join `professor_livro_ponto` `p1` on((`p1`.`cpf` = `m`.`cpf_professor`))) left join `professor_livro_ponto` `p2` on((`p2`.`cpf` = `m`.`cpf_professor_2`))) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-03-05 16:28:04
