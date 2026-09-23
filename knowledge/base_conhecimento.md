# BASE DE CONHECIMENTO — ASSISTENTE DE TI

> Cada atendimento é descrito como um bloco `### ENTRADA` autocontido, com
> campos fixos (Categoria, Palavras-chave, Autoatendimento, Chamado, URL,
> Informações obrigatórias). O parser da aplicação (`document_service.py`)
> lê cada `### ENTRADA` como uma unidade única — ela NUNCA é dividida em
> pedaços menores, então a URL e os dados do chamado nunca se perdem no
> meio do processo de chunking.
>
> Para adicionar um novo atendimento, copie o modelo no final deste arquivo
> e preencha os campos. Veja instruções completas no README.md.

---

## CATEGORIA: Senhas e Acessos

### ENTRADA: Reset de senha
Palavras-chave: esqueci minha senha, senha bloqueada, resetar senha, não consigo entrar, senha de rede, senha de e-mail, trocar senha, senha expirada

Autoatendimento:
1. Acesse o portal de autoatendimento: https://senha.paschoalotto.com.br
2. Clique em "Esqueci minha senha".
3. Informe seu usuário de rede (o mesmo do e-mail corporativo, sem o "@paschoalotto.com.br").
4. Você receberá um código de verificação por SMS no celular cadastrado.
5. Digite o código e defina a nova senha (mínimo 8 caracteres, com letra maiúscula, número e caractere especial).
6. A nova senha já vale para e-mail, rede e sistemas internos.

Quando abrir chamado: se você não tem mais acesso ao celular cadastrado, se o portal retornar erro, ou se a conta estiver bloqueada por tentativas excessivas.

Chamado: Reset/Desbloqueio de Senha
Categoria: TI > Acessos > Desbloqueio/Reset de Senha
URL: https://chamados.paschoalotto.com.br/abrir/ti-acessos-reset-senha
Informações obrigatórias: nome completo, usuário de rede, motivo (sem celular cadastrado / conta bloqueada / erro no portal)
Prioridade: Normal

---

### ENTRADA: Conta bloqueada por tentativas de login
Palavras-chave: conta bloqueada, muitas tentativas, usuário bloqueado, não consigo mais tentar logar

Autoatendimento: aguardar 15 minutos costuma desbloquear automaticamente. Se continuar bloqueado após esse tempo, é necessário abrir chamado.

Quando abrir chamado: quando o bloqueio persistir após 15 minutos de espera.

Chamado: Reset/Desbloqueio de Senha
Categoria: TI > Acessos > Desbloqueio/Reset de Senha
URL: https://chamados.paschoalotto.com.br/abrir/ti-acessos-reset-senha
Informações obrigatórias: nome completo, usuário de rede, horário aproximado do bloqueio
Prioridade: Alta

---

### ENTRADA: Acesso sem MFA / código de verificação não chega
Palavras-chave: MFA, autenticação em duas etapas, código não chega, não recebo o código, autenticador

Autoatendimento:
1. Verifique se o celular está com sinal e conseguindo receber SMS.
2. Confira se o número cadastrado no portal está correto em https://senha.paschoalotto.com.br.
3. Se usar aplicativo autenticador (Microsoft Authenticator), verifique se o horário do celular está sincronizado automaticamente.

Quando abrir chamado: se nenhum dos passos acima resolver, ou se você trocou de celular e perdeu o acesso ao aplicativo autenticador.

Chamado: Reconfiguração de MFA
Categoria: TI > Acessos > Reconfiguração de MFA
URL: https://chamados.paschoalotto.com.br/abrir/ti-acessos-sistema
Informações obrigatórias: nome completo, usuário de rede, se trocou de aparelho recentemente
Prioridade: Alta

---

### ENTRADA: Solicitação de acesso a sistema
Palavras-chave: solicitar acesso, preciso de acesso, não tenho permissão, acesso a sistema, liberar sistema

Autoatendimento: não há autoatendimento — toda concessão de acesso passa por aprovação do gestor e exige chamado.

