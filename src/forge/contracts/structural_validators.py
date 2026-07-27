"""Declarative, data-only text-structure validator contracts."""

from typing import Annotated

from pydantic import Field, StringConstraints, model_validator

from forge.contracts.base import ForgeModel, SemanticVersion, SymbolicId, VersionedModel

StructuralLiteral = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=512),
]


class StructuralTextRule(ForgeModel):
    artifact_role: SymbolicId
    allowed_media_types: Annotated[
        tuple[StructuralLiteral, ...],
        Field(min_length=1, max_length=16),
    ] = ("text/markdown", "text/plain")
    required_headings: Annotated[
        tuple[StructuralLiteral, ...],
        Field(max_length=128),
    ] = ()
    required_field_prefixes: Annotated[
        tuple[StructuralLiteral, ...],
        Field(max_length=128),
    ] = ()

    @model_validator(mode="after")
    def validate_rule(self) -> "StructuralTextRule":
        if not (self.required_headings or self.required_field_prefixes):
            raise ValueError("structural text rule must declare a heading or field prefix")
        for label, values in (
            ("allowed media types", self.allowed_media_types),
            ("required headings", self.required_headings),
            ("required field prefixes", self.required_field_prefixes),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"structural text rule {label} must be unique")
        return self


class StructuralValidatorDefinition(VersionedModel):
    id: SymbolicId
    version: SemanticVersion
    check_id: SymbolicId
    purpose: StructuralLiteral
    artifact_rules: Annotated[
        tuple[StructuralTextRule, ...],
        Field(min_length=1, max_length=32),
    ]
    limitations: Annotated[
        tuple[StructuralLiteral, ...],
        Field(min_length=1, max_length=32),
    ]

    @model_validator(mode="after")
    def validate_unique_artifact_roles(self) -> "StructuralValidatorDefinition":
        roles = [rule.artifact_role for rule in self.artifact_rules]
        if len(roles) != len(set(roles)):
            raise ValueError("structural validator artifact roles must be unique")
        if len(self.limitations) != len(set(self.limitations)):
            raise ValueError("structural validator limitations must be unique")
        return self
