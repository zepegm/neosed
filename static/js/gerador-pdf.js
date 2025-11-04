const meses = [
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro"
  ];

function PriMaiuscula(palavra) {
    //const palavras = palavra.toLowerCase().split(" ");

    return palavra.toLowerCase().replace(/(^\w{1})|(\s+\w{1})/g, letra => letra.toUpperCase()).replace(/Da /g, "da ").replace(/Do /g, "do ").replace(/De /g, "de ").replace(/Dos /g, "dos ");
}

function gerarAtaConselhoFinal(lista) {
    // primeiro gerará a capa (opcional)
    var doc = new jsPDF({
        orientation: 'portrait',
        unit: 'cm',
        format: 'a4'
    });

    doc.setFont('BebasKai', 'normal');
    x = 10.5;
    
    y = 14.7;
    doc.setTextColor(255, 0, 0);
    doc.setFontSize(75);
    doc.text(x, y, 'CONSELHO FINAL', 'center');

    doc.setLineWidth(0.2);
    doc.rect(0.7, 0.7, 19.6, 28.3, 'S');

    doc.setLineWidth(0.05);
    doc.rect(1, 1, 19, 27.7, 'S');

    // agora será gerada a lista piloto final
    doc.addPage();  
    
    var img = new Image();

    img.src = "/static/images/Logo%20Neo%20Sed%20White.png";
    doc.addImage(img, 'png', 0, -1, 6, 6);        

    doc.setFont('BebasKai', 'normal');
    doc.setFontSize(20);
    y = 1;
    x = 2.7;

    doc.setTextColor(0, 0, 0);
    doc.text(x, y, 'Lista Geral - ');

    textWidth = x + doc.getTextWidth('Lista Geral - ');

    doc.setTextColor(255, 0, 0);
    doc.text(textWidth, y, lista['turma']['nome_turma']);

    textWidth = textWidth + doc.getTextWidth(lista['turma']['nome_turma']);

    doc.setTextColor(0, 0, 0);

    if (lista['turma']['tipo_ensino'] == "Itinerário Formativo Regular") {
        doc.text(textWidth, y, " - " +  "IF - Regular");
        textWidth = textWidth + doc.getTextWidth(" - " +  "IF - Regular");
    } else {
        doc.text(textWidth, y, " - " +  lista['turma']['tipo_ensino']);
        textWidth = textWidth + doc.getTextWidth(" - " +  lista['turma']['tipo_ensino']);
    }

    doc.text(textWidth, y, " - " +  lista['turma']['desc_duracao']);    

    x = 5.2;
    y = 1.6

    doc.setTextColor(0, 112, 192);
    doc.text('RESULTADO FINAL', 15.3, 3)
    doc.setTextColor(0, 0, 0);

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(12);
    doc.text("Número da Classe:", x , y);
    textWidth =  doc.getTextWidth("Número da Classe:") + x + 0.2;
    doc.setFont('helvetica', 'normal');
    doc.text(String(lista['turma']['num_classe']), textWidth, y);

    y += 0.6;

    doc.setFont('helvetica', 'bold');
    doc.text("Período:", x , y);
    textWidth =  doc.getTextWidth("Período:") + x + 0.2;
    doc.setFont('helvetica', 'normal');
    doc.text(lista['turma']['periodo'], textWidth, y);      

    y += 0.6;

    doc.setFont('helvetica', 'bold');
    doc.text("Duração:", x , y);
    textWidth =  doc.getTextWidth("Duração:") + x + 0.2;
    doc.setFont('helvetica', 'normal');
    doc.text(lista['turma']['inicio'] + ' até ' + lista['turma']['fim'], textWidth, y); 

    y += 0.6; 
    
    // agora que o bicho pega
    x_num = 0.5;
    x_rm = 1.2;

    if (lista['turma']['tipo_ensino'] == "Itinerário Formativo Regular") {
        x_nome = 2.3;
        x_serie = 0;
    } else {
        x_serie = 2.3;
        x_nome = 3.75;
    }

    x_ra = 13.9;
    x_mat = 16.5;
    x_mov = 18.7;

    y = 4;

    // borda do cabecalho
    doc.setLineWidth(0.05);
    doc.setFillColor(254, 254, 226);
    doc.rect(0.4, 3.6, 20.2, 0.5, 'F');
    doc.line(0.4, 3.6, 20.6, 3.6);

    // desenha o cabeçalho
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(10);
    doc.text('Nº', x_num, y);
    doc.text('RM', x_rm, y);
    
    if (lista['turma']['tipo_ensino'] != "Itinerário Formativo Regular") {
        doc.text('SÉRIE', x_serie, y);
        tamanho = doc.getTextWidth('SÉRIE');
    }

    doc.text('NOME', x_nome, y);
    //doc.text('NASC.', x_nasc, y);
    doc.text("RA", x_ra, y);
    doc.text("SITUAÇÃO", x_mat, y);
    //doc.text("FIM MATR.", x_mov, y);

    doc.setLineWidth(0.01);
    doc.line(0.4, y + 0.13, 20.6, y + 0.13);

    doc.setFont('helvetica', 'normal');    

    var cont = 0;    
    var aprovados = 0;

    for(let i = 0; i < lista['alunos'].length; i++) {

        if (lista['alunos'][i]['abv1'] != "APROV" && lista['alunos'][i]['abv1'] != "ATIVO") {
            doc.setTextColor(255, 0, 0);
        } else {
            doc.setTextColor(0, 0, 0);
            aprovados += 1;
        }

        
        doc.setFont('helvetica', 'normal');
        y += 0.49;

        doc.text(String(lista['alunos'][i]['num']).padStart(2, "0"), x_num, y);   
        doc.text(lista['alunos'][i]['rm'], x_rm, y)
        if (lista['turma']['tipo_ensino'] != "Itinerário Formativo Regular") {
            doc.text(String(lista['alunos'][i]['serie']), x_serie + (tamanho / 2) - (doc.getTextWidth(String(lista['alunos'][i]['serie'])) / 2), y);
        }
        doc.text(PriMaiuscula(lista['alunos'][i]['nome']), x_nome, y);
        //doc.text(table[i][5]['display'], x_nasc, y);
        doc.text(lista['alunos'][i]['ra'], x_ra, y);

        doc.setFont('helvetica', 'bold');

        if (lista['alunos'][i]['abv1'] == "APROV" || lista['alunos'][i]['abv1'] == "ATIVO") {
            doc.setTextColor(0, 112, 192);
        } else {
            doc.setTextColor(255, 0, 0);
        }
        
        doc.text(lista['alunos'][i]['situacao'], x_mat, y);

        /*doc.setFont('helvetica', 'bold');
        doc.text(lista['alunos'][i]['mat'], x_mat, y);*/

        doc.setLineWidth(0.01);

        if (i == lista['alunos'].length - 1 && i == 50) {
            doc.setLineWidth(0.05);
        }

        doc.line(0.4, y + 0.13, 20.6, y + 0.13);
        cont += 1;

    }

    var dif = 51 - cont;

    if (dif > 0) {
        var num = parseInt(lista['alunos'][lista['alunos'].length - 1]['num']) + 1;
        doc.setFont('helvetica', 'normal');
        doc.setLineWidth(0.01);
        doc.setTextColor(0, 0, 0);

        for(let i = 0; i < dif; i++) {
            y += 0.49;

            doc.text(String(num).padStart(2, "0"), x_num, y);
            num += 1;

            if (i == dif - 1) {
                doc.setLineWidth(0.05);
            }

            doc.line(0.4, y + 0.13, 20.6, y + 0.13);                    
        }
    }

    doc.setLineWidth(0.05);
    doc.line(0.4, 3.6, 0.4, y + 0.13);
    doc.line(x_rm - 0.2, 3.6, x_rm - 0.2, y + 0.13);
    doc.line(x_nome - 0.2, 3.6, x_nome - 0.2, y + 0.13);
    doc.line(x_serie - 0.2, 3.6, x_serie - 0.2, y + 0.13);
    doc.line(x_ra - 0.2, 3.6, x_ra - 0.2, y + 0.13);
    doc.line(x_mat - 0.2, 3.6, x_mat - 0.2, y + 0.13);
    //doc.line(x_mov - 0.2, 3.6, x_mov - 0.2, y + 0.13);
    doc.line(20.6, 3.6, 20.6, y + 0.13);    


    x = 5.2;
    y = 3.4;

    doc.setFont('helvetica', 'bold');
    doc.text("Total:", x , y);
    textWidth =  doc.getTextWidth("Total:") + x + 0.2;
    doc.setFont('helvetica', 'normal');
    if (lista['turma']['tipo_ensino'] != "Itinerário Formativo Regular") {
        doc.text(aprovados + " Aprovados (" + lista['alunos'].length + " no total).", textWidth, y);   
    } else {
        doc.text(aprovados + " Ativos (" + lista['alunos'].length + " no total).", textWidth, y);   
    }


    // agora gerar o lendário final
    doc.addPage();
    x = 1;
    y = 1.5;
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(255, 0, 0);
    
    var splitText = doc.splitTextToSize('CONS. FINAL', 0.3);

    /*doc.setFontSize(13);
    doc.text(bimestre + 'º', x, y, 'center');
    y += 1;*/

    doc.setFontSize(11);
    for (var i = 0, length = splitText.length; i < length; i++) {
        // loop thru each line and increase
        doc.text(splitText[i], x, y, 'center')
        y += 0.5;
      }

    doc.setLineWidth(0.01);
    doc.line(0.7, 6.2, 1.3, 6.2);

    y += 0.2;

    doc.setTextColor(0, 0, 0);
    doc.text("Nº", x, y, 'center');
    //doc.line(x + 0.3, 1, x + 0.3, y + 0.2);

    //doc.line(1.4, 0.5, 11, 0.5);


    doc.setFont('helvetica', 'normal');
    
    x = 1.3;
    total = lista['disciplinas'].length;
    dif = (10 - x) / total;

    lin_inicial = y;
    limite = 11;

    doc.setFontSize(10);
    for (var disc in lista['disciplinas']) {
        center = x + (dif / 2);

        if (lista['turma']['tipo_ensino'] != "Itinerário Formativo Regular") {
            doc.text(lista['disciplinas'][disc]['completo'], (center + 0.1), y, null, 90);
        } else {
            doc.text(lista['disciplinas'][disc]['desc_disc'], (center + 0.1), y, null, 90);
        }
        
        if (disc == 0) {
            doc.line(0.7, y + 0.15, limite, y + 0.15);
        }

        y += 0.5;

        doc.setFontSize(9);
        for (var aluno in lista['alunos']) {
            doc.setFont('helvetica', 'bold');

            if (disc == 0) {
                doc.text(String(lista['alunos'][aluno]['num']).padStart(2, '0'), 1, y, 'center');
                doc.line(0.7, y + 0.1, limite, y + 0.1);
                ultimo = lista['alunos'][aluno]['num'];
            }
            
            var ra = parseInt(lista['alunos'][aluno]['ra'].replaceAll('.', '').slice(0, -2));
            doc.setFont('helvetica', 'normal');
            //doc.setFontSize(7);
            try {

                if (lista['alunos'][aluno]['abv1'] == "APROV" || lista['alunos'][aluno]['abv1'] == "RETD" || lista['alunos'][aluno]['abv1'] == "ATIVO") {
                    if (lista['disciplinas'][disc]['notas'][ra]['media'] < 5) {
                        doc.setTextColor(255, 0, 0);
                    }
    
                    doc.text(String(lista['disciplinas'][disc]['notas'][ra]['media']), center, y, 'center');
                    //doc.line(x - (dif / 3) + ((dif / 3) / 2), y - 0.4, x - (dif / 3) + ((dif / 3) / 2), y + 0.1);
                    doc.setTextColor(0, 0, 0);
                } else {
                    doc.text('-', center, y - 0.05, 'center');
                }

            } catch (error) {
                doc.text('-', center, y - 0.05, 'center');
            }            

            y += 0.45;
        }

        diferenca = 48 - lista['alunos'].length;

        for (let i = 0; i < diferenca; i++) {
            if (disc == 0) {
                //doc.setFontSize(11);
                doc.setFont('helvetica', 'bold');
                ultimo += 1;
                doc.text(String(ultimo).padStart(2, '0'), 1, y, 'center');
                //doc.setFont('helvetica', 'normal');        
                
                doc.line(0.7, y + 0.1, limite, y + 0.1);
            }
            
            y += 0.45; 
        }         

        if (disc == 0) {
            doc.line(1.3, 1, 1.3, y - 0.35);
        }

        if (disc == total - 1) {
            doc.setLineWidth(0.05);
        }

        doc.line(center + (dif / 2), 1, center + (dif / 2), y - 0.35);

        doc.setLineWidth(0.01);

        x += dif;
        lin_final = y;        
        y = lin_inicial;
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(10);
    }

    //x -= dif;

    x += 0.5;

    // após a digitação das notas será digitada as faltas
    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    doc.text("TOTAL FALTAS", x, y - 0.3, null, 90);
    doc.text("TOTAL AUS. COMPENSADAS", x + 0.7, y - 0.3, null, 90);
    doc.text("% FREQUÊNCIA FINAL", x + 1.4, y - 0.3, null, 90);
    if (lista['turma']['tipo_ensino'] != "Itinerário Formativo Regular") {
        doc.text("SITUAÇÃO FINAL", x + 2.8, y - 0.3, null, 90);
    } else {
        doc.text("SITUAÇÃO", x + 2.8, y - 0.3, null, 90);
    }

    doc.line(x - 0.52, y + 0.15, x + 3.7, y + 0.15);

    y += 0.5;

    for (var aluno in lista['alunos']) {
        try {

            if (lista['alunos'][aluno]['abv1'] == "APROV" || lista['alunos'][aluno]['abv1'] == "RETD" || lista['alunos'][aluno]['abv1'] == "ATIVO") {
                ra = parseInt(lista['alunos'][aluno]['ra'].replaceAll('.', '').slice(0, -2));
                doc.text(lista['freq'][ra]['total_faltas'], x - 0.15, y, 'center');
    
                doc.text(lista['freq'][ra]['ac'], x + 0.55, y, 'center');

                if (lista['freq'][ra]['freq'] < 75) {
                    doc.setTextColor(255, 0, 0);
                }
    
                doc.text(lista['freq'][ra]['freq'], x + 1.25, y, 'center');
                doc.setTextColor(0, 0, 0);
                
    
                //doc.setFont('helvetica', 'normal');
                doc.setFontSize(7);

                if (lista['alunos'][aluno]['abv1'] == "APROV" || lista['alunos'][aluno]['abv1'] == "ATIVO") {
                    doc.setTextColor(0, 112, 192);
                } else {
                    doc.setTextColor(255, 0, 0);
                }

                doc.text(lista['alunos'][aluno]['abv1'], x + 2.65, y - 0.04, 'center');
                doc.setTextColor(0, 0, 0);
                doc.setFont('helvetica', 'bold');
                doc.setFontSize(10);
            } else {
                doc.text('-', x - 0.15, y, 'center');
                doc.text('-', x + 0.55, y, 'center');
                doc.text('-', x + 1.25, y, 'center');
                doc.setTextColor(255, 0, 0);
                doc.setFontSize(7);
                doc.text(lista['alunos'][aluno]['abv1'], x + 2.65, y - 0.04, 'center');
                doc.setTextColor(0, 0, 0);
                doc.setFontSize(10);                
            }



        } catch (error) {
            doc.text('-', x - 0.15, y, 'center');
            doc.text('-', x + 0.55, y, 'center');
            doc.text('-', x + 1.25, y, 'center');
            doc.setTextColor(255, 0, 0);
            doc.setFontSize(7);
            doc.text(lista['alunos'][aluno]['abv1'], x + 2.65, y - 0.04, 'center');
            doc.setTextColor(0, 0, 0);
            doc.setFontSize(10);
        }     
        doc.line(x - 0.52, y + 0.1, x + 3.7, y + 0.1);
        
        y += 0.45;
    }

    for (let i = 0; i < diferenca; i++) {
        doc.line(x - 0.52, y + 0.1, x + 3.7, y + 0.1);
        
        y += 0.45; 
    } 
    
    // desenhar bordas da frequência
    doc.setLineWidth(0.05);
    doc.line(x + 0.2, 1, x + 0.2, y - 0.35);
    doc.line(x + 0.9, 1, x + 0.9, y - 0.35);
    doc.line(x + 1.6, 1, x + 1.6, y - 0.35);
    doc.line(x + 3.7, 1, x + 3.7, y - 0.35);

    // desenhar a parte direita da ata

    var dt = new Date(lista['turma']['fim'].substring(6, 11), parseInt(lista['turma']['fim'].substring(3, 5)) - 1, parseInt(lista['turma']['fim'].substring(0, 2)));
    
    

    console.log(dt);

    // texto da ata

    x += 7.2;

    var in_x = x;

    y = 1.5;
    doc.text('CONSELHO DE CLASSE', x, y, 'center');
    doc.setFont('helvetica', 'normal');
    y += 1;
    x -= 1.4;
    
    if (dt.getDate() == 1) {
        doc.text('No primeiro dia do mês de', x - 0.55, y);
    } else {
        doc.text('Aos ', x, y);
        tamanho = doc.getTextWidth('Aos ');
        doc.setFont('helvetica', 'bold');
        x += tamanho;
        doc.text(String(dt.getDate()).padStart(2, '0'), x, y);
        tamanho = doc.getTextWidth(String(dt.getDate()).padStart(2, '0'));
        doc.setLineWidth(0.01);
        doc.line(x, y + 0.05, x + tamanho, y + 0.05);
        x += tamanho;
        doc.setFont('helvetica', 'normal');
        doc.text(' dias do mês de ', x, y);
    }

    y += 0.6;
    x = in_x - 1.3;

    doc.setFont('helvetica', 'bold');
    doc.text(meses[dt.getMonth()], x + 0.25, y, 'center');
    doc.line(x - 1, y + 0.05, x + 1.5, y + 0.05);
    doc.setFont('helvetica', 'normal');
    x += 1.5;
    doc.text(" de ", x, y);
    x += doc.getTextWidth(" de ");
    doc.setFont('helvetica', 'bold');
    doc.text('2023', x + 0.77, y, 'center');
    doc.line(x, y + 0.05, x + 1.55, y + 0.05);

    y += 0.6;
    x = in_x;

    doc.setFont('helvetica', 'normal');
    doc.text('realizou-se o Cons.  Final de ', x + 2.2, y, 'right');

    y += 0.6;

    doc.text('Classe e Série dos alunos da', x + 2.2, y, 'right');

    y += 0.6;

    doc.setTextColor(255, 0, 0);
    doc.setFont('helvetica', 'bold');
    x -= 2.4;
    doc.text(lista['turma']['nome_turma'], x, y);
    tamanho = doc.getTextWidth(lista['turma']['nome_turma']);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(0, 0, 0);
    doc.text(" do", x + tamanho, y);

    y += 0.6;

    doc.setFont('helvetica', 'bold');

    if (lista['turma']['tipo_ensino'] != "Itinerário Formativo Regular") {
        doc.text(lista['turma']['tipo_ensino'], x, y);
        tamanho = doc.getTextWidth(lista['turma']['tipo_ensino']);
    } else {
        doc.text("IF - Regular", x, y);
        tamanho = doc.getTextWidth("IF - Regular");        
    }

    doc.setFont('helvetica', 'normal');
    doc.text(" da", x + tamanho, y);

    y += 0.6;
    
    doc.text("EE Profª Alice Vilela Galvão", x, y);

    y += 0.6;
    doc.text('Canas, ' + lista['turma']['fim'], x + 4.5, y, 'right');

    y += 0.6;
    x = in_x - 2.7;

    // lista dos professores

    doc.setFontSize(5);
    doc.line(x, y - 0.2, x + 5, y - 0.2);
    doc.text('Matéria', x, y);
    x += 1.5;
    doc.text('Professor', x, y);
    x += 2;
    doc.text('Assinatura', x, y);
    
    y += 0.4;

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(8);
    for (item in lista['disciplinas']) {
        x = in_x - 2.7;

        doc.setLineDash([0.05, 0.05]);
        doc.line(x, y + 0.2, x + 5, y + 0.2);

        if (lista['turma']['tipo_ensino'] != "Itinerário Formativo Regular") {
            doc.text(lista['disciplinas'][item]['desc_disc'], x, y);
        } else {
            doc.setFontSize(6);
            doc.text(lista['disciplinas'][item]['desc_disc'], x, y);
            doc.setFontSize(8);
        }

        x += 1.5;
        doc.text(lista['disciplinas'][item]['nome_ata'], x, y); 
        x += 2;

        y += 0.6    
    }

    // observações

    x = in_x - 2.7;
    y += 0.3;
    doc.text('OBSERVAÇÕES', x, y);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(6);
    for (item in dificuldades) {
        y += 0.4;
        doc.setFont('helvetica', 'bold');
        //doc.text(String(dificuldades[item]['id']).padStart(2, '0'), x, y);
        doc.setFont('helvetica', 'normal');
        //doc.text(' - ' + dificuldades[item]['title'], x + doc.getTextWidth('00'), y);
        doc.line(x, y + 0.14, x + 5, y + 0.14);
        //console.log(dificuldades[item]);
    }

    // assinaturas

    y += 1.5;

    doc.setFontSize(8);
    doc.setLineDash([]);
    doc.line(x, y - 0.3, x + 5, y - 0.3);
    doc.text("Coordenador Pedagógico", x + 2.5, y, 'center');

    y += 1.5;
    doc.line(x, y - 0.3, x + 5, y - 0.3);
    doc.text("Diretor de Escola", x + 2.5, y, 'center');


    // após escrever tudo gerar as bordas finais
    doc.setLineWidth(0.05);

    // borda esquerda
    doc.line(0.68, 1, 0.68, lin_final - 0.31);
    // borda inferior
    doc.line(0.68, lin_final - 0.33, x + 5.5, lin_final - 0.33);
    // borda direita
    doc.line(x + 5.5, 1, x + 5.5, lin_final - 0.31);
    // borda superior
    doc.line(0.68, 1, x + 5.5, 1);

    window.open(doc.output('bloburl'), '_blank');  

    
}