Chamado: Solicitação de Acesso a Sistema
Categoria: TI > Acessos > Solicitação de Acesso
URL: https://chamados.paschoalotto.com.br/abrir/ti-acessos-sistema
Informações obrigatórias: nome do sistema, nível de acesso necessário, justificativa, nome do gestor aprovador
Prioridade: Normal

---

### ENTRADA: Acesso expirado ou revogado
Palavras-chave: acesso expirado, acesso removido, perdi o acesso, acesso negado, não consigo mais entrar no sistema

Autoatendimento: não se aplica — se o acesso foi removido (por exemplo, após mudança de área), a reativação exige nova aprovação.

Chamado: Solicitação de Acesso a Sistema
Categoria: TI > Acessos > Solicitação de Acesso
URL: https://chamados.paschoalotto.com.br/abrir/ti-acessos-sistema
Informações obrigatórias: nome do sistema, quando o acesso parou de funcionar, nome do gestor aprovador
Prioridade: Normal

---

## CATEGORIA: Equipamentos

### ENTRADA: Computador não liga
Palavras-chave: computador não liga, pc não liga, não inicia, tela preta ao ligar, não dá sinal

Autoatendimento:
1. Verifique se o cabo de energia está bem conectado na tomada e no computador/notebook.
2. Teste outra tomada, se possível.
3. Se for notebook, verifique se a luz do carregador acende.
4. Segure o botão de ligar por 10 segundos, solte e tente ligar novamente.

Quando abrir chamado: se o equipamento continuar sem ligar após os passos acima.

Chamado: Suporte Técnico de Hardware
Categoria: TI > Hardware > Suporte Técnico
URL: https://chamados.paschoalotto.com.br/abrir/ti-hardware-computador
Informações obrigatórias: patrimônio do equipamento, o que já foi testado
Prioridade: Urgente (impede totalmente o trabalho)

---

### ENTRADA: Computador lento
Palavras-chave: computador lento, travando, demorado, lento pra abrir programas

Autoatendimento:
1. Reinicie o computador (muitas vezes resolve lentidão acumulada).
2. Feche programas e abas do navegador que não está usando.
3. Verifique o espaço livre em disco — menos de 10% livre deixa o sistema lento.

Quando abrir chamado: se a lentidão persistir mesmo após reiniciar e fechar programas.

Chamado: Suporte Técnico de Hardware
Categoria: TI > Hardware > Suporte Técnico
URL: https://chamados.paschoalotto.com.br/abrir/ti-hardware-computador
Informações obrigatórias: patrimônio do equipamento, há quanto tempo está lento, se piorou após alguma atualização
Prioridade: Normal

---

### ENTRADA: Tela azul (BSOD)
Palavras-chave: tela azul, blue screen, erro de sistema, reiniciou sozinho com tela azul

Autoatendimento: anote o código do erro exibido na tela azul (se aparecer) e reinicie o computador. Se acontecer apenas uma vez, pode ser um evento isolado.

Quando abrir chamado: sempre que a tela azul se repetir mais de uma vez.

Chamado: Suporte Técnico de Hardware
Categoria: TI > Hardware > Suporte Técnico
URL: https://chamados.paschoalotto.com.br/abrir/ti-hardware-computador
Informações obrigatórias: patrimônio, código do erro (se anotado), com que frequência acontece
Prioridade: Alta

---

### ENTRADA: Monitor sem imagem
Palavras-chave: monitor não liga, monitor sem imagem, tela preta, monitor não mostra nada

Autoatendimento:
1. Verifique se o cabo de vídeo (HDMI/DisplayPort) está bem conectado nas duas pontas.
2. Verifique se o monitor está ligado na tomada e o botão de força foi pressionado.
3. Teste trocar a entrada de vídeo no próprio monitor (botão de "input/source").

Quando abrir chamado: se a imagem continuar não aparecendo após esses testes.

