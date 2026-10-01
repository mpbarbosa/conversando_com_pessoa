# Procedência do corpus

## Origem

**<http://arquivopessoa.net/>** — Arquivo Pessoa, arquivo digital da obra de
Fernando Pessoa.

Indicado pelo proprietário do repositório em 2026-10-01.

**Data de entrada no repositório: 2025-10-24.** Os 2083 ficheiros entraram todos
num único commit, `396cca7` («Major project restructure and documentation»,
2025-10-24 23:54:09 -0300, Marcelo Pereira Barbosa), a par de `ROADMAP.md`,
`src/main.py`, `src/model.py` e `src/retriever.py`.

A recolha em si é anterior a essa data e **não há script de recolha no histórico**
— nenhum commit, em nenhum ramo, contém um crawler, descarregador ou importador.
Os ficheiros foram produzidos fora do repositório, por meio não registado. Para
reproduzir o corpus seria preciso reescrever a recolha.

## O que não está verificado

Tentei acedar ao sítio em 2026-10-01 para confirmar os termos de uso e não
consegui — sem resposta na porta 443 e `http=000` por `curl`. Pode ser
restrição de rede deste ambiente ou indisponibilidade do sítio. **Os termos de
uso do Arquivo Pessoa não foram verificados** e devem ser confirmados antes de
qualquer distribuição do corpus.

## Situação de direitos

Fernando Pessoa morreu em **1935**. Em Portugal e no Brasil o prazo é de 70 anos
após a morte do autor, logo **a obra está em domínio público desde 2006**.

Há porém uma distinção que importa e que não está resolvida: a **obra** estar em
domínio público não implica que uma **transcrição ou edição crítica** específica
o esteja. O trabalho de digitalização, fixação de texto e anotação pode ter
protecção própria em algumas jurisdições. Os ficheiros aqui vêm de uma edição
digital concreta, não de manuscritos.

Para uso local e de investigação não há questão. **Para distribuir o corpus ou
publicar um serviço que o sirva, confirmar os termos do Arquivo Pessoa primeiro.**

## Estado dos ficheiros

Medido em 2026-10-01 (ver `docs/CONTROLO.md`):

| | |
|---|---|
| ficheiros | 2083 `.txt` |
| formato | linha 1 = autor · linha `Titulo:` · corpo |
| cobertura do cabeçalho | **2083/2083**, sem excepções |
| palavras no corpo | 216 285 após limpeza (243 320 em bruto) |
| idioma | 1926 pt · 153 en · 4 indeterminados |
| vozes | ortónimo 1298 · Campos 324 · Reis 252 · Caeiro 120 · Search 52 · Soares 6 · outros 31 |

### Defeitos conhecidos nos dados

| Defeito | Ficheiros |
|---|---|
| Mojibake: o «Á» de «Álvaro» substituído por bytes espúrios | `poem_224.txt` |
| Duplicados exactos | 3 pares |
| Variantes do mesmo poema | 18 grupos |
| Tradução parcial de um poema já presente | `poem_1794` (*Ode Marítima* em inglês) |
| Poemas em que o título **é** o único verso | `poem_2873`, `poem_2886`, `poem_4347` |
| Fragmentos com menos de 12 palavras | 11 |

Todos são tratados em `src/corpus/` e cobertos por testes. Nenhum ficheiro foi
alterado — a limpeza é feita na ingestão.