function gerarAtaConselho(bimestre, ano, turma, fim_bim, lista, dificuldades) {
    
    // primeiro gerará a capa (opcional)
    var doc = new jsPDF({
        orientation: 'portrait',
        unit: 'cm',
        format: 'a4'
    });

    //console.log(lista);

    if (lista['turma']['tipo_ensino'] != "Itinerário Formativo Regular") {

        doc.setFont('BebasKai', 'normal');
        doc.setFontSize(50);
        y = 3;
        x = 10.5;
        doc.text(x, y, 'EE PROFª ALICE VILELA GALVÃO', 'center');

        y = 27;
        doc.setTextColor(255, 0, 0);
        doc.setFontSize(75);
        doc.text(x, y, bimestre + 'º Bimestre de ' + ano, 'center');

        doc.setFont('GreatVibes-Regular', 'normal');
        y = 14.7;
        doc.setFontSize(60);
        doc.setTextColor(0, 0, 0);
        doc.text(x, y, 'Conselho de classe/série', 'center');

        doc.setLineWidth(0.2);
        doc.rect(0.7, 0.7, 19.6, 28.3, 'S');

        doc.setLineWidth(0.05);
        doc.rect(1, 1, 19, 27.7, 'S');

        doc.addPage();
        doc.addPage();   
    
    }

    // agora gerará a capa da sala (obrigatório)
    doc.setLineWidth(0.2);
    doc.rect(0.7, 0.7, 19.6, 28.3, 'S');

    doc.setLineWidth(0.05);
    doc.rect(1, 1, 19, 27.7, 'S');

    doc.setFont('BebasKai', 'normal');
    doc.setFontSize(80);
    doc.setTextColor(255, 0, 0);

    x = 10.5;
    y = 14.7;

    //console.log(turma);

    if (lista['turma']['tipo_ensino'] == "Itinerário Formativo Regular") {
        doc.text(x, y, "IF - REGULAR", 'center');
        tamanho = doc.getTextWidth("IF - REGULAR");
    } else {
        doc.text(x, y, turma, 'center');
        tamanho = doc.getTextWidth(turma);
    }

    doc.setLineWidth(0.2);
    doc.rect(x - (tamanho / 2) - 0.5, 11.7, tamanho + 1.5, 4);

    doc.addPage();
    doc.addPage();

    // agora gerará a lista piloto do bimestre
    var img = new Image();

    img.src = "/static/images/Logo%20Neo%20Sed%20White.png";
    doc.addImage(img, 'png', 0, -1, 6, 6);        

    doc.setFont('BebasKai', 'normal');
    doc.setFontSize(20);
    y = 1;
    x = 2.7;

    doc.setTextColor(0, 0, 0);
    doc.text(x, y, 'Lista Geral - ');

    textWidth = x + doc.getTextWidth('Lista Geral - ');

    doc.setTextColor(255, 0, 0);
    doc.text(textWidth, y, lista['turma']['nome_turma']);

    textWidth = textWidth + doc.getTextWidth(lista['turma']['nome_turma']);

    doc.setTextColor(0, 0, 0);

    if (lista['turma']['tipo_ensino'] == "Itinerário Formativo Regular") {
        doc.text(textWidth, y, " - " +  "IF - Regular");
        textWidth = textWidth + doc.getTextWidth(" - " +  "IF - Regular");
    } else {
        doc.text(textWidth, y, " - " +  lista['turma']['tipo_ensino']);
        textWidth = textWidth + doc.getTextWidth(" - " +  lista['turma']['tipo_ensino']);
    }

    

    

    doc.text(textWidth, y, " - " +  lista['turma']['desc_duracao']);    

    x = 5.2;
    y = 1.6

    doc.setTextColor(0, 112, 192);
    doc.text('Dados de Matrícula', 15.3, 3)
    doc.setTextColor(0, 0, 0);

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(12);
    doc.text("Número da Classe:", x , y);
    textWidth =  doc.getTextWidth("Número da Classe:") + x + 0.2;
    doc.setFont('helvetica', 'normal');
    doc.text(String(lista['turma']['num_classe']), textWidth, y);

    y += 0.6;

    doc.setFont('helvetica', 'bold');
    doc.text("Período:", x , y);
    textWidth =  doc.getTextWidth("Período:") + x + 0.2;
    doc.setFont('helvetica', 'normal');
    doc.text(lista['turma']['periodo'], textWidth, y);      

    y += 0.6;

    doc.setFont('helvetica', 'bold');
    doc.text("Duração:", x , y);
    textWidth =  doc.getTextWidth("Duração:") + x + 0.2;
    doc.setFont('helvetica', 'normal');
    doc.text(lista['turma']['inicio'] + ' até ' + lista['turma']['fim'], textWidth, y); 

    y += 0.6; 
    
    // agora que o bicho pega
    x_num = 0.5;
    x_rm = 1.2;

    if (lista['turma']['tipo_ensino'] == "Itinerário Formativo Regular") {
        x_nome = 2.3;
        x_serie = 0;
    } else {
        x_serie = 2.3;
        x_nome = 3.75;
    }

    x_ra = 13.9;
    x_mat = 16.5;
    x_mov = 18.7;

    y = 4;

    // borda do cabecalho
    doc.setLineWidth(0.05);
    doc.setFillColor(254, 254, 226);
    doc.rect(0.4, 3.6, 20.2, 0.5, 'F');
    doc.line(0.4, 3.6, 20.6, 3.6);

    // desenha o cabeçalho
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(10);
    doc.text('Nº', x_num, y);
    doc.text('RM', x_rm, y);

    if (lista['turma']['tipo_ensino'] != "Itinerário Formativo Regular") {
        doc.text('SÉRIE', x_serie, y);
        tamanho = doc.getTextWidth('SÉRIE');
    }
    
    doc.text('NOME', x_nome, y);
    //doc.text('NASC.', x_nasc, y);
    doc.text("RA", x_ra, y);
    doc.text("MATR.", x_mat, y);
    doc.text("FIM MATR.", x_mov, y);

    doc.setLineWidth(0.01);
    doc.line(0.4, y + 0.13, 20.6, y + 0.13);

    doc.setFont('helvetica', 'normal');    

    var cont = 0;    
    var ativos = 0;

    for(let i = 0; i < lista['alunos'].length; i++) {

        if (lista['alunos'][i]['mat'] == "APROV" || lista['alunos'][i]['mat'] == "RETD") {
            lista['alunos'][i]['fim_mat'] = "";
            lista['alunos'][i]['mat'] = "";
        }

        if (lista['alunos'][i]['fim_mat'] != "") {
            doc.setTextColor(255, 0, 0);
        } else {
            doc.setTextColor(0, 0, 0);
            ativos += 1;
        }

        
        doc.setFont('helvetica', 'normal');
        y += 0.49;

        doc.text(String(lista['alunos'][i]['num']).padStart(2, "0"), x_num, y);   
        doc.text(lista['alunos'][i]['rm'], x_rm, y)
        if (lista['turma']['tipo_ensino'] != "Itinerário Formativo Regular") {
            doc.text(String(lista['alunos'][i]['serie']), x_serie + (tamanho / 2) - (doc.getTextWidth(String(lista['alunos'][i]['serie'])) / 2), y);
        }
        doc.text(PriMaiuscula(lista['alunos'][i]['nome']), x_nome, y);
        //doc.text(table[i][5]['display'], x_nasc, y);
        doc.text(lista['alunos'][i]['ra'], x_ra, y);

        doc.setFont('helvetica', 'bold');
        doc.text(lista['alunos'][i]['fim_mat'], x_mov, y);

        if (lista['alunos'][i]['fim_mat'] == "") {
            doc.setTextColor(0, 112, 192);
        } else {
            doc.setTextColor(255, 0, 0);
        }
        
        doc.setFont('helvetica', 'bold');
        doc.text(lista['alunos'][i]['mat'], x_mat, y);

        doc.setLineWidth(0.01);

        if (i == lista['alunos'].length - 1 && i == 50) {
            doc.setLineWidth(0.05);
        }

        doc.line(0.4, y + 0.13, 20.6, y + 0.13);
        cont += 1;

    }

    var dif = 51 - cont;

    if (dif > 0) {
        var num = parseInt(lista['alunos'][lista['alunos'].length - 1]['num']) + 1;
        doc.setFont('helvetica', 'normal');
        doc.setLineWidth(0.01);
        doc.setTextColor(0, 0, 0);

        for(let i = 0; i < dif; i++) {
            y += 0.49;

            doc.text(String(num).padStart(2, "0"), x_num, y);
            num += 1;

            if (i == dif - 1) {
                doc.setLineWidth(0.05);
            }

            doc.line(0.4, y + 0.13, 20.6, y + 0.13);                    
        }
    }

    doc.setLineWidth(0.05);
    doc.line(0.4, 3.6, 0.4, y + 0.13);
    doc.line(x_rm - 0.2, 3.6, x_rm - 0.2, y + 0.13);
    doc.line(x_nome - 0.2, 3.6, x_nome - 0.2, y + 0.13);
    doc.line(x_serie - 0.2, 3.6, x_serie - 0.2, y + 0.13);
    doc.line(x_ra - 0.2, 3.6, x_ra - 0.2, y + 0.13);
    doc.line(x_mat - 0.2, 3.6, x_mat - 0.2, y + 0.13);
    doc.line(x_mov - 0.2, 3.6, x_mov - 0.2, y + 0.13);
    doc.line(20.6, 3.6, 20.6, y + 0.13);    


    x = 5.2;
    y = 3.4;

    doc.setFont('helvetica', 'bold');
    doc.text("Total:", x , y);
    textWidth =  doc.getTextWidth("Total:") + x + 0.2;
    doc.setFont('helvetica', 'normal');
    doc.text(ativos + " ativos (" + lista['alunos'].length + " no total).", textWidth, y);   

    // agora a coisa fica um pouco mais complicada, hora de fazer o mapão
    doc.addPage();

    x = 10.5;
    y = 1.5;

    doc.line(0.7, 0.7, 20.3, 0.7);

    doc.setFontSize(15);
    doc.setFont('times', 'bold');
    doc.text('REGISTRO DE CONTROLE DO RENDIMENTO ESCOLAR', x, y, 'center');

    x = 1.5;
    y += 1;

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(12);
    /*doc.text('TURMA: ', x, y);
    x += doc.getTextWidth('TURMA: ');
    doc.setTextColor(255, 0, 0);
    doc.text(lista['turma']['nome_turma'], x, y);*/

    texto = "TURMA: " + lista['turma']['nome_turma'] + "    BIMESTRE: " + bimestre + "º    ANO: " + lista['turma']['ano'] + "    " + lista['turma']['tipo_ensino'];
    x = (21 - doc.getTextWidth(texto)) / 2;

    doc.text("TURMA: ", x, y);
    x += doc.getTextWidth("TURMA: ");

    doc.setTextColor(255, 0, 0);
    doc.text(lista['turma']['nome_turma'], x, y);
    x += doc.getTextWidth(lista['turma']['nome_turma']);

    doc.setTextColor(0, 0, 0);
    doc.text("    BIMESTRE: ", x, y);
    x += doc.getTextWidth("    BIMESTRE: ");

    doc.setTextColor(255, 0, 0);
    doc.text(bimestre + "º    ", x, y);
    x += doc.getTextWidth(bimestre + "º    ");

    doc.setTextColor(0, 0, 0);
    doc.text("ANO: ", x, y);
    x += doc.getTextWidth("ANO: ");

    doc.setTextColor(255, 0, 0);
    doc.text(lista['turma']['ano'] + "    ", x, y);
    x += doc.getTextWidth(lista['turma']['ano'] + "    ");

    doc.setTextColor(0, 0, 0);
    doc.text(lista['turma']['tipo_ensino'], x, y);
    //x += doc.getTextWidth("    " + lista['turma']['tipo_ensino']);

    y += 0.3;
    doc.line(0.7, y, 20.3, y);

    y += 0.4;

    doc.text('Nº', 1.05, y + 0.2, 'center');

    total = lista['disciplinas'].length;
    //console.log(total);

    //x = 1.4;
    //x = 2.5;
    dif = (20.3 - 1.4) / total;
    console.log(dif);
    x = 1.4;

    //x += dif / 2;
    //console.log(dif);

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(11);

    lin_inicial = y;
    lin_final = 0;
    ultimo = 0;

    doc.setLineWidth(0.01);
    for (var item in lista['disciplinas']) {

        center = x + (dif / 2)

        doc.text(lista['disciplinas'][item]['desc_disc'], center, y, 'center');

        if (item == 0) {
            doc.line(1.4, y + 0.1, 20.3, y + 0.1);
        }

        y += 0.4;                                                                                                                                                                                                                                                                                                                                                                                                                                                           

        doc.setFontSize(8);
        doc.text("N", center - (dif / 3), y, 'center');
        doc.line(center - (dif / 3) + ((dif / 3) / 2), y - 0.3, center - (dif / 3) + ((dif / 3) / 2), y + 0.1);
        doc.text("F", center, y, 'center');
        doc.line(center + (dif / 3) - ((dif / 3) / 2), y - 0.3, center + (dif / 3) - ((dif / 3) / 2), y + 0.1);
        doc.setFontSize(6);
        doc.text("AC", center + (dif / 3), y - 0.03, 'center');

        y += 0.1;

        if (item == 0) {
            doc.setLineWidth(0.05);
            doc.line(0.7, y, 20.3, y);
            doc.setLineWidth(0.01);
        }

        y += 0.4;

        // rodar um loop com as notas
        for (var aluno in lista['alunos']) {
            if (item == 0) {
                doc.setFontSize(11);
                doc.setFont('helvetica', 'bold');
                doc.text(String(lista['alunos'][aluno]['num']).padStart(2, '0'), 1.05, y, 'center');
                ultimo = lista['alunos'][aluno]['num'];
                doc.setFont('helvetica', 'normal');        
                
                doc.line(0.7, y + 0.1, 20.3, y + 0.1);
            }

            var ra = parseInt(lista['alunos'][aluno]['ra'].replaceAll('.', '').slice(0, -2));

            doc.setFontSize(7);
            try {
                if (lista['alunos'][aluno]['fim_mat'] == "") {

                    if (lista['disciplinas'][item]['notas'][ra]['nota'] < 5) {
                        doc.setTextColor(255, 0, 0);
                    }

                    doc.text(String(lista['disciplinas'][item]['notas'][ra]['nota']), center - (dif / 3), y - 0.05, 'center');
                    doc.line(center - (dif / 3) + ((dif / 3) / 2), y - 0.4, center - (dif / 3) + ((dif / 3) / 2), y + 0.1);
    
                    doc.setTextColor(0, 0, 0);
    
                    doc.text(String(lista['disciplinas'][item]['notas'][ra]['falta']), center, y - 0.05, 'center');
                    doc.line(center + (dif / 3) - ((dif / 3) / 2), y - 0.4, center + (dif / 3) - ((dif / 3) / 2), y + 0.1);
    
                    doc.text(String(lista['disciplinas'][item]['notas'][ra]['ac']), center + (dif / 3), y - 0.05, 'center');
                } else {
                    doc.setTextColor(255, 0, 0);
                    doc.text(lista['alunos'][aluno]['mat'], center, y - 0.05, 'center');
                    doc.setTextColor(0, 0, 0);                    
                }
            } catch (error) {
                doc.setTextColor(255, 0, 0);
                doc.text(lista['alunos'][aluno]['mat'], x, y - 0.05, 'center');
                doc.setTextColor(0, 0, 0);
            }

            y += 0.5; 
        }

        diferenca = 48 - lista['alunos'].length;

        for (let i = 0; i < diferenca; i++) {
            if (item == 0) {
                doc.setFontSize(11);
                doc.setFont('helvetica', 'bold');
                ultimo += 1;
                doc.text(String(ultimo).padStart(2, '0'), 1.05, y, 'center');
                doc.setFont('helvetica', 'normal');        
                
                doc.line(0.7, y + 0.1, 20.3, y + 0.1);
            }

            doc.line(center - (dif / 3) + ((dif / 3) / 2), y - 0.4, center - (dif / 3) + ((dif / 3) / 2), y + 0.1);
            doc.line(center + (dif / 3) - ((dif / 3) / 2), y - 0.4, center + (dif / 3) - ((dif / 3) / 2), y + 0.1);
            
            y += 0.5; 
        } 
        
        // após tudo isso será necessário inserir os dados dos professores e das aulas dadas e previstas
           
        
        if (item == 0) {
            doc.setLineWidth(0.05);

            doc.setFontSize(7);
            doc.setFont('helvetica', 'bold');
            doc.text('Prof', 1.05, y, 'center');
            doc.line(0.7, y - 0.4, 20.3, y - 0.4);
            doc.line(0.7, y + 0.2, 20.3, y + 0.2);

            doc.setLineWidth(0.01);              
        }

        doc.setFont('helvetica', 'normal');
        font_size = 8;
        doc.setFontSize(font_size);

        //console.log(lista['disciplinas'][item]['nome_ata']);
        tamanho = doc.getTextWidth(lista['disciplinas'][item]['nome_ata']);

        vertical = y;

        while (tamanho > dif) {
            font_size -= 1;
            vertical -= 0.02;
            doc.setFontSize(font_size);
            tamanho = doc.getTextWidth(lista['disciplinas'][item]['nome_ata']);
        }

        doc.text(lista['disciplinas'][item]['nome_ata'], center, vertical, 'center');

        y += 0.5; 

        if (item == 0) {
            doc.setFontSize(8);
            doc.setFont('helvetica', 'bold');
            doc.text('AD', 1.05, y + 0.07, 'center');
            doc.setFont('helvetica', 'normal');
        }

        doc.setFontSize(10);
        doc.text(String(lista['disciplinas'][item]['aulas_dadas']), center, y + 0.07, 'center');

        y += 0.2;

        // desenhar linha no final
        if (item == 0) {
            doc.setLineWidth(0.05);
            doc.line(1.4, lin_inicial - 0.4, 1.4, y);
            doc.line(0.7, y, 20.3, y);
            doc.setLineWidth(0.01);
        }

        if (item < lista['disciplinas'].length - 1) {
            doc.setLineWidth(0.04);
            doc.line(center + (dif / 3) + ((dif / 3) / 2), lin_inicial - 0.4, center + (dif / 3) + ((dif / 3) / 2), y);
            y = lin_inicial
            doc.setLineWidth(0.01);
        }

        x += dif;
        doc.setFontSize(11);
    }    


    // após fazer isso desenhar as bordas finais
    doc.setLineWidth(0.05);
    doc.line(0.7, 0.7, 0.7, y); // borda esquerda
    doc.line(20.3, 0.7, 20.3, y); // borda direita

    doc.addPage();

    // agora gerar o verso do mapão
    x = 1;
    y = 1.5;
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(255, 0, 0);
    
    var splitText = doc.splitTextToSize('BIMESTRE', 0.3);

    doc.setFontSize(13);
    doc.text(bimestre + 'º', x, y, 'center');
    y += 1;

    doc.setFontSize(11);
    for (var i = 0, length = splitText.length; i < length; i++) {
        // loop thru each line and increase
        doc.text(splitText[i], x, y, 'center')
        y += 0.5;
      }

    doc.setLineWidth(0.01);
    doc.line(0.7, 6.2, 1.3, 6.2);

    y += 0.2;

    doc.setTextColor(0, 0, 0);
    doc.text("Nº", x, y, 'center');
    //doc.line(x + 0.3, 1, x + 0.3, y + 0.2);

    //doc.line(1.4, 0.5, 11, 0.5);


    doc.setFont('helvetica', 'normal');
    
    x = 1.3;
    dif = (10 - x) / total;

    lin_inicial = y;
    limite = 11;

    doc.setFontSize(10);
    for (var disc in lista['disciplinas']) {
        center = x + (dif / 2);

        if (lista['turma']['tipo_ensino'] != "Itinerário Formativo Regular") {
            doc.text(lista['disciplinas'][disc]['completo'], (center + 0.1), y, null, 90);
        } else {
            doc.text(lista['disciplinas'][disc]['desc_disc'], (center + 0.1), y, null, 90);
        }
        
        if (disc == 0) {
            doc.line(0.7, y + 0.15, limite, y + 0.15);
        }

        y += 0.5;

        doc.setFontSize(9);
        for (var aluno in lista['alunos']) {
            doc.setFont('helvetica', 'bold');

            if (disc == 0) {
                doc.text(String(lista['alunos'][aluno]['num']).padStart(2, '0'), 1, y, 'center');
                doc.line(0.7, y + 0.1, limite, y + 0.1);
                ultimo = lista['alunos'][aluno]['num'];
            }
            
            var ra = parseInt(lista['alunos'][aluno]['ra'].replaceAll('.', '').slice(0, -2));
            doc.setFont('helvetica', 'normal');
            //doc.setFontSize(7);
            try {

                if (lista['alunos'][aluno]['fim_mat'] == "") {
                    if (lista['disciplinas'][disc]['notas'][ra]['nota'] < 5) {
                        doc.setTextColor(255, 0, 0);
                    }
    
                    doc.text(String(lista['disciplinas'][disc]['notas'][ra]['nota']), center, y, 'center');
                    //doc.line(x - (dif / 3) + ((dif / 3) / 2), y - 0.4, x - (dif / 3) + ((dif / 3) / 2), y + 0.1);
                    doc.setTextColor(0, 0, 0);
                } else {
                    doc.text('-', center, y - 0.05, 'center');
                }

            } catch (error) {
                doc.text('-', center, y - 0.05, 'center');
            }            

            y += 0.45;
        }

        for (let i = 0; i < diferenca; i++) {
            if (disc == 0) {
                //doc.setFontSize(11);
                doc.setFont('helvetica', 'bold');
                ultimo += 1;
                doc.text(String(ultimo).padStart(2, '0'), 1, y, 'center');
                //doc.setFont('helvetica', 'normal');        
                
                doc.line(0.7, y + 0.1, limite, y + 0.1);
            }
            
            y += 0.45; 
        }         

        if (disc == 0) {
            doc.line(1.3, 1, 1.3, y - 0.35);
        }

        if (disc == total - 1) {
            doc.setLineWidth(0.05);
        }

        doc.line(center + (dif / 2), 1, center + (dif / 2), y - 0.35);

        doc.setLineWidth(0.01);

        x += dif;
        lin_final = y;        
        y = lin_inicial;
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(10);
    }

    //x -= dif;

    x += 0.5;

    // após a digitação das notas será digitada as faltas
    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    doc.text("FALTAS", x, y - 0.5, null, 90);
    doc.text("% FREQUÊNCIA", x + 0.7, y - 0.5, null, 90);
    doc.text("AUSÊNCIAS COMPENSADAS", x + 1.4, y - 0.5, null, 90);
    doc.text("OBSERVAÇÕES", x + 2.8, y - 0.5, null, 90);

    doc.line(x - 0.52, y + 0.15, x + 3.7, y + 0.15);

    y += 0.5;

    for (var aluno in lista['alunos']) {
        try {

            if (lista['alunos'][aluno]['fim_mat'] == "") {
                ra = parseInt(lista['alunos'][aluno]['ra'].replaceAll('.', '').slice(0, -2));
                doc.text(lista['freq'][ra]['total_faltas'], x - 0.15, y, 'center');
    
                if (lista['freq'][ra]['freq'] < 75) {
                    doc.setTextColor(255, 0, 0);
                }
    
                doc.text(lista['freq'][ra]['freq'], x + 0.55, y, 'center');
                doc.setTextColor(0, 0, 0);
                doc.text(lista['freq'][ra]['ac'], x + 1.25, y, 'center');
    
                doc.setFont('helvetica', 'normal');
                doc.setFontSize(7);
                doc.text(lista['alunos'][aluno]['dificuldade'], x + 2.65, y - 0.04, 'center');
                doc.setFont('helvetica', 'bold');
                doc.setFontSize(10);
            } else {
                doc.text('-', x - 0.15, y, 'center');
                doc.text('-', x + 0.55, y, 'center');
                doc.text('-', x + 1.25, y, 'center');
                doc.setTextColor(255, 0, 0);
                doc.setFontSize(7);
                doc.text(lista['alunos'][aluno]['mat'], x + 2.65, y - 0.04, 'center');
                doc.setTextColor(0, 0, 0);
                doc.setFontSize(10);                
            }



        } catch (error) {
            doc.text('-', x - 0.15, y, 'center');
            doc.text('-', x + 0.55, y, 'center');
            doc.text('-', x + 1.25, y, 'center');
            doc.setTextColor(255, 0, 0);
            doc.setFontSize(7);
            doc.text(lista['alunos'][aluno]['mat'], x + 2.65, y - 0.04, 'center');
            doc.setTextColor(0, 0, 0);
            doc.setFontSize(10);
        }     
        doc.line(x - 0.52, y + 0.1, x + 3.7, y + 0.1);
        
        y += 0.45;
    }

    for (let i = 0; i < diferenca; i++) {
        doc.line(x - 0.52, y + 0.1, x + 3.7, y + 0.1);
        
        y += 0.45; 
    } 
    
    // desenhar bordas da frequência
    doc.setLineWidth(0.05);
    doc.line(x + 0.2, 1, x + 0.2, y - 0.35);
    doc.line(x + 0.9, 1, x + 0.9, y - 0.35);
    doc.line(x + 1.6, 1, x + 1.6, y - 0.35);
    doc.line(x + 3.7, 1, x + 3.7, y - 0.35);

    // desenhar a parte direita da ata

    var dt = new Date(fim_bim.substring(0, 4), parseInt(fim_bim.substring(5, 7)) - 1, parseInt(fim_bim.substring(8, 10)));


    // texto da ata

    x += 7.2;

    var in_x = x;

    y = 1.5;
    doc.text('CONSELHO DE CLASSE', x, y, 'center');
    doc.setFont('helvetica', 'normal');
    y += 1;
    x -= 1.4;
    
    if (dt.getDate() == 1) {
        doc.text('No primeiro dia do mês de', x - 0.55, y);
    } else {
        doc.text('Aos ', x, y);
        tamanho = doc.getTextWidth('Aos ');
        doc.setFont('helvetica', 'bold');
        x += tamanho;
        doc.text(String(dt.getDate()).padStart(2, '0'), x, y);
        tamanho = doc.getTextWidth(String(dt.getDate()).padStart(2, '0'));
        doc.setLineWidth(0.01);
        doc.line(x, y + 0.05, x + tamanho, y + 0.05);
        x += tamanho;
        doc.setFont('helvetica', 'normal');
        doc.text(' dias do mês de ', x, y);
    }

    y += 0.6;
    x = in_x - 1.3;

    doc.setFont('helvetica', 'bold');
    doc.text(meses[dt.getMonth()], x + 0.25, y, 'center');
    doc.line(x - 1, y + 0.05, x + 1.5, y + 0.05);
    doc.setFont('helvetica', 'normal');
    x += 1.5;
    doc.text(" de ", x, y);
    x += doc.getTextWidth(" de ");
    doc.setFont('helvetica', 'bold');
    doc.text('2023', x + 0.77, y, 'center');
    doc.line(x, y + 0.05, x + 1.55, y + 0.05);

    y += 0.6;
    x = in_x;

    doc.setFont('helvetica', 'normal');
    doc.text('realizou-se   o   Conselho  de', x + 2.2, y, 'right');

    y += 0.6;

    doc.text('Classe e Série dos alunos da', x + 2.2, y, 'right');

    y += 0.6;

    doc.setTextColor(255, 0, 0);
    doc.setFont('helvetica', 'bold');
    x -= 2.4;
    doc.text(lista['turma']['nome_turma'], x, y);
    tamanho = doc.getTextWidth(lista['turma']['nome_turma']);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(0, 0, 0);
    doc.text(" do", x + tamanho, y);

    y += 0.6;

    doc.setFont('helvetica', 'bold');

    if (lista['turma']['tipo_ensino'] != "Itinerário Formativo Regular") {
        doc.text(lista['turma']['tipo_ensino'], x, y);
        tamanho = doc.getTextWidth(lista['turma']['tipo_ensino']);
    } else {
        doc.text("IF - Regular", x, y);
        tamanho = doc.getTextWidth("IF - Regular");        
    }


    doc.setFont('helvetica', 'normal');
    doc.text(" da", x + tamanho, y);

    y += 0.6;
    
    doc.text("EE Profª Alice Vilela Galvão", x, y);

    y += 0.6;
    doc.text('Canas, ' + fim_bim.substring(8, 10) + '/' + fim_bim.substring(5, 7) + '/' + fim_bim.substring(0, 4), x + 4.5, y, 'right');

    y += 0.6;
    x = in_x - 2.7;

    // lista dos professores

    doc.setFontSize(5);
    doc.line(x, y - 0.2, x + 5, y - 0.2);
    doc.text('Matéria', x, y);
    x += 1.5;
    doc.text('Professor', x, y);
    x += 2;
    doc.text('Assinatura', x, y);
    
    y += 0.4;

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(8);
    for (item in lista['disciplinas']) {
        x = in_x - 2.7;

        doc.setLineDash([0.05, 0.05]);
        doc.line(x, y + 0.2, x + 5, y + 0.2);

        if (lista['turma']['tipo_ensino'] != "Itinerário Formativo Regular") {
            doc.text(lista['disciplinas'][item]['desc_disc'], x, y);
        } else {
            doc.setFontSize(6);
            doc.text(lista['disciplinas'][item]['desc_disc'], x, y);
            doc.setFontSize(8);
        }
        
        
        x += 1.5;
        doc.text(lista['disciplinas'][item]['nome_ata'], x, y); 
        x += 2;

        y += 0.6    
    }

    // observações

    x = in_x - 2.7;
    y += 0.3;
    doc.text('OBSERVAÇÕES', x, y);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(6);
    for (item in dificuldades) {
        y += 0.4;
        doc.setFont('helvetica', 'bold');
        doc.text(String(dificuldades[item]['id']).padStart(2, '0'), x, y);
        doc.setFont('helvetica', 'normal');
        doc.text(' - ' + dificuldades[item]['title'], x + doc.getTextWidth('00'), y);
        doc.line(x, y + 0.14, x + 5, y + 0.14);
        //console.log(dificuldades[item]);
    }

    // assinaturas

    y += 1.5;

    doc.setFontSize(8);
    doc.setLineDash([]);
    doc.line(x, y - 0.3, x + 5, y - 0.3);
    doc.text("Coordenador Pedagógico", x + 2.5, y, 'center');

    y += 1.5;
    doc.line(x, y - 0.3, x + 5, y - 0.3);
    doc.text("Diretor de Escola", x + 2.5, y, 'center');


    // após escrever tudo gerar as bordas finais
    doc.setLineWidth(0.05);

    // borda esquerda
    doc.line(0.68, 1, 0.68, lin_final - 0.31);
    // borda inferior
    doc.line(0.68, lin_final - 0.33, x + 5.5, lin_final - 0.33);
    // borda direita
    doc.line(x + 5.5, 1, x + 5.5, lin_final - 0.31);
    // borda superior
    doc.line(0.68, 1, x + 5.5, 1);

    window.open(doc.output('bloburl'), '_blank');    
}

