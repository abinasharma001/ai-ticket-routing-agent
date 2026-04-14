from ticket_router_agent.bootstrap import build_services
from ticket_router_agent.core.config import get_settings


def main() -> None:
    settings = get_settings()
    orchestrator = build_services(settings)
    print(f"Seeded {len(orchestrator.repository.list_tickets())} tickets and built the FAISS index.")


if __name__ == "__main__":
    main()
