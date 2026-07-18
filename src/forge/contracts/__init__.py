"""Versioned public data contracts for FORGE Production v1."""

from collections.abc import Mapping

from pydantic import BaseModel

from forge.contracts.actors import Actor, ActorType, AuthorityGrant, OwnerIdentity
from forge.contracts.agents import (
    AgentContextDecision,
    AgentContextInput,
    AgentContextReturnContract,
    AgentContextStep,
    AgentHandoff,
    AgentResult,
    CanonicalAgentContext,
    ReturnedFile,
)
from forge.contracts.archives import (
    AbandonmentRecord,
    ArchivedFile,
    ArchivedObjectReference,
    ArchiveManifest,
    ClosureRecord,
)
from forge.contracts.artifacts import ArtifactRecord, ArtifactRevision, ProvenanceRecord
from forge.contracts.base import SCHEMA_VERSION
from forge.contracts.capabilities import (
    CapabilityDefinition,
    CapabilityTrustState,
    SideEffectClass,
)
from forge.contracts.configuration import ProjectConfiguration
from forge.contracts.decisions import (
    ApprovalRevocation,
    DecisionRecord,
    DecisionStatus,
    DecisionSupersession,
    EmergencyOverride,
    RiskAcceptance,
    ScopeAmendment,
    WorkflowDeviation,
)
from forge.contracts.events import AuditEvent
from forge.contracts.idempotency import (
    CommandRecoveryRecord,
    IdempotencyEventMetadata,
    IdempotencyEventReference,
    IdempotencyReceipt,
)
from forge.contracts.initiatives import Initiative, InitiativeReference
from forge.contracts.locking import LockRemediationRecord
from forge.contracts.migrations import MigrationRecord
from forge.contracts.packs import PackManifest, PackTrustDecision, PackTrustState
from forge.contracts.recovery import (
    JournalDamageCondition,
    JournalRecoveryRecord,
    JournalRecoverySnapshotCondition,
    RecoveryRecord,
    SnapshotCondition,
)
from forge.contracts.runs import RunRecord
from forge.contracts.state import (
    ExplanationProfile,
    InitiativeLifecycleState,
    IntegrityState,
    MaterializedState,
    RepositoryState,
    RunState,
    StepState,
)
from forge.contracts.verification import (
    AcceptanceRecord,
    CheckOutcome,
    CheckResult,
    Claim,
    EvidencePacket,
)
from forge.contracts.workflows import (
    CancellationBehavior,
    Gate,
    StepDefinition,
    TransitionDefinition,
    WorkflowDefinition,
)

CONTRACT_MODELS: Mapping[str, type[BaseModel]] = {
    "acceptance-record": AcceptanceRecord,
    "abandonment-record": AbandonmentRecord,
    "actor": Actor,
    "agent-handoff": AgentHandoff,
    "canonical-agent-context": CanonicalAgentContext,
    "agent-result": AgentResult,
    "approval-revocation": ApprovalRevocation,
    "artifact-record": ArtifactRecord,
    "artifact-revision": ArtifactRevision,
    "archive-manifest": ArchiveManifest,
    "archived-file": ArchivedFile,
    "archived-object-reference": ArchivedObjectReference,
    "audit-event": AuditEvent,
    "authority-grant": AuthorityGrant,
    "capability-definition": CapabilityDefinition,
    "check-result": CheckResult,
    "claim": Claim,
    "command-recovery-record": CommandRecoveryRecord,
    "closure-record": ClosureRecord,
    "decision-record": DecisionRecord,
    "decision-supersession": DecisionSupersession,
    "emergency-override": EmergencyOverride,
    "evidence-packet": EvidencePacket,
    "gate": Gate,
    "initiative": Initiative,
    "initiative-reference": InitiativeReference,
    "idempotency-receipt": IdempotencyReceipt,
    "materialized-state": MaterializedState,
    "migration-record": MigrationRecord,
    "journal-recovery-record": JournalRecoveryRecord,
    "lock-remediation-record": LockRemediationRecord,
    "owner-identity": OwnerIdentity,
    "pack-manifest": PackManifest,
    "pack-trust-decision": PackTrustDecision,
    "project-configuration": ProjectConfiguration,
    "recovery-record": RecoveryRecord,
    "provenance-record": ProvenanceRecord,
    "returned-file": ReturnedFile,
    "risk-acceptance": RiskAcceptance,
    "run-record": RunRecord,
    "scope-amendment": ScopeAmendment,
    "step-definition": StepDefinition,
    "transition-definition": TransitionDefinition,
    "workflow-definition": WorkflowDefinition,
    "workflow-deviation": WorkflowDeviation,
}

__all__ = [
    "CONTRACT_MODELS",
    "SCHEMA_VERSION",
    "AbandonmentRecord",
    "AcceptanceRecord",
    "Actor",
    "ActorType",
    "AgentContextDecision",
    "AgentContextInput",
    "AgentContextReturnContract",
    "AgentContextStep",
    "AgentHandoff",
    "AgentResult",
    "ApprovalRevocation",
    "ArchiveManifest",
    "ArchivedFile",
    "ArchivedObjectReference",
    "ArtifactRecord",
    "ArtifactRevision",
    "AuditEvent",
    "AuthorityGrant",
    "CancellationBehavior",
    "CanonicalAgentContext",
    "CapabilityDefinition",
    "CapabilityTrustState",
    "CheckOutcome",
    "CheckResult",
    "Claim",
    "ClosureRecord",
    "CommandRecoveryRecord",
    "DecisionRecord",
    "DecisionStatus",
    "DecisionSupersession",
    "EmergencyOverride",
    "EvidencePacket",
    "ExplanationProfile",
    "Gate",
    "IdempotencyEventMetadata",
    "IdempotencyEventReference",
    "IdempotencyReceipt",
    "Initiative",
    "InitiativeLifecycleState",
    "InitiativeReference",
    "IntegrityState",
    "JournalDamageCondition",
    "JournalRecoveryRecord",
    "JournalRecoverySnapshotCondition",
    "LockRemediationRecord",
    "MaterializedState",
    "MigrationRecord",
    "OwnerIdentity",
    "PackManifest",
    "PackTrustDecision",
    "PackTrustState",
    "ProjectConfiguration",
    "ProvenanceRecord",
    "RecoveryRecord",
    "RepositoryState",
    "ReturnedFile",
    "RiskAcceptance",
    "RunRecord",
    "RunState",
    "ScopeAmendment",
    "SideEffectClass",
    "SnapshotCondition",
    "StepDefinition",
    "StepState",
    "TransitionDefinition",
    "WorkflowDefinition",
    "WorkflowDeviation",
]
