"""Supported-command actor and transition authorization."""

from uuid import NAMESPACE_URL, UUID, uuid5

from forge import __version__
from forge.contracts.actors import Actor, ActorType, OwnerIdentity
from forge.contracts.workflows import StepDefinition, TransitionDefinition
from forge.errors import AuthorizationError


def owner_actor(owner: OwnerIdentity) -> Actor:
    """Represent the configured owner at the supported CLI boundary."""
    return Actor(
        id=owner.id,
        actor_type=ActorType.OWNER,
        display_label=owner.display_name,
        tool_reference=f"forge {__version__}",
    )


def forge_cli_actor() -> Actor:
    """Return the stable service actor used for deterministic CLI-only transitions."""
    return Actor(
        id=uuid5(NAMESPACE_URL, "https://forge.local/actors/forge-cli"),
        actor_type=ActorType.FORGE_CLI,
        display_label="FORGE CLI",
        tool_reference=f"forge {__version__}",
    )


def require_owner(actor: Actor, owner_identity_id: UUID, action: str) -> None:
    if actor.actor_type is not ActorType.OWNER or actor.id != owner_identity_id:
        raise AuthorizationError(
            f"Only configured owner {owner_identity_id} may {action}; "
            f"actor {actor.id} has type {actor.actor_type.value}"
        )


def authorize_transition(
    actor: Actor,
    owner_identity_id: UUID,
    step: StepDefinition,
    transition: TransitionDefinition,
) -> None:
    requirement = transition.authority_requirement
    if requirement == "forge-cli":
        if actor.actor_type is not ActorType.FORGE_CLI:
            raise AuthorizationError(
                f"Transition {transition.id} requires the FORGE CLI service actor"
            )
        return
    if actor.actor_type not in step.allowed_actors:
        raise AuthorizationError(
            f"Actor type {actor.actor_type.value} is not allowed for step {step.id}"
        )
    if requirement == "owner":
        require_owner(actor, owner_identity_id, f"apply transition {transition.id}")
    elif requirement == "participant":
        return
    else:
        raise AuthorizationError(
            f"Transition {transition.id} has unsupported authority requirement {requirement!r}"
        )