function gerarListaPilotoPadrao(url_logo, desc_turma, desc_tipo_ensino, desc_duracao, num_classe, desc_periodo, inicio_turma, fim_turma, desc_total, table) {
    var doc = new jsPDF({
        orientation: 'portrait',
        unit: 'cm',
        format: 'a4'
    });

    var img = new Image();

    img.src = url_logo;
    doc.addImage(img, 'png', 0, -1, 6, 6);    

    doc.setFont('BebasKai', 'normal');
    doc.setFontSize(20);
    y = 1;
    x = 2.7;
    doc.text(x, y, 'Lista Geral - ');

    textWidth = x + doc.getTextWidth('Lista Geral - ');

    doc.setTextColor(255, 0, 0);
    doc.text(textWidth, y, desc_turma);

    textWidth = textWidth + doc.getTextWidth(desc_turma);    

    doc.setTextColor(0, 0, 0);
    doc.text(textWidth, y, " - " +  desc_tipo_ensino);

    textWidth = textWidth + doc.getTextWidth(" - " +  desc_tipo_ensino);

    doc.text(textWidth, y, " - " +  desc_duracao);    

    x = 5.2;
    y = 1.6

    doc.setTextColor(0, 112, 192);
    doc.text('Dados de Matrícula', 15.3, 3)
    doc.setTextColor(0, 0, 0);

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(12);
    doc.text("Número da Classe:", x , y);
    textWidth =  doc.getTextWidth("Número da Classe:") + x + 0.2;
    doc.setFont('helvetica', 'normal');
    doc.text(num_classe, textWidth, y);

    y += 0.6;

    doc.setFont('helvetica', 'bold');
    doc.text("Período:", x , y);
    textWidth =  doc.getTextWidth("Período:") + x + 0.2;
    doc.setFont('helvetica', 'normal');
    doc.text(desc_periodo, textWidth, y);      

    y += 0.6;

    doc.setFont('helvetica', 'bold');
    doc.text("Duração:", x , y);
    textWidth =  doc.getTextWidth("Duração:") + x + 0.2;
    doc.setFont('helvetica', 'normal');
    doc.text(inicio_turma + ' até ' + fim_turma, textWidth, y); 

    y += 0.6;

    doc.setFont('helvetica', 'bold');
    doc.text("Total:", x , y);
    textWidth =  doc.getTextWidth("Total:") + x + 0.2;
    doc.setFont('helvetica', 'normal');
    doc.text(desc_total, textWidth, y);    
    
    // agora que o bicho pega
    x_num = 0.5;
    x_rm = 1.2;
    x_serie = 2.3;
    x_nome = 3.75;
    x_ra = 13.9;
    x_mat = 16.5;
    x_mov = 18.7;

    y = 4;

    // borda do cabecalho
    doc.setLineWidth(0.05);
    doc.setFillColor(254, 254, 226);
    doc.rect(0.4, 3.6, 20.2, 0.5, 'F');
    doc.line(0.4, 3.6, 20.6, 3.6);

    // desenha o cabeçalho
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(10);
    doc.text('Nº', x_num, y);
    doc.text('RM', x_rm, y);
    doc.text('SÉRIE', x_serie, y);
    tamanho = doc.getTextWidth('SÉRIE');
    doc.text('NOME', x_nome, y);
    //doc.text('NASC.', x_nasc, y);
    doc.text("RA", x_ra, y);
    doc.text("MATR.", x_mat, y);
    doc.text("FIM MATR.", x_mov, y);

    doc.setLineWidth(0.01);
    doc.line(0.4, y + 0.13, 20.6, y + 0.13);

    doc.setFont('helvetica', 'normal');    

    var cont = 0;

    for(let i = 0; i < table.length; i++) {

        if (table[i][12] != "ATIVO") {
            doc.setTextColor(255, 0, 0);
        } else {
            doc.setTextColor(0, 0, 0);
        }

        
        doc.setFont('helvetica', 'normal');
        y += 0.49;

        doc.text(table[i][0].padStart(2, "0"), x_num, y);   
        doc.text(table[i][1], x_rm, y)
        doc.text(table[i][3], x_serie + (tamanho / 2) - (doc.getTextWidth(table[i][3]) / 2), y);
        doc.text(PriMaiuscula(table[i][4]), x_nome, y);
        //doc.text(table[i][5]['display'], x_nasc, y);
        doc.text(table[i][2], x_ra, y);

        if (table[i][11]['display'] != $("#fimTurma").text()) {
            doc.setFont('helvetica', 'bold');
            doc.text(table[i][11]['display'], x_mov, y);
        }

        if (table[i][12] != "ATIVO") {
            doc.setTextColor(0, 112, 192);
            doc.setFont('helvetica', 'bold');
            doc.text(table[i][12], x_mat, y);
        } else if (table[i][10]['display'] != $("#inicioTurma").text()) {
            doc.setTextColor(0, 112, 192);
            doc.setFont('helvetica', 'bold');
            doc.text(table[i][10]['display'], x_mat, y);
        }

        doc.setLineWidth(0.01);

        if (i == table.length - 1 && i == 50) {
            doc.setLineWidth(0.05);
        }

        doc.line(0.4, y + 0.13, 20.6, y + 0.13);
        cont += 1;

    }

    var dif = 51 - cont;

    if (dif > 0) {
        var num = parseInt(table[table.length - 1][0]) + 1;
        doc.setFont('helvetica', 'normal');
        doc.setLineWidth(0.01);
        doc.setTextColor(0, 0, 0);

        for(let i = 0; i < dif; i++) {
            y += 0.49;

            doc.text(String(num).padStart(2, "0"), x_num, y);
            num += 1;

            if (i == dif - 1) {
                doc.setLineWidth(0.05);
            }

            doc.line(0.4, y + 0.13, 20.6, y + 0.13);                    
        }
    }

    doc.setLineWidth(0.05);
    doc.line(0.4, 3.6, 0.4, y + 0.13);
    doc.line(x_rm - 0.2, 3.6, x_rm - 0.2, y + 0.13);
    doc.line(x_nome - 0.2, 3.6, x_nome - 0.2, y + 0.13);
    doc.line(x_serie - 0.2, 3.6, x_serie - 0.2, y + 0.13);
    doc.line(x_ra - 0.2, 3.6, x_ra - 0.2, y + 0.13);
    doc.line(x_mat - 0.2, 3.6, x_mat - 0.2, y + 0.13);
    doc.line(x_mov - 0.2, 3.6, x_mov - 0.2, y + 0.13);
    doc.line(20.6, 3.6, 20.6, y + 0.13);

    doc.setFont('courier', 'bold');
    doc.setTextColor(0, 0, 0);
    doc.text("Lista gerada em " + ((new Date()).toLocaleDateString('pt-BR')), 15, 3.4);

    // gerar segunda folha
    doc.addPage();

    doc.addImage(img, 'png', 0, -1, 6, 6);    

    doc.setFont('BebasKai', 'normal');
    doc.setFontSize(20);
    y = 1;
    x = 2.7;
    doc.text(x, y, 'Lista Geral - ');

    textWidth = x + doc.getTextWidth('Lista Geral - ');

    doc.setTextColor(255, 0, 0);
    doc.text(textWidth, y, desc_turma);

    textWidth = textWidth + doc.getTextWidth(desc_turma);    

    doc.setTextColor(0, 0, 0);
    doc.text(textWidth, y, " - " +  desc_tipo_ensino);

    textWidth = textWidth + doc.getTextWidth(" - " +  desc_tipo_ensino);

    doc.text(textWidth, y, " - " +  desc_duracao);    

    x = 5.2;
    y = 1.6

    doc.setTextColor(0, 108, 49);
    doc.text('Dados Pessoais', 15.9, 3)
    doc.setTextColor(0, 0, 0);

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(12);
    doc.text("Número da Classe:", x , y);
    textWidth =  doc.getTextWidth("Número da Classe:") + x + 0.2;
    doc.setFont('helvetica', 'normal');
    doc.text(num_classe, textWidth, y);

    y += 0.6;

    doc.setFont('helvetica', 'bold');
    doc.text("Período:", x , y);
    textWidth =  doc.getTextWidth("Período:") + x + 0.2;
    doc.setFont('helvetica', 'normal');
    doc.text(desc_periodo, textWidth, y);      

    y += 0.6;

    doc.setFont('helvetica', 'bold');
    doc.text("Duração:", x , y);
    textWidth =  doc.getTextWidth("Duração:") + x + 0.2;
    doc.setFont('helvetica', 'normal');
    doc.text(inicio_turma + ' até ' + fim_turma, textWidth, y); 

    y += 0.6;

    doc.setFont('helvetica', 'bold');
    doc.text("Total:", x , y);
    textWidth =  doc.getTextWidth("Total:") + x + 0.2;
    doc.setFont('helvetica', 'normal');
    doc.text(desc_total, textWidth, y);    
    
    // agora que o bicho pega
    x_num = 0.5;
    //x_serie = 1.2;
    x_nome = 1.2;
    x_nasc = 10.7;
    x_sexo = 12.9;
    x_cpf = 14.3;
    x_rg = 17.4;

    y = 4;

    // borda do cabecalho
    doc.setLineWidth(0.05);
    doc.setFillColor(254, 254, 226);
    doc.rect(0.4, 3.6, 20.2, 0.5, 'F');
    doc.line(0.4, 3.6, 20.6, 3.6);

    // desenha o cabeçalho
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(10);
    doc.text('Nº', x_num, y);
    //doc.text('SÉRIE', x_serie, y);
    //tamanho = doc.getTextWidth('SÉRIE');
    doc.text('NOME', x_nome, y);
    doc.text('NASC.', x_nasc, y);
    doc.text('SEXO', x_sexo, y);
    tamanhoS = doc.getTextWidth('SEXO');
    doc.text("CPF", x_cpf, y);
    doc.text("RG", x_rg, y);

    doc.setLineWidth(0.01);
    doc.line(0.4, y + 0.13, 20.6, y + 0.13);

    doc.setFont('helvetica', 'normal');    

    var cont = 0;    

    for(let i = 0; i < table.length; i++) {

        if (table[i][12] != "ATIVO") {
            doc.setTextColor(255, 0, 0);
        } else {
            doc.setTextColor(0, 0, 0);
        }

        
        doc.setFont('helvetica', 'normal');
        y += 0.49;

        doc.text(table[i][0].padStart(2, "0"), x_num, y);   
        //doc.text(table[i][3], x_serie + (tamanho / 2) - (doc.getTextWidth(table[i][3]) / 2), y)
        doc.text(PriMaiuscula(table[i][4]), x_nome, y);
        doc.text(table[i][5]['display'], x_nasc, y);
        doc.text(table[i][7], x_sexo + (tamanhoS / 2) - (doc.getTextWidth(table[i][7]) / 2), y)
        doc.text(table[i][9], x_cpf, y)
        doc.text(table[i][8], x_rg, y)

        doc.setLineWidth(0.01);

        if (i == table.length - 1 && i == 50) {
            doc.setLineWidth(0.05);
        }

        doc.line(0.4, y + 0.13, 20.6, y + 0.13);
        cont += 1;

    }

    var dif = 51 - cont;

    if (dif > 0) {
        var num = parseInt(table[table.length - 1][0]) + 1;
        doc.setFont('helvetica', 'normal');
        doc.setLineWidth(0.01);
        doc.setTextColor(0, 0, 0);

        for(let i = 0; i < dif; i++) {
            y += 0.49;

            doc.text(String(num).padStart(2, "0"), x_num, y);
            num += 1;

            if (i == dif - 1) {
                doc.setLineWidth(0.05);
            }

            doc.line(0.4, y + 0.13, 20.6, y + 0.13);                    
        }
    }

    doc.setLineWidth(0.05);
    doc.line(0.4, 3.6, 0.4, y + 0.13);
    //doc.line(x_serie - 0.2, 3.6, x_rm - 0.2, y + 0.13);
    doc.line(x_nome - 0.2, 3.6, x_nome - 0.2, y + 0.13);
    doc.line(x_nasc - 0.2, 3.6, x_nasc - 0.2, y + 0.13);
    doc.line(x_sexo - 0.2, 3.6, x_sexo - 0.2, y + 0.13);
    doc.line(x_cpf - 0.2, 3.6, x_cpf - 0.2, y + 0.13);
    doc.line(x_rg - 0.2, 3.6, x_rg - 0.2, y + 0.13);
    doc.line(20.6, 3.6, 20.6, y + 0.13);

    doc.setFont('courier', 'bold');
    doc.setTextColor(0, 0, 0);
    doc.text("Lista gerada em " + ((new Date()).toLocaleDateString('pt-BR')), 15, 3.4);

    window.open(doc.output('bloburl'), '_blank');      

}