Chamado: Suporte Técnico de Hardware
Categoria: TI > Hardware > Suporte Técnico
URL: https://chamados.paschoalotto.com.br/abrir/ti-hardware-monitor
Informações obrigatórias: patrimônio do monitor, modelo (se souber), o que já foi testado
Prioridade: Alta

---

### ENTRADA: Monitor com tela quebrada ou danificada
Palavras-chave: monitor quebrado, tela rachada, tela com manchas, monitor danificado

Autoatendimento: não se aplica — dano físico exige substituição do equipamento.

Chamado: Suporte Técnico de Hardware
Categoria: TI > Hardware > Suporte Técnico
URL: https://chamados.paschoalotto.com.br/abrir/ti-hardware-monitor
Informações obrigatórias: patrimônio do monitor, como o dano ocorreu
Prioridade: Alta

---

### ENTRADA: Teclado ou mouse não funciona
Palavras-chave: teclado não funciona, mouse não funciona, teclado travado, mouse não responde, periférico com defeito

Autoatendimento:
1. Desconecte e reconecte o cabo USB (ou reinicie o receptor sem fio).
2. Teste o periférico em outra porta USB.
3. Se for sem fio, verifique/troque a pilha ou bateria.

Quando abrir chamado: se o periférico continuar sem funcionar após esses testes.

Chamado: Suporte Técnico de Periféricos
Categoria: TI > Hardware > Periféricos
URL: https://chamados.paschoalotto.com.br/abrir/ti-hardware-perifericos
Informações obrigatórias: patrimônio (se houver), qual periférico, o que já foi testado
Prioridade: Normal

---

### ENTRADA: Headset não funciona
Palavras-chave: headset não funciona, fone não funciona, sem áudio no headset, microfone do headset não funciona

Autoatendimento:
1. Verifique se o headset está selecionado como dispositivo de áudio padrão no Windows (ícone de som na barra de tarefas).
2. Desconecte e reconecte o cabo USB ou P2.
3. Teste o headset em outro computador, se possível, para confirmar se o defeito é do equipamento.

Quando abrir chamado: se o headset não funcionar em nenhum cenário testado.

Chamado: Suporte Técnico de Periféricos
Categoria: TI > Hardware > Periféricos
URL: https://chamados.paschoalotto.com.br/abrir/ti-hardware-perifericos
Informações obrigatórias: patrimônio (se houver), modelo do headset, o que já foi testado
Prioridade: Normal

---

### ENTRADA: Webcam não funciona
Palavras-chave: webcam não funciona, câmera não aparece, câmera não liga, sem imagem na chamada

Autoatendimento:
1. Verifique se algum outro aplicativo está usando a câmera (feche outros programas de vídeo).
2. Confira nas configurações de privacidade do Windows se o acesso à câmera está permitido.
3. Reinicie o computador.

Quando abrir chamado: se a câmera continuar não sendo reconhecida.

Chamado: Suporte Técnico de Periféricos
Categoria: TI > Hardware > Periféricos
URL: https://chamados.paschoalotto.com.br/abrir/ti-hardware-perifericos
Informações obrigatórias: patrimônio, modelo do notebook ou webcam, o que já foi testado
Prioridade: Normal

---

## CATEGORIA: Software

### ENTRADA: Instalação de programa
Palavras-chave: instalar programa, preciso de um software, instalar aplicativo, novo programa

Autoatendimento: não se aplica — instalação exige permissão administrativa que o colaborador não possui na máquina.

Quando abrir chamado: sempre que precisar de um programa novo.

Chamado: Instalação de Programa
Categoria: TI > Software > Instalação
URL: https://chamados.paschoalotto.com.br/abrir/ti-software-instalacao
Informações obrigatórias: nome do programa, versão (se souber), justificativa de uso, se é pago ou gratuito
Prioridade: Normal (1 dia útil se já homologado, até 3 dias úteis se for análise nova)

---

### ENTRADA: Atualizar programa
Palavras-chave: atualizar programa, nova versão, programa desatualizado, update

