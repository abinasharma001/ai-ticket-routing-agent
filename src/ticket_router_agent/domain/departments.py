from ticket_router_agent.domain.models import TicketCategory

CATEGORY_TO_DEPARTMENT = {
    TicketCategory.infrastructure: "Infrastructure Operations",
    TicketCategory.application: "Application Support",
    TicketCategory.security: "Security Operations",
    TicketCategory.database: "Database Administration",
    TicketCategory.storage: "Storage Services",
    TicketCategory.network: "Network Operations",
    TicketCategory.access_management: "Identity and Access Management",
}
