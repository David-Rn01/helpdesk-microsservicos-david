# Segurança

Este projeto é didático, mas segue práticas de segurança reais. Esta página
explica o que já está protegido e o que fica como responsabilidade de quem
for colocar o sistema em produção.

## O que está protegido

| Risco | Proteção |
|---|---|
| Acesso sem login | Todas as rotas, exceto `/auth/login`, `/saude` e a tela, exigem token JWT (`Authorization: Bearer ...`). |
| Senhas vazadas do banco | Senhas guardadas só como hash **scrypt** com sal aleatório. A senha nunca é salva nem devolvida pela API. |
| Adivinhar senhas | Bloqueio temporário após 5 tentativas erradas (por e-mail e endereço). Mensagem igual para e-mail inexistente e senha errada. |
| Token falsificado | Token assinado (HS256) com segredo do servidor, com validade, emissor e algoritmo fixos (tokens `alg: none` são recusados). |
| Ver ou mexer no que não é seu | Permissões por perfil: o solicitante só vê os próprios chamados e notificações; só técnicos e administradores atribuem e resolvem; só administradores criam usuários. |
| Agir em nome de outra pessoa | O solicitante e o autor do comentário vêm do token, não do corpo da requisição. Campos extras são recusados. |
| Descobrir o que existe | Chamado de outra pessoa responde "não encontrado" (404), sem revelar que existe. A lista de usuários não mostra e-mails. |
| XSS na tela | Todo texto vindo da API é escapado antes de entrar no HTML; não há scripts embutidos na página; política CSP só permite scripts do próprio servidor. |
| Clickjacking e outros | Cabeçalhos `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`. |
| Dados enormes | Limites de tamanho em todos os campos e corpo da requisição limitado a 64 KB. |
| SQL injection | Acesso ao banco só pelo SQLAlchemy, com parâmetros (sem SQL montado com texto). |
| Erros que vazam detalhes | Erros de banco respondem com mensagem genérica. |
| Dependências vulneráveis | Versões fixas, `pip-audit` no GitHub Actions a cada envio e Dependabot semanal. |
| Contêiner | Roda como usuário sem privilégios, sistema de arquivos somente leitura, sem capacidades extras, porta exposta só em `127.0.0.1`. |
| Segredos no código | Segredos só por variável de ambiente (`.env`, fora do Git). |

## O que mudou com os microsserviços

| Ponto | Como ficou |
|---|---|
| Quem cria o token | Só o serviço de **Usuários** (login). Ele guarda as senhas e o limite de tentativas. |
| Quem confere o token | **Todos** os serviços conferem assinatura, validade e emissor do token sozinhos, antes de responder. Inventário, Chamados e Notificações leem o id e o perfil do próprio token, sem acessar o banco de Usuários. |
| Repasse do token | Quando Chamados consulta Usuários ou Inventário, repassa o token do usuário (`Authorization`). Os outros serviços aplicam as próprias permissões. |
| Segredo | `JWT_SEGREDO` vem do `.env`. Se não houver, o contêiner `segredo` gera um aleatório na primeira vez e guarda no volume `segredos`, lido só pelos serviços. Nunca fica no código. Sem segredo, o serviço não sobe. |
| Exposição | Só o **gateway** publica porta (`127.0.0.1:8000`). Serviços, bancos e a fila (Redis) ficam só na rede interna do Docker. |
| Endereço real no login | O gateway sobrescreve o `X-Forwarded-For` com o endereço de quem chamou (um valor falso enviado pelo cliente é descartado), e o serviço de Usuários usa esse endereço no limite de tentativas. |
| Falhas | Chamadas entre serviços têm tempo limite; um serviço fora do ar vira 503 com mensagem clara, sem travar. |
| Limitação conhecida | Um usuário desativado continua com acesso nos outros serviços até o token vencer (`TOKEN_MINUTOS`), porque eles não consultam o banco de Usuários. |

## Antes de usar em produção

- Defina `JWT_SEGREDO` com pelo menos 32 caracteres aleatórios.
- Rode com `DADOS_EXEMPLO=0` (os usuários de exemplo têm senha conhecida) e `DOCS=0`.
- Coloque o sistema atrás de HTTPS (por exemplo, um proxy reverso com certificado).
- Troque o SQLite por um banco gerenciado (PostgreSQL) com backup.
- O limite de tentativas de login fica em memória no serviço de Usuários: com várias instâncias dele, use um armazenamento compartilhado (Redis).
- Proteja o Redis com senha e TLS se ele sair da rede interna.

## Como relatar um problema

Encontrou uma falha? Não abra uma issue pública: envie os detalhes diretamente ao professor.
