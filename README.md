# Laya Decision Lab

PoC local para acompanhar **Untitled slide.pdf**, apresentação de George Michelon sobre Laya (outubro2026). Implementa a triagem do slide8 com inferência real, sem respostas pré-fixadas. Interface em inglês para combinar com os slides; exemplos em inglês e português.

## Executar no Mac

Abra `start.command` no Terminal ou execute:

```bash
git clone https://github.com/geomichelon/laya-decision-lab.git
cd laya-decision-lab
bash start.command
```

Acesse **http://127.0.0.1:8765**. Mantenha o Terminal aberto; Ctrl+C encerra. Se a porta já estiver ocupada pela PoC, use a instância existente. O launcher prepara um ambiente isolado em `~/Library/Application Support/LayaDecisionLab/venv` no Mac (disco interno), ou `.venv` no Linux, na primeira execução. Python3.11 recomendado; dependências exatas em `requirements.lock.txt`. A PoC é independente do Archmazing.

O modelo executa no Mac com PyTorch/MPS (Metal) quando disponível, ou CPU. Para escolher CPU explicitamente: `LAYA_LAB_DEVICE=cpu bash start.command`. Na primeira utilização, os pesos públicos são baixados do Hugging Face, sem chave. O cache fica em `.cache/huggingface`; checkpoints e ambiente Python não entram no Git. Dois checkpoints são usados: `typed-decisions` para inglês e `multilingual` para português. Apenas um fica residente; trocar idioma requer carregá-lo novamente.

Antes da apresentação, execute os oito exemplos para baixar ambos os checkpoints. Depois de preparados, é possível iniciar com `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 bash start.command`. O primeiro carregamento/inferência pode ser mais lento. Não apagar o cache antes da demonstração.

## Roteiro de demonstração (3–5 minutos)

1. Após o slide7, abra a PoC e clique em **Present** para tela cheia. O slide8 serve como introdução visual.
2. Em **Live demo**, escolha **Duplicate charge** e **Analyze ticket**. Mostre departamento (`choice`), distribuição de urgência (`score`) e probabilidade de intenção de cancelamento (`noul`). Os números são resultados reais e podem diferir dos valores ilustrativos do PDF.
3. Explique a caixa **Policy outcome**: é uma regra determinística aplicada aos resultados, não outra resposta gerada. Nenhum reembolso ou cancelamento é executado.
4. Use **The negation test**, depois um ticket livre. O modelo pode errar mesmo com confiança alta. Não selecione apenas exemplos favoráveis.
5. Abra **Decision schema** para mostrar as perguntas e critérios enviados. O rótulo de urgência é o nível mais provável; o valor decimal é a média ordinal esperada.
6. Em **Evaluate samples**, execute os oito casos. Mostre acertos/erros por ticket, concordância do departamento com os rótulos esperados, comparação com regras e tempos medidos. Exporte JSON para auditoria.
7. Retorne à apresentação: isso demonstra integração e comportamento, mas a adoção depende de dados representativos, calibração e avaliação independente.

## Análise do PDF

A sequência dos nove slides conecta origem, arquitetura, uso, alternativas e piloto. O slide8 já oferece um escopo adequado à PoC; o slide9 apenas verifica importação do pacote. A demonstração agora cobre carregamento, inferência e interface, que são passos adicionais.

A principal melhoria na narrativa é separar **predição**, **confiança** e **política**. Uma saída estruturada pode estar semanticamente errada. A documentação oficial descreve sensibilidade a rótulos/negação e necessidade de avaliação/calibração no domínio. Portanto, a demo não usa a confiança como uma taxa de acerto comprovada.

O slide7 propõe uma comparação completa com Jev, LLM e regras. Esta etapa implementa **Laya versus regras para departamento**. Não há integração Jev/LLM, medição de custo financeiro ou comparação de velocidade com APIs externas. Oito tickets sintéticos visíveis não constituem um conjunto de teste independente. Não usar os resultados como benchmark de mercado ou prova de superioridade.

