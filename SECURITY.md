# Segurança

Este projeto é didático, mas segue práticas de segurança reais. Esta página explica o que já está
protegido na versão em **microsserviços** e o que fica como responsabilidade de quem for colocar o
sistema em produção.

## O que está protegido

| Risco | Proteção |
|---|---|
| Acesso sem login | Todas as rotas, exceto `/auth/login`, `/saude` e a tela, exigem token JWT (`Authorization: Bearer ...`). **Cada serviço confere o token por conta própria**, mesmo que a requisição venha do gateway. |
| Falar direto com um serviço | Só o **gateway** publica porta (`127.0.0.1:8000`). Usuários, Inventário, Chamados e os bancos ficam apenas na rede interna do Docker. |
| Senhas vazadas do banco | Senhas guardadas só como hash **scrypt** com sal aleatório, **somente no serviço de Usuários**. A senha nunca é salva nem devolvida pela API. |
| Adivinhar senhas | Bloqueio temporário após 5 tentativas erradas (por e-mail e endereço). Mensagem igual para e-mail inexistente e senha errada. |
| Token falsificado | Token assinado (HS256) com segredo do servidor, com validade, emissor e algoritmo fixos (tokens `alg: none` são recusados). Perfil ausente ou inventado também é recusado. |
| Segredo diferente entre serviços | O `JWT_SEGREDO` é **obrigatório** (mínimo de 32 caracteres): se faltar, o serviço se recusa a subir, em vez de sortear um segredo e quebrar o login entre serviços. |
| Ver ou mexer no que não é seu | Permissões por perfil, conferidas no serviço dono da regra: o solicitante só vê os próprios chamados e notificações; só técnicos e administradores atribuem e resolvem; só administradores criam usuários. |
| Agir em nome de outra pessoa | O solicitante e o autor do comentário vêm do token, não do corpo da requisição. Campos extras são recusados. |
| Token nas chamadas entre serviços | Ao chamar Usuários ou Inventário, o serviço de Chamados **repassa o token de quem fez a requisição**: o outro serviço autoriza como autorizaria uma chamada da tela. O gateway também só repassa o cabeçalho, sem conferir nem inventar credencial. |
| Descobrir o que existe | Chamado de outra pessoa responde "não encontrado" (404), sem revelar que existe. A lista de usuários não mostra e-mails. `GET /usuarios/{id}` devolve só id, nome e perfil. O `/docs` dos serviços não é exposto pelo gateway. |
| XSS na tela | Todo texto vindo da API é escapado antes de entrar no HTML; não há scripts embutidos na página; a política CSP só permite scripts do próprio servidor. |
| Clickjacking e outros | Cabeçalhos `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy` e CSP, em todos os serviços e no gateway. |
| Dados enormes | Limites de tamanho em todos os campos e corpo da requisição limitado a 64 KB em cada serviço e no gateway. |
| Serviço lento ou fora do ar | Toda chamada entre serviços tem tempo limite (3 s). Falha vira erro claro (503) sem gravar nada pela metade; o gateway devolve 503 ou 504. Um serviço parado não derruba os outros. |
| SQL injection | Acesso ao banco só pelo SQLAlchemy, com parâmetros (sem SQL montado com texto). |
| Erros que vazam detalhes | Erros de banco respondem com mensagem genérica. |
| Dependências vulneráveis | Versões fixas, `pip-audit` no GitHub Actions a cada envio (um job por serviço) e Dependabot semanal em cada pasta. |
| Contêiner | Cada serviço roda como usuário sem privilégios, com sistema de arquivos somente leitura, sem capacidades extras e sem novos privilégios. |
| Segredos no código | Segredos só por variável de ambiente (`.env`, fora do Git). O `.env.example` traz um segredo **só para aula**. |

## Limitações conhecidas (o que mudou em relação ao monólito)

- **Perfil desatualizado.** O perfil vem dentro do token. Se um administrador mudar o perfil de alguém, o token antigo
  continua valendo até expirar (60 minutos). No monólito, o banco era consultado a cada requisição.
- **Sem revogação.** Não existe lista de tokens cancelados; "Sair" só apaga o token no navegador.
- **Segredo compartilhado (HS256).** Todos os serviços conhecem o mesmo `JWT_SEGREDO`, então qualquer um deles
  *poderia* assinar tokens. Em produção, o ideal é uma chave assimétrica (RS256 ou EdDSA): só o serviço de Usuários
  guarda a chave privada, e os demais conferem com a chave pública.
- **Sem integridade entre serviços.** Não há chave estrangeira entre bancos: se um equipamento for apagado depois,
  o chamado fica com um `ativo_id` que não existe mais.
- **Tráfego interno sem criptografia.** A comunicação entre os serviços é HTTP puro dentro da rede do Docker.
- **Endereço do cliente no bloqueio de login.** O serviço de Usuários só enxerga o endereço do gateway, então, na
  prática, o bloqueio vale por e-mail.

## Antes de usar em produção

- Defina um `JWT_SEGREDO` **novo**, com pelo menos 32 caracteres aleatórios, igual em todos os serviços. Nunca use o do `.env.example`.
- Rode com `DADOS_EXEMPLO=0` (os usuários de exemplo têm senha conhecida) e `DOCS=0`.
- Coloque o gateway atrás de **HTTPS** (por exemplo, um proxy reverso com certificado) e use uma rede privada entre os serviços.
- Troque o SQLite por um banco gerenciado (PostgreSQL), **um por serviço**, com backup.
- O limite de tentativas de login fica em memória: com várias instâncias, use um armazenamento compartilhado (Redis) e
  repasse o endereço real do cliente (`X-Forwarded-For`) do gateway ao serviço de Usuários.
- Considere tokens de vida mais curta e uma forma de revogá-los.

## Como relatar um problema

Encontrou uma falha? Não abra uma issue pública: envie os detalhes diretamente ao professor.