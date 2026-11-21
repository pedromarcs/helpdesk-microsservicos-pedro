"""Cria os chamados de exemplo quando o banco está vazio (só para aula).

Os ids de usuários e equipamentos vêm dos dados de exemplo dos outros serviços:
  usuários: ana=2, bruno=3, carla=4  |  equipamentos: PAT-0001=1, PAT-0002=2
Aqui NÃO chamamos os outros serviços: eles podem ainda estar subindo.
"""
from datetime import datetime

from sqlalchemy.orm import Session

from app.chamados import repositorio, servico
from app.chamados.modelos import Chamado
from app.notificacoes import servico as notificacoes

ANA, BRUNO, CARLA = 2, 3, 4
PC, IMPRESSORA = 1, 2


def _abrir(db: Session, titulo: str, descricao: str, prioridade: str, solicitante_id: int, ativo_id: int | None = None) -> Chamado:
    agora = datetime.now()
    chamado = repositorio.salvar(db, Chamado(
        titulo=titulo, descricao=descricao, prioridade=prioridade, status="aberto",
        solicitante_id=solicitante_id, ativo_id=ativo_id, criado_em=agora,
        prazo_sla=servico.calcular_prazo(prioridade, agora),
    ))
    notificacoes.notificar(
        db, "ChamadoAberto", solicitante_id,
        f"Seu chamado #{chamado.id} foi aberto. Prazo: {chamado.prazo_sla:%d/%m %H:%M}.",
    )
    return chamado


def carregar(db: Session) -> None:
    if repositorio.listar(db):
        return
    c1 = _abrir(db, "Computador não liga", "Apertei o botão e nada acontece.", "alta", ANA, PC)
    _abrir(db, "Impressora atolando papel", "Atola a cada 3 folhas.", "media", BRUNO, IMPRESSORA)
    _abrir(db, "Acesso ao sistema de RH", "Preciso de acesso para a nova estagiária.", "baixa", BRUNO)

    c1.tecnico_id = CARLA
    c1.status = "em_atendimento"
    repositorio.salvar(db, c1)
    notificacoes.notificar(db, "ChamadoAtribuido", CARLA, f"O chamado #{c1.id} foi atribuído a você.")