Ao atualizar os slides: substitua no slide8 “No live inference” por uma referência à demo real, mantenha os números identificados como exemplo ou use um resultado exportado com hardware/versão/data. Acrescente fontes ao slide2 e aos limites técnicos. Repositório: [geomichelon/laya-decision-lab](https://github.com/geomichelon/laya-decision-lab). O acesso depende das permissões do repositório. O PDF original foi preservado.

## Implementação e limites

- Backend FastAPI; frontend HTML/CSS/JavaScript sem CDNs. Servidor local em127.0.0.1.
- Laya0.4.15, pesos `convaiinnovations/laya`, revisão fixa `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`.
- Perguntas em `questions.json`. Expectativas em `samples.json` ficam na avaliação e não são enviadas ao modelo.
- A regra sugere revisão se alguma confiança < limiar, probabilidade de cancelamento ≥0,5 ou urgência esperada ≥1,5. Limiar padrão80% é ilustrativo, sem calibração neste domínio. A regra nunca executa ações.
- Tempo de inferência inclui a chamada local do SDK e sincronização da GPU. Exclui download/carregamento e HTTP; tempo total do servidor é separado. p95 da amostra usa nearest rank e inclui primeiras inferências após carregar cada modelo, sem promessa de desempenho em produção.
- Baseline: palavras-chave ordenadas para Billing, Technical, Sales, Other. Compara somente o departamento. Não entende negação ou contexto.
- Input limitado a2000 caracteres e450 tokens do checkpoint para reduzir risco de truncamento. Erros não são substituídos por respostas simuladas. Inferências serializadas; requisições simultâneas recebem409.
- Texto livre não é salvo em disco nem enviado a uma API de inferência. Exports só são gravados quando o usuário baixa o JSON. Os artefatos em `evidence/` contêm apenas tickets sintéticos.

## Testes

```bash
"$HOME/Library/Application Support/LayaDecisionLab/venv/bin/python" -m unittest discover -s tests -v
```

Três testes de limites da política, uma única confiança baixa, entrada inválida e origem/host aprovados. Navegador Chromium validou análise real, exportação JSON, limpeza de resultado ao editar, schema, oito exemplos, português e largura390px sem overflow.

Execução real em25/10/2026: **7/8 departamentos corretos (87,5%)**, regras8/8, cancelamento6/8 (75%), erro absoluto médio da urgência0,569 numa escala0–2. Na primeira execução, p50=119,55ms e p95=498,34ms; no reteste offline final, p50=114,14ms e p95=142,69ms nas oito inferências, excluindo carregamentos; todos os casos foram encaminhados para revisão pelo limiar ilustrativo80%. O primeiro pedido da sessão levou2715ms; aquecimento e carga do Mac influenciam os tempos. Em português, o pedido de preços foi classificado incorretamente como Billing. O caso inglês de indisponibilidade gerou falso positivo de cancelamento. Esses resultados não demonstram vantagem do Laya sobre regras neste conjunto.

Evidências de inferência e navegador ficam em `evidence/`, incluindo todas as respostas, schema/revisão, latências e capturas. Nenhuma resposta simulada. Não extrapolar esses resultados para produção.

Para repetir a verificação de navegador, com o servidor aberto:

```bash
npm install
npx playwright install chromium
npm run test:browser
```

O teste faz inferência real local e sobrescreve somente as evidências de tickets sintéticos em `evidence/`. O reteste completo também passou com `HF_HUB_OFFLINE=1` e `TRANSFORMERS_OFFLINE=1`, depois de baixar os dois checkpoints. Um ensaio inicial expôs uma janela em que o botão aparecia habilitado antes da leitura de status; corrigida a inicialização da UI para aguardar o status do modelo.

## Docker (alternativa de distribuição)

Artefato preparado; não validado nesta entrega, que usa MPS nativo no Mac. Docker Desktop usa CPU, sem acesso direto ao MPS do host.

```bash
docker build -t laya-decision-lab .
docker run --rm -p 127.0.0.1:8765:8765 -v laya-models:/models laya-decision-lab
```

## Fontes

- [Código e limites oficiais do Laya](https://github.com/NandhaKishorM/laya)
- [Tipos de perguntas e respostas](https://github.com/NandhaKishorM/laya/blob/main/docs/questions-and-answers.md)
- [Distribuição Python](https://pypi.org/project/laya/)
- [Pesos públicos](https://huggingface.co/convaiinnovations/laya)
