from ticket_router_agent.domain.models import EvaluationSummary, FeedbackPayload


class EvaluationResponse(EvaluationSummary):
    pass


class FeedbackRequest(FeedbackPayload):
    pass