Autoatendimento: alguns programas se atualizam sozinhos (verifique o menu "Ajuda > Verificar atualizações" do próprio programa). Se a atualização exigir permissão de administrador, não é possível fazer sozinho.

Quando abrir chamado: se a atualização pedir permissão de administrador ou não aparecer opção de atualizar.

Chamado: Instalação de Programa
Categoria: TI > Software > Instalação
URL: https://chamados.paschoalotto.com.br/abrir/ti-software-instalacao
Informações obrigatórias: nome do programa, versão atual, versão desejada (se souber)
Prioridade: Normal

---

### ENTRADA: Remover programa
Palavras-chave: remover programa, desinstalar, tirar programa do computador

Autoatendimento: não se aplica na maioria dos casos — desinstalação de software corporativo exige permissão administrativa.

Chamado: Instalação de Programa
Categoria: TI > Software > Instalação
URL: https://chamados.paschoalotto.com.br/abrir/ti-software-instalacao
Informações obrigatórias: nome do programa a ser removido, motivo
Prioridade: Baixa

---

### ENTRADA: Programa não abre ou apresenta erro
Palavras-chave: programa não abre, erro no programa, programa travando, aplicativo com erro, mensagem de erro

Autoatendimento:
1. Feche o programa completamente (verifique o Gerenciador de Tarefas) e abra novamente.
2. Reinicie o computador.
3. Anote a mensagem de erro exata, se aparecer (isso ajuda muito na solução).

Quando abrir chamado: se o erro persistir após reiniciar.

Chamado: Suporte a Software
Categoria: TI > Software > Erro em Aplicação
URL: https://chamados.paschoalotto.com.br/abrir/ti-software-erro
Informações obrigatórias: nome do programa, mensagem de erro exata (se houver), quando começou a acontecer
Prioridade: Normal (Alta se o programa for essencial para o trabalho)

---

### ENTRADA: Navegador com problema
Palavras-chave: navegador travando, chrome não abre, site não carrega, navegador lento, erro no navegador

Autoatendimento:
1. Feche e abra o navegador novamente.
2. Limpe o cache do navegador (Configurações > Privacidade > Limpar dados de navegação).
3. Teste em outro navegador, se disponível, para confirmar se o problema é específico de um navegador ou do site.

Quando abrir chamado: se o problema persistir em qualquer navegador testado.

Chamado: Suporte a Software
Categoria: TI > Software > Erro em Aplicação
URL: https://chamados.paschoalotto.com.br/abrir/ti-software-erro
Informações obrigatórias: qual navegador, qual site ou sistema, mensagem de erro (se houver)
Prioridade: Normal

---

## CATEGORIA: Rede e Internet

### ENTRADA: Sem internet
Palavras-chave: sem internet, não conecta, sem conexão, internet caiu

Autoatendimento:
1. Verifique se o cabo de rede está bem conectado (se usar cabo).
2. Reinicie o computador.
3. Verifique se outros colegas próximos também estão sem internet (se sim, pode ser problema geral, não individual).

Quando abrir chamado: se apenas o seu equipamento estiver sem internet, mesmo após reiniciar.

Chamado: Suporte de Rede
Categoria: TI > Rede > Conectividade
URL: https://chamados.paschoalotto.com.br/abrir/ti-rede-internet
Informações obrigatórias: patrimônio, se é cabo ou Wi-Fi, se outros colegas também estão afetados
Prioridade: Urgente (impede totalmente o trabalho)

---

### ENTRADA: Internet lenta
Palavras-chave: internet lenta, conexão lenta, demora para carregar, lentidão de rede

Autoatendimento:
1. Reinicie o computador.
2. Feche downloads ou vídeos rodando em segundo plano.
3. Se estiver no Wi-Fi, teste aproximar-se do roteador/access point.

Quando abrir chamado: se a lentidão persistir e afetar o trabalho.

Chamado: Suporte de Rede
Categoria: TI > Rede > Conectividade
URL: https://chamados.paschoalotto.com.br/abrir/ti-rede-internet
Informações obrigatórias: patrimônio, se é cabo ou Wi-Fi, horário em que a lentidão ocorre
Prioridade: Normal

