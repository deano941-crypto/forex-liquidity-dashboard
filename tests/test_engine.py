from data.demo import make_demo_data
from agents.engine import run_desk

def test_six_agent_engine():
    result=run_desk(make_demo_data("XAU_USD","M1",300))
    assert len(result["agents"]) == 6
    assert result["decision"] in {"BUY","SELL","WAIT"}
