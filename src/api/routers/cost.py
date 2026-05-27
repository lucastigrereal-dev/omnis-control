"""Router de custo — relatorio via CostTracker."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/summary")
def cost_summary():
    from src.agencia.cost_tracker import CostTracker

    try:
        report = CostTracker.generate_report()
        return report.to_dict() if hasattr(report, "to_dict") else {"report": str(report)}
    except Exception as e:
        return {"error": str(e), "note": "CostTracker unavailable"}