function gerarListaIF(lista) {

    var doc = new jsPDF({
        orientation: 'portrait',
        unit: 'cm',
        format: 'a4'
    });

    extra = 0;

    for (turma in lista) {
        //console.log(lista[turma]);
        doc.setFontSize(20);
        doc.setFont('helvetica', 'bold');

        var splitTitle = doc.splitTextToSize(lista[turma]['info']['cat_if'], 15);

        doc.setFillColor(254, 254, 226);

        if (splitTitle.length > 1) {
            altura = 2.2 + extra;
        } else {
            altura = 1.5 + extra;
        }

        doc.rect(0.4, extra + 1, 20.2, altura - extra, 'F');    

        
        //console.log(splitTitle);
        tamanho = doc.getTextWidth(splitTitle[0]);
        doc.text(splitTitle, 10.5, extra + 2, 'center');    

        y = altura + 1.5;

        doc.setFontSize(14);
        doc.setFont('helvetica', 'bold');

        doc.setFillColor(255, 192, 0);
        doc.rect(0.4, y - 0.5, 20.2, 0.7, 'F');   

        if (lista[turma]['info']['nome_turma'].search('\n') > 0) {
            doc.setFillColor(254, 254, 226);
            doc.rect(0.4, y + 0.9, 20.2, 0.5, 'F');
        } else {
            doc.setFillColor(254, 254, 226);
            doc.rect(0.4, y + 0.2, 20.2, 0.5, 'F');
        }


        
        doc.setLineWidth(0.01);
        doc.line(0.4, altura + 1, 20.6, altura + 1)

        if (lista[turma]['info']['nome_turma'].search('\n') > 0) {
            y += 0.7;
            altura += 0.7;

            doc.setFillColor(201, 241, 255);
            doc.rect(0.4, y - 0.5, 20.2, 0.7, 'F');

            doc.text(lista[turma]['info']['nome_turma'], 10.5, y - 0.65, {lineHeightFactor: 1.4, align:"center"});            
        } else {
            doc.text(lista[turma]['info']['nome_turma'], 10.5, y, "center");            
        }


        y += 0.6;

        // agora que o bicho pega
        x_num = 0.5;
        x_rm = 1.2;
        x_nome = 2.3;
        x_ra = 13.9;
        x_mat = 16.5;
        x_mov = 18.7;

        // desenha o cabeçalho
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(10);
        doc.text('Nº', x_num, y);
        doc.text('RM', x_rm, y);
        tamanho = doc.getTextWidth('SÉRIE');
        doc.text('NOME', x_nome, y);
        //doc.text('NASC.', x_nasc, y);
        doc.text("RA", x_ra, y);
        doc.text("SIT.", x_mat, y);
        doc.text("TURMA", x_mov, y);

        doc.line(0.4, y - 0.4, 20.6, y - 0.4)

        y += 0.5;
        cont = 0;

        doc.setFont('helvetica', 'normal');
        for (alunos in lista[turma]['lista']) {

            var nome_turma = lista[turma]['lista'][alunos]['turma'];

            if (lista[turma]['lista'][alunos]['sit'] != 'ATIVO') {
                doc.setTextColor(255, 0, 0);
            } else {
                //console.log(lista[turma]['esquema_cores'][nome_turma]);
                doc.setTextColor(lista[turma]['esquema_cores'][nome_turma]['r'], lista[turma]['esquema_cores'][nome_turma]['g'], lista[turma]['esquema_cores'][nome_turma]['b']);
            }

            doc.text(String(lista[turma]['lista'][alunos]['num_chamada']).padStart(2, "0"), x_num, y);
            doc.text(lista[turma]['lista'][alunos]['rm'], x_rm, y);
            doc.text(lista[turma]['lista'][alunos]['ra'], x_ra, y);
            doc.text(PriMaiuscula(lista[turma]['lista'][alunos]['nome']), x_nome, y);
            
            if (lista[turma]['lista'][alunos]['sit'] != 'ATIVO') {
                doc.text(lista[turma]['lista'][alunos]['sit'], x_mat, y);
            }

            doc.text(lista[turma]['lista'][alunos]['turma'], x_mov, y);
            
            doc.line(0.4, y + 0.13, 20.6, y + 0.13);

            y += 0.5;
            cont += 1;
        }


        if(lista[0]['qtd_classes'] > 1) {

            var dif = 48 - cont;

            if (dif > 0) {
    
                /*console.log(lista);
                console.log(lista[0]['lista']);*/
    
                var num = parseInt(lista[turma]['lista'][[lista[turma]['lista'].length - 1]]['num_chamada']) + 1;
                doc.setFont('helvetica', 'normal');
                doc.setLineWidth(0.01);
                doc.setTextColor(0, 0, 0);
    
                //for(let i = 0; i < dif; i++) {
                while (y < 28.5) {
                    doc.text(String(num).padStart(2, "0"), x_num, y);
                    num += 1;
    
                    if ((y + 0.5) > 28.5) {
                        doc.setLineWidth(0.05);
                    }
    
                    doc.line(0.4, y + 0.13, 20.6, y + 0.13);                    
    
                    y += 0.5;
                    //console.log(y);
                }
            }            

        } else {

            var dif = 21 - cont;

            if (dif > 0) {
    
                /*console.log(lista);
                console.log(lista[0]['lista']);*/
    
                var num = parseInt(lista[turma]['lista'][[lista[turma]['lista'].length - 1]]['num_chamada']) + 1;
                doc.setFont('helvetica', 'normal');
                doc.setLineWidth(0.01);
                doc.setTextColor(0, 0, 0);
    
                for(let i = 0; i < dif; i++) {
                //while (y < 12) {
                    doc.text(String(num).padStart(2, "0"), x_num, y);
                    num += 1;
    
                    if (i == dif - 1) {
                        doc.setLineWidth(0.05);
                    }
    
                    doc.line(0.4, y + 0.13, 20.6, y + 0.13);                    
    
                    y += 0.5;
                    //console.log(y);
                }
            }             

        }



        doc.setLineWidth(0.05);
        doc.line(0.4, 1, 20.6, 1);
        doc.line(0.4, 1, 0.4, y - 0.35);
        doc.line(0.4, altura + 2.2, 20.6, altura + 2.2);
        
        //doc.line(x_serie - 0.2, 3.6, x_rm - 0.2, y + 0.13);
        //doc.line(x_num - 0.2, 3.6, x_num - 0.2, y + 0.13);
        doc.line(x_rm - 0.2, altura + 1.7, x_rm - 0.2, y - 0.35);
        doc.line(x_nome - 0.2, altura + 1.7, x_nome - 0.2, y - 0.35);
        doc.line(x_ra - 0.2, altura + 1.7, x_ra - 0.2, y - 0.35);
        doc.line(x_mat - 0.2, altura + 1.7, x_mat - 0.2, y - 0.35);
        doc.line(x_mov - 0.2, altura + 1.7, x_mov - 0.2, y - 0.35);
        doc.line(20.6, 1, 20.6, y - 0.35);


        doc.setFont('courier', 'bold');
        doc.setTextColor(0, 0, 0);


        if(lista[0]['qtd_classes'] > 1) {
            doc.text("Lista gerada em " + ((new Date()).toLocaleDateString('pt-BR')), 0.4, y);            
        } else if(parseInt(turma) == lista.length - 1) {
            doc.text("Lista gerada em " + ((new Date()).toLocaleDateString('pt-BR')), 0.4, y);            
        }

        if (parseInt(turma) < lista.length - 1) {
            if(lista[0]['qtd_classes'] > 1) {
                doc.addPage();
            } else {
                extra = y - 1.35;
            }
        }
    }

    window.open(doc.output('bloburl'), '_blank');

}

