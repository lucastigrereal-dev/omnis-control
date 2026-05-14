from src.decision_log.models import (
    LogEventType,
    DecisionCreatedEvent,
    WorkOrderParsedEvent,
    ContractValidatedEvent,
    RiskBlockedEvent,
    DryRunCompletedEvent,
    ApprovalRequiredEvent,
    ExecutionCompletedEvent,
    ExecutionFailedEvent,
    BaseEvent,
    LogEvent,
)
from src.decision_log.errors import LogError


_EVENT_CLASS_MAP: dict[LogEventType, type[BaseEvent]] = {
    LogEventType.DECISION_CREATED: DecisionCreatedEvent,
    LogEventType.WORK_ORDER_PARSED: WorkOrderParsedEvent,
    LogEventType.CONTRACT_VALIDATED: ContractValidatedEvent,
    LogEventType.RISK_BLOCKED: RiskBlockedEvent,
    LogEventType.DRY_RUN_COMPLETED: DryRunCompletedEvent,
    LogEventType.APPROVAL_REQUIRED: ApprovalRequiredEvent,
    LogEventType.EXECUTION_COMPLETED: ExecutionCompletedEvent,
    LogEventType.EXECUTION_FAILED: ExecutionFailedEvent,
}


class EventFactory:

    @staticmethod
    def create(
        event_type: LogEventType,
        summary: str = "",
        project: str = "",
        correlation_id: str = "",
        evidence: dict | None = None,
        next_action: str = "",
        **kwargs,
    ) -> BaseEvent:
        cls = _EVENT_CLASS_MAP.get(event_type)
        if cls is None:
            raise LogError(f"Unknown event type: {event_type}")

        event = LogEvent(
            event_type=event_type,
            source="omnis",
            project=project,
            correlation_id=correlation_id,
            summary=summary,
            evidence=evidence or {},
            next_action=next_action,
        )

        instance = cls(event=event)
        for attr, value in kwargs.items():
            if hasattr(instance, attr):
                setattr(instance, attr, value)

        return instance

    @staticmethod
    def from_raw(data: dict) -> BaseEvent:
        event_type = LogEventType(data.get("event_type", "DecisionCreated"))
        cls = _EVENT_CLASS_MAP.get(event_type)
        if cls is None:
            raise LogError(f"Unknown event type: {event_type}")

        event = LogEvent.from_dict(data)
        extra = {
            k: v
            for k, v in data.items()
            if k not in event.to_dict() and hasattr(cls(event=event), k)
        }
        return cls(event=event, **extra)

    @staticmethod
    def decision_created(
        decision_id: str = "",
        summary: str = "",
        project: str = "",
        correlation_id: str = "",
        evidence: dict | None = None,
        next_action: str = "",
    ) -> DecisionCreatedEvent:
        return EventFactory.create(
            event_type=LogEventType.DECISION_CREATED,
            decision_id=decision_id,
            summary=summary,
            project=project,
            correlation_id=correlation_id,
            evidence=evidence,
            next_action=next_action,
        )

    @staticmethod
    def work_order_parsed(
        order_id: str = "",
        summary: str = "",
        project: str = "",
        correlation_id: str = "",
    ) -> WorkOrderParsedEvent:
        return EventFactory.create(
            event_type=LogEventType.WORK_ORDER_PARSED,
            order_id=order_id,
            summary=summary,
            project=project,
            correlation_id=correlation_id,
        )

    @staticmethod
    def contract_validated(
        contract_id: str = "",
        summary: str = "",
        project: str = "",
        correlation_id: str = "",
    ) -> ContractValidatedEvent:
        return EventFactory.create(
            event_type=LogEventType.CONTRACT_VALIDATED,
            contract_id=contract_id,
            summary=summary,
            project=project,
            correlation_id=correlation_id,
        )

    @staticmethod
    def risk_blocked(
        risk_level: str = "",
        reason: str = "",
        summary: str = "",
        project: str = "",
        correlation_id: str = "",
    ) -> RiskBlockedEvent:
        return EventFactory.create(
            event_type=LogEventType.RISK_BLOCKED,
            risk_level=risk_level,
            reason=reason,
            summary=summary,
            project=project,
            correlation_id=correlation_id,
        )

    @staticmethod
    def dry_run_completed(
        request_id: str = "",
        summary: str = "",
        project: str = "",
        correlation_id: str = "",
        evidence: dict | None = None,
    ) -> DryRunCompletedEvent:
        return EventFactory.create(
            event_type=LogEventType.DRY_RUN_COMPLETED,
            request_id=request_id,
            summary=summary,
            project=project,
            correlation_id=correlation_id,
            evidence=evidence,
        )

    @staticmethod
    def approval_required(
        item_id: str = "",
        risk_level: str = "",
        summary: str = "",
        project: str = "",
        correlation_id: str = "",
    ) -> ApprovalRequiredEvent:
        return EventFactory.create(
            event_type=LogEventType.APPROVAL_REQUIRED,
            item_id=item_id,
            risk_level=risk_level,
            summary=summary,
            project=project,
            correlation_id=correlation_id,
        )

    @staticmethod
    def execution_completed(
        item_id: str = "",
        tests_run: int = 0,
        tests_passed: int = 0,
        summary: str = "",
        project: str = "",
        correlation_id: str = "",
    ) -> ExecutionCompletedEvent:
        return EventFactory.create(
            event_type=LogEventType.EXECUTION_COMPLETED,
            item_id=item_id,
            tests_run=tests_run,
            tests_passed=tests_passed,
            summary=summary,
            project=project,
            correlation_id=correlation_id,
        )

    @staticmethod
    def execution_failed(
        item_id: str = "",
        error: str = "",
        summary: str = "",
        project: str = "",
        correlation_id: str = "",
    ) -> ExecutionFailedEvent:
        return EventFactory.create(
            event_type=LogEventType.EXECUTION_FAILED,
            item_id=item_id,
            error=error,
            summary=summary,
            project=project,
            correlation_id=correlation_id,
        )