---

### ENTRADA: Wi-Fi não conecta ou instável
Palavras-chave: wifi não conecta, wi-fi caindo, rede sem fio instável, não encontra a rede

Autoatendimento:
1. Verifique se o Wi-Fi está ativado no computador.
2. Esqueça a rede e conecte novamente, digitando a senha correta.
3. Reinicie o computador.

Quando abrir chamado: se o Wi-Fi continuar instável ou não conectar após esses passos.

Chamado: Suporte de Rede
Categoria: TI > Rede > Wi-Fi
URL: https://chamados.paschoalotto.com.br/abrir/ti-rede-wifi
Informações obrigatórias: patrimônio, local onde está (andar/sala), se o problema é constante ou intermitente
Prioridade: Normal

---

### ENTRADA: VPN não conecta
Palavras-chave: vpn não conecta, não consigo acessar de casa, vpn com erro, sem acesso remoto

Autoatendimento:
1. Verifique se sua internet doméstica está funcionando normalmente.
2. Feche e abra o aplicativo de VPN novamente.
3. Confirme se está usando o usuário e senha de rede atualizados.

Quando abrir chamado: se a VPN continuar sem conectar após esses passos.

Chamado: Suporte de Rede
Categoria: TI > Rede > VPN
URL: https://chamados.paschoalotto.com.br/abrir/ti-rede-internet
Informações obrigatórias: mensagem de erro exibida, se já conectou alguma vez com sucesso, de onde está tentando acessar
Prioridade: Alta

---

## CATEGORIA: Microsoft 365

### ENTRADA: Outlook não abre
Palavras-chave: outlook não abre, outlook travando, e-mail não abre

Autoatendimento:
1. Feche o Outlook pelo Gerenciador de Tarefas e abra novamente.
2. Reinicie o computador.
3. Verifique se há atualizações pendentes do Office.

Quando abrir chamado: se o Outlook continuar não abrindo após esses passos.

Chamado: Suporte Microsoft 365
Categoria: TI > Microsoft 365 > Outlook
URL: https://chamados.paschoalotto.com.br/abrir/ti-microsoft-outlook
Informações obrigatórias: mensagem de erro (se houver), quando começou o problema
Prioridade: Alta

---

### ENTRADA: Outlook não envia e-mail
Palavras-chave: outlook não envia, e-mail não sai, e-mail travado na caixa de saída

Autoatendimento:
1. Verifique sua conexão com a internet.
2. Confira se o e-mail tem anexos muito grandes (acima de 25MB costuma travar o envio).
3. Feche e abra o Outlook novamente.

Quando abrir chamado: se o problema persistir com e-mails sem anexos grandes e internet funcionando.

Chamado: Suporte Microsoft 365
Categoria: TI > Microsoft 365 > Outlook
URL: https://chamados.paschoalotto.com.br/abrir/ti-microsoft-outlook
Informações obrigatórias: tamanho aproximado do e-mail/anexo, mensagem de erro (se houver)
Prioridade: Normal

---

### ENTRADA: Teams não abre
Palavras-chave: teams não abre, teams travando, não consigo abrir o teams

Autoatendimento:
1. Feche o Teams pelo Gerenciador de Tarefas (verifique se não há processo travado em segundo plano) e abra novamente.
2. Reinicie o computador.
3. Reinstale o Teams pelo Portal da Empresa, se a opção estiver disponível.

Quando abrir chamado: se o Teams continuar não abrindo.

Chamado: Suporte Microsoft 365
Categoria: TI > Microsoft 365 > Teams
URL: https://chamados.paschoalotto.com.br/abrir/ti-microsoft-teams
Informações obrigatórias: mensagem de erro (se houver), se afeta reuniões em andamento
Prioridade: Alta

---

### ENTRADA: Teams sem áudio ou vídeo
Palavras-chave: teams sem áudio, teams sem som, não escuto na reunião, câmera não funciona no teams