function declaracaoTransferencia(url_brasao, nome, rg, cpf, ra, nascimento, serie, ensino, nome_assinatura, assinatura_rg, cargo_assinatura) {

    var doc = new jsPDF({
        orientation: 'portrait',
        unit: 'pt',
        format: 'a4'
    });

    var img = new Image();

    img.src = url_brasao;
    doc.addImage(img, 'svg', 40, 20, 80, 90);

    x = 130;
    y = 40;

    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.text('GOVERNO DO ESTADO DE SÃO PAULO', x, y);
    y += 15;
    doc.text('SECRETARIA DE ESTADO DA EDUCAÇÃO', x, y)
    y += 15;
    doc.text('UNIDADE REGIONAL DE ENSINO DE GUARATINGUETÁ', x, y)
    y += 15;
    doc.text('EE MAJOR HERMÓGENES', x, y)
    y += 15;
    doc.text('Rua Ipiranga, S/N - Vila Paulista – Cruzeiro', x, y)
    
    y += 100;

    doc.setFontSize(18);
    doc.text('DECLARAÇÃO DE TRANSFERÊNCIA', 297.64, y, 'center');

    var texto = "           Declaro para os devidos fins que, **" + nome + ", **";

    if (rg != "-") {
        texto += "RG: " + rg;
    } else if(cpf != '-') {
        texto += "CPF: " + cpf;
    } else {
        texto += "RA: " + ra + ", nascido em " + nascimento;
    }
    
    if (ensino == "Ensino Fundamental") {
        texto += " solicitou transferência com direito a matricular-se no **" + getNumberSerie(parseInt(serie)) + " do " + ensino + ".**";    
    } else {
        texto += " solicitou transferência com direito a matricular-se na **" + serie + "ª série do " + ensino + ".**";
    }

    y += 130;

    //console.log(texto);

    doc.setFontSize(14);
    y = printCharacters(doc, texto, y, 75, 445.28);

    y += 100;

    //doc.setFontSize(12);
    doc.setFont('helvetica', 'normal');
    doc.text(data_extensa(), 520.28, y, 'right');    

    if (nome_assinatura != "Sem assinatura") {
        y += 200;
        doc.setFontSize(9);

        doc.setLineWidth(0.7); // Set line thickness
        doc.line(197.64, y - 15, 397.64, y - 15);

        doc.text(nome_assinatura, 297.64, y, 'center');
        y += 15;
        doc.text('RG: ' + assinatura_rg, 297.64, y, 'center');
        y += 15;
        doc.text(cargo_assinatura, 297.64, y, 'center');
    }    

    window.open(doc.output('bloburl'), '_blank');        

}

