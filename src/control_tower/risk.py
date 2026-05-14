from src.control_tower.models import RiskLevel, ActionType


class RiskClassifier:

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def classify(
        self,
        action: str,
        target_system: str = "",
        is_external: bool = False,
        is_destructive: bool = False,
        paths_touched: list[str] | None = None,
    ) -> RiskLevel:
        paths_touched = paths_touched or []

        if self._is_blocked(action, target_system, paths_touched):
            return RiskLevel.CRITICAL

        if self._is_critical(action, is_external, is_destructive, target_system):
            return RiskLevel.CRITICAL

        if self._is_high(action, is_external, is_destructive, target_system):
            return RiskLevel.HIGH

        if self._is_medium(action, is_external, is_destructive):
            return RiskLevel.MEDIUM

        return RiskLevel.LOW

    def _is_blocked(
        self, action: str, target_system: str, paths_touched: list[str]
    ) -> bool:
        if any(p.startswith(".kratos") or p.startswith("C:\\Users\\lucas\\.kratos")
               for p in paths_touched):
            return True
        return False

    def _is_kratos_interference(
        self, action: str, target_system: str, is_destructive: bool
    ) -> bool:
        if target_system != "KRATOS":
            return False
        if is_destructive:
            return True
        kratos_actions = {"write", "modify", "delete", "execute", "configure"}
        action_lower = action.lower()
        return any(word in action_lower for word in kratos_actions)

    def _is_critical(
        self, action: str, is_external: bool, is_destructive: bool,
        target_system: str = "",
    ) -> bool:
        if self._is_kratos_interference(action, target_system, is_destructive):
            return True
        critical_actions = {"delete", "destroy", "drop", "rm", "remove"}
        action_lower = action.lower()
        if any(word in action_lower for word in critical_actions) and is_destructive:
            return True
        if is_external and is_destructive:
            return True
        return False

    def _is_high(
        self, action: str, is_external: bool, is_destructive: bool, target_system: str
    ) -> bool:
        high_actions = {"push", "merge", "deploy", "install", "publish"}
        action_lower = action.lower()
        if any(word in action_lower for word in high_actions):
            return True
        safe_reads = {"health_check", "read_status", "read", "status", "list", "get"}
        if any(word in action_lower for word in safe_reads):
            return False
        if is_external and not is_destructive:
            return True
        return False

    def _is_medium(
        self, action: str, is_external: bool, is_destructive: bool
    ) -> bool:
        medium_actions = {"configure", "update_config", "modify"}
        action_lower = action.lower()
        if any(word in action_lower for word in medium_actions):
            return True
        return False

    def recommended_action_type(self, risk_level: RiskLevel,
                                requires_human: bool = False) -> ActionType:
        if risk_level == RiskLevel.CRITICAL:
            return ActionType.BLOCK
        elif risk_level == RiskLevel.HIGH:
            return ActionType.EXECUTE_WITH_APPROVAL
        elif risk_level == RiskLevel.MEDIUM:
            return ActionType.DRY_RUN
        else:
            return ActionType.OBSERVE
