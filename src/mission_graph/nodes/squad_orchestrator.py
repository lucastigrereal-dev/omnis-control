"""SquadOrchestrator — executa múltiplos agentes em paralelo via asyncio."""
from __future__ import annotations
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

_EXECUTOR = ThreadPoolExecutor(max_workers=4)


async def run_agent_async(agent_class: Any, mission: dict) -> dict:
    """Roda um agente em thread pool (agentes são síncronos)."""
    loop = asyncio.get_event_loop()
    agent = agent_class()
    return await loop.run_in_executor(_EXECUTOR, agent.execute_mission_dict, mission)


async def execute_squad_async(squad_config: dict, mission: dict) -> dict:
    """Orquestra squad: fase paralela → fase sequencial."""
    parallel_classes = squad_config.get("parallel", [])
    sequential_classes = squad_config.get("sequential", [])

    # Fase 1: paralelo
    parallel_results = []
    if parallel_classes:
        parallel_results = list(await asyncio.gather(*[
            run_agent_async(cls, mission) for cls in parallel_classes
        ]))

    # Fase 2: sequencial
    sequential_results = []
    context = {**mission, "parallel_results": parallel_results}
    for cls in sequential_classes:
        result = await run_agent_async(cls, {**mission, "context": context})
        sequential_results.append(result)
        context["last_result"] = result

    all_results = parallel_results + sequential_results
    total_cost = sum(r.get("cost_usd", 0.0) for r in all_results)
    total_tokens = sum(r.get("tokens_used", 0) for r in all_results)

    return {
        "squad_name": squad_config.get("name", "unknown"),
        "parallel_results": parallel_results,
        "sequential_results": sequential_results,
        "total_cost_usd": total_cost,
        "total_tokens": total_tokens,
        "agent_count": len(all_results),
    }


def run_squad(squad_config: dict, mission: dict) -> dict:
    """API síncrona — entrada principal para o grafo."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Se já há event loop (ex: pytest-asyncio), usa thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, execute_squad_async(squad_config, mission))
                return future.result(timeout=60)
        return loop.run_until_complete(execute_squad_async(squad_config, mission))
    except Exception as e:
        return {"error": str(e), "squad_name": squad_config.get("name", "unknown")}