function declaracaoMatricula(url_brasao, nome, rg, cpf, ra, nascimento, sexo, serie, ensino, nome_assinatura, assinatura_rg, cargo_assinatura) {
    var doc = new jsPDF({
        orientation: 'portrait',
        unit: 'pt',
        format: 'a4'
    });

    var img = new Image();

    img.src = url_brasao;
    doc.addImage(img, 'svg', 40, 20, 80, 90);

    x = 130;
    y = 40;

    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.text('GOVERNO DO ESTADO DE SÃO PAULO', x, y);
    y += 15;
    doc.text('SECRETARIA DE ESTADO DA EDUCAÇÃO', x, y)
    y += 15;
    doc.text('UNIDADE REGIONAL DE ENSINO DE GUARATINGUETÁ', x, y)
    y += 15;
    doc.text('EE MAJOR HERMÓGENES', x, y)
    y += 15;
    doc.text('Rua Ipiranga, S/N - Vila Paulista – Cruzeiro', x, y)
    
    y += 100;

    doc.setFontSize(18);
    doc.text('DECLARAÇÃO DE MATRÍCULA', 297.64, y, 'center');

    var texto = "       Declaro para os devidos fins que, **" + nome + ", **";

    if (rg != "-") {
        texto += "RG: " + rg;
    } else if(cpf != '-') {
        texto += "CPF: " + cpf;
    } else {
        texto += "RA: " + ra + ", nascido em " + nascimento;
    }

    if (sexo == "M") {

        if (ensino == "Ensino Fundamental EJA") {
            texto += " é aluno regularmente matriculado na **" + serie + "ª série " + " do " + ensino + ". **" + getTextSerie(parseInt(serie));
        } else {
            texto += " é aluno regularmente matriculado na **" + serie + "ª série do " + ensino + ". **";
        }

    } else {
        if (ensino == "Ensino Fundamental EJA") {
            texto += " é aluna regularmente matriculada na **" + serie + "ª série " + " do " + ensino + ". **" + getTextSerie(parseInt(serie));
        } else {
            texto += " é aluna regularmente matriculada na **" + serie + "ª série do " + ensino + ". **";
        }
    }
    
    y += 130;

    doc.setFontSize(14);
    y = printCharacters(doc, texto, y, 75, 445.28);

    y += 100;

    //doc.setFontSize(12);
    doc.setFont('helvetica', 'normal');
    doc.text(data_extensa(), 520.28, y, 'right');

    if (nome_assinatura != "Sem assinatura") {
        y += 200;
        doc.setFontSize(9);

        doc.setLineWidth(0.7); // Set line thickness
        doc.line(197.64, y - 15, 397.64, y - 15);

        doc.text(nome_assinatura, 297.64, y, 'center');
        y += 15;
        doc.text('RG: ' + assinatura_rg, 297.64, y, 'center');
        y += 15;
        doc.text(cargo_assinatura, 297.64, y, 'center');
    }



    window.open(doc.output('bloburl'), '_blank');    
}