Autoatendimento:
1. Verifique se o dispositivo de áudio/vídeo correto está selecionado nas configurações do Teams (ícone de engrenagem > Dispositivos).
2. Teste o microfone/câmera em outro aplicativo para confirmar se o problema é do Teams ou do equipamento.
3. Saia e entre novamente na reunião.

Quando abrir chamado: se o problema persistir após esses testes.

Chamado: Suporte Microsoft 365
Categoria: TI > Microsoft 365 > Teams
URL: https://chamados.paschoalotto.com.br/abrir/ti-microsoft-teams
Informações obrigatórias: se é áudio, vídeo ou os dois, equipamento usado (headset, webcam)
Prioridade: Alta

---

### ENTRADA: OneDrive não sincroniza
Palavras-chave: onedrive não sincroniza, arquivos não atualizam, onedrive travado, nuvem não sincroniza

Autoatendimento:
1. Verifique o ícone do OneDrive na barra de tarefas — passe o mouse sobre ele para ver o status da sincronização.
2. Feche e abra o OneDrive novamente (clique com o botão direito no ícone > Fechar OneDrive, depois abra pelo menu Iniciar).
3. Verifique sua conexão com a internet.

Quando abrir chamado: se a sincronização continuar travada ou com erro após esses passos.

Chamado: Suporte Microsoft 365
Categoria: TI > Microsoft 365 > OneDrive
URL: https://chamados.paschoalotto.com.br/abrir/ti-microsoft-teams
Informações obrigatórias: mensagem de erro exibida (se houver), quais arquivos/pastas estão afetados
Prioridade: Normal

---

## CATEGORIA: Impressão

### ENTRADA: Impressora não imprime
Palavras-chave: impressora não imprime, não sai a impressão, impressora offline, fila de impressão travada

Autoatendimento:
1. Verifique se a impressora está ligada e com papel/toner.
2. Verifique se a impressora aparece como "Pronta" (não "Offline") nas configurações de impressoras do Windows.
3. Cancele os trabalhos travados na fila de impressão e tente imprimir novamente.

Quando abrir chamado: se a impressora continuar não imprimindo após esses passos.

Chamado: Suporte de Impressão
Categoria: TI > Impressão > Suporte Técnico
URL: https://chamados.paschoalotto.com.br/abrir/ti-impressao
Informações obrigatórias: nome/local da impressora, mensagem de erro (se houver)
Prioridade: Normal

---

## CATEGORIA: Outros

### ENTRADA: Dúvida sobre qual chamado abrir
Palavras-chave: não sei qual chamado abrir, dúvida sobre chamado, qual categoria usar

Autoatendimento: descreva o problema com mais detalhes (o que você estava tentando fazer, o que aconteceu, se apareceu alguma mensagem) para identificarmos o chamado correto.

Quando abrir chamado: após identificar a categoria certa com mais detalhes do colaborador.

---

### ENTRADA: Problema não identificado na base
Palavras-chave: problema diferente, não encontrei minha situação, outro problema

Autoatendimento: não se aplica — não há procedimento específico conhecido para esse caso.

Quando abrir chamado: sempre, para que a equipe de TI analise o caso.

Chamado: Chamado Geral de TI
Categoria: TI > Outros > Não Categorizado
URL: https://chamados.paschoalotto.com.br/abrir/ti-outros
Informações obrigatórias: descrição detalhada do problema, prints ou mensagens de erro, quando começou
Prioridade: Normal

---

<!--
MODELO PARA NOVA ENTRADA (copie e preencha):

### ENTRADA: [Nome curto do problema]
Palavras-chave: [termo 1, termo 2, termo 3, ...]

Autoatendimento:
1. [passo 1]
2. [passo 2]

Quando abrir chamado: [condição]

Chamado: [Nome do chamado]
Categoria: [Categoria > Subcategoria]
URL: https://chamados.paschoalotto.com.br/abrir/[slug]
Informações obrigatórias: [lista separada por vírgula]
Prioridade: [Baixa | Normal | Alta | Urgente]
-->
