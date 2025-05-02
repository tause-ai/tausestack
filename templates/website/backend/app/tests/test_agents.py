import pytest
import asyncio
from app.repositories.agent_repository import AgentRepository
from app.services.agent_service import AgentService

@pytest.mark.asyncio
async def test_get_all_agents():
    repo = AgentRepository()
    agents = await repo.get_all()
    assert len(agents) >= 2
    assert agents[0].name == "Claude"

@pytest.mark.asyncio
async def test_get_agent_by_id_found():
    repo = AgentRepository()
    agent = await repo.get_by_id(1)
    assert agent is not None
    assert agent.name == "Claude"

@pytest.mark.asyncio
async def test_get_agent_by_id_not_found():
    repo = AgentRepository()
    agent = await repo.get_by_id(999)
    assert agent is None

@pytest.mark.asyncio
async def test_service_list_agents():
    repo = AgentRepository()
    service = AgentService(repo)
    agents = await service.list_agents()
    assert len(agents) >= 2

@pytest.mark.asyncio
async def test_service_get_agent_found():
    repo = AgentRepository()
    service = AgentService(repo)
    agent = await service.get_agent(1)
    assert agent is not None
    assert agent.name == "Claude"

@pytest.mark.asyncio
async def test_service_get_agent_not_found():
    repo = AgentRepository()
    service = AgentService(repo)
    agent = await service.get_agent(999)
    assert agent is None