const printCharacters = (doc, text, startY, startX, width) => {
    const startXCached = startX;
    const boldStr = "bold";
    const normalStr = "";
    const fontSize = doc.getFontSize();
    const lineSpacing = doc.getLineHeightFactor() + fontSize + 15;
  
    let textObject = getTextRows(doc, text, width);
  
    textObject.map((row, rowPosition) => {
      Object.entries(row.chars).map(([key, value]) => {
        doc.setFont('Helvetica', value.bold ? boldStr : normalStr);
        doc.text(value.char, startX, startY);
  
        if (value.char == " " && rowPosition < textObject.length - 1) {
          startX += row.blankSpacing;
        } else {
          startX += doc.getStringUnitWidth(value.char) * fontSize;
        }
      });
      startX = startXCached;
      startY += lineSpacing;
    });

    return startY;
  };

const getTextRows = (doc, inputValue, width) => {
    const regex = /(\*{2})+/g; // all "**" words
    const textWithoutBoldMarks = inputValue.replace(regex, "");
    const boldStr = "bold";
    const normalStr = "normal";
    const fontSize = doc.getFontSize();
  
    let splitTextWithoutBoldMarks = doc.splitTextToSize(
      textWithoutBoldMarks,
      width
    );
  
    let charsMapLength = 0;
    let position = 0;
    let isBold = false;
  
    // <><>><><>><>><><><><><>>><><<><><><><>
    // power algorithm to determine which char is bold
    let textRows = splitTextWithoutBoldMarks.map((row, i) => {
      const charsMap = row.split("");
  
      const chars = charsMap.map((char, j) => {
        position = charsMapLength + j + i;
  
        let currentChar = inputValue.charAt(position);
  
        if (currentChar === "*") {
          const spyNextChar = inputValue.charAt(position + 1);
          if (spyNextChar === "*") {
            // double asterix marker exist on these position's so we toggle the bold state
            isBold = !isBold;
            currentChar = inputValue.charAt(position + 2);
  
            // now we remove the markers, so loop jumps to the next real printable char
            let removeMarks = inputValue.split("");
            removeMarks.splice(position, 2);
            inputValue = removeMarks.join("");
          }
        }
  
        return { char: currentChar, bold: isBold };
      });
      charsMapLength += charsMap.length;
  
      // Calculate the size of the white space to justify the text
      let charsWihoutsSpacing = Object.entries(chars).filter(
        ([key, value]) => value.char != " "
      );
      let widthRow = 0;
  
      charsWihoutsSpacing.forEach(([key, value]) => {
        // Keep in mind that the calculations are affected if the letter is in bold or normal
        doc.setFont(undefined, value.bold ? boldStr : normalStr);
        widthRow += doc.getStringUnitWidth(value.char) * fontSize;
      });
  
      let totalBlankSpaces = charsMap.length - charsWihoutsSpacing.length;
      let blankSpacing = (width - widthRow) / totalBlankSpaces;
  
      return { blankSpacing: blankSpacing, chars: { ...chars } };
    });
  
    return textRows;
  };

  function getTextSerie(serie) {

    textoFinal = "(Correspondente ao "

    switch (serie) {
        case 9:
            textoFinal += "6º ano do Ensino Fundamental)."
            break;
        case 10:
            textoFinal += "7º ano do Ensino Fundamental)."
            break;
        case 11:
            textoFinal += "8º ano do Ensino Fundamental)."
            break;         
        case 12:
            textoFinal += "9º ano do Ensino Fundamental)."
            break;                         
    }

    return textoFinal;

  }

  function getNumberSerie(serie) {

    textoFinal = ""

    switch (serie) {
        case 9:
            textoFinal += "6º ano"
            break;
        case 10:
            textoFinal += "7º ano"
            break;
        case 11:
            textoFinal += "8º ano"
            break;         
        case 12:
            textoFinal += "9º ano"
            break;                         
    }

    return textoFinal;

  }

  function data_extensa() {
    const hoje = new Date();
    const month = hoje.toLocaleString('pt-BR', { month: 'long' });

    //console.log(hoje.toLocaleDateString('pt-BR'));

    return 'Canas, ' + String(hoje.getDate()).padStart(2, '0') + ' de ' + month + ' de ' + hoje.getFullYear();

}