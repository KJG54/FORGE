"""Strict project-level ``forge.yaml`` configuration contract."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, model_validator

from forge.contracts.actors import OwnerIdentity
from forge.contracts.base import ForgeModel, NonEmptyString, RepositoryRelativePath, VersionedModel
from forge.contracts.state import ExplanationProfile


class BehaviorConfiguration(ForgeModel):
    explanation_profile: ExplanationProfile = ExplanationProfile.STANDARD
    require_clean_git_for_close: bool = False


class ImportConfiguration(ForgeModel):
    max_files: Annotated[int, Field(ge=1, le=100_000)] = 100
    max_file_bytes: Annotated[int, Field(ge=1)] = 10_485_760
    max_total_bytes: Annotated[int, Field(ge=1)] = 104_857_600
    preserve_failed_staging: bool = True

    @model_validator(mode="after")
    def validate_aggregate_limit(self) -> "ImportConfiguration":
        if self.max_total_bytes < self.max_file_bytes:
            raise ValueError("max_total_bytes must be at least max_file_bytes")
        return self


class ArtifactConfiguration(ForgeModel):
    digest_algorithm: Literal["sha256"] = "sha256"
    max_preserved_object_bytes: Annotated[int, Field(ge=1)] = 104_857_600


class PackConfiguration(ForgeModel):
    local_paths: tuple[RepositoryRelativePath, ...] = ()


class AgentConfiguration(ForgeModel):
    preferred_adapter: NonEmptyString | None = None


class SecurityConfiguration(ForgeModel):
    secret_path_patterns: tuple[NonEmptyString, ...] = (
        ".env",
        ".forge/local/secrets/**",
    )


class ProjectConfiguration(VersionedModel):
    project_id: UUID
    owner: OwnerIdentity
    behavior: BehaviorConfiguration = BehaviorConfiguration()
    imports: ImportConfiguration = ImportConfiguration()
    artifacts: ArtifactConfiguration = ArtifactConfiguration()
    packs: PackConfiguration = PackConfiguration()
    agents: AgentConfiguration = AgentConfiguration()
    security: SecurityConfiguration = SecurityConfiguration()

    @model_validator(mode="after")
    def reject_local_owner_metadata(self) -> "ProjectConfiguration":
        if self.owner.local_metadata:
            raise ValueError("owner local_metadata does not belong in tracked forge.yaml")
        return self
