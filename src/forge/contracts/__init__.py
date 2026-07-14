"""Versioned public data contracts for FORGE Production v1."""

from collections.abc import Mapping

from pydantic import BaseModel

from forge.contracts.actors import Actor, ActorType, AuthorityGrant, OwnerIdentity
from forge.contracts.agents import AgentHandoff, AgentResult, ReturnedFile
from forge.contracts.archives import (
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
from forge.contracts.initiatives import Initiative, InitiativeReference
from forge.contracts.packs import PackManifest, PackTrustDecision, PackTrustState
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
    "actor": Actor,
    "agent-handoff": AgentHandoff,
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
    "closure-record": ClosureRecord,
    "decision-record": DecisionRecord,
    "decision-supersession": DecisionSupersession,
    "emergency-override": EmergencyOverride,
    "evidence-packet": EvidencePacket,
    "gate": Gate,
    "initiative": Initiative,
    "initiative-reference": InitiativeReference,
    "materialized-state": MaterializedState,
    "owner-identity": OwnerIdentity,
    "pack-manifest": PackManifest,
    "pack-trust-decision": PackTrustDecision,
    "project-configuration": ProjectConfiguration,
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
    "AcceptanceRecord",
    "Actor",
    "ActorType",
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
    "CapabilityDefinition",
    "CapabilityTrustState",
    "CheckOutcome",
    "CheckResult",
    "Claim",
    "ClosureRecord",
    "DecisionRecord",
    "DecisionStatus",
    "DecisionSupersession",
    "EmergencyOverride",
    "EvidencePacket",
    "ExplanationProfile",
    "Gate",
    "Initiative",
    "InitiativeLifecycleState",
    "InitiativeReference",
    "IntegrityState",
    "MaterializedState",
    "OwnerIdentity",
    "PackManifest",
    "PackTrustDecision",
    "PackTrustState",
    "ProjectConfiguration",
    "ProvenanceRecord",
    "RepositoryState",
    "ReturnedFile",
    "RiskAcceptance",
    "RunRecord",
    "RunState",
    "ScopeAmendment",
    "SideEffectClass",
    "StepDefinition",
    "StepState",
    "TransitionDefinition",
    "WorkflowDefinition",
    "WorkflowDeviation",
]
