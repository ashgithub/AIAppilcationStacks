"""Pydantic schema for validating layout-builder shell output."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, RootModel, TypeAdapter, model_validator


class BeginRenderingStyles(BaseModel):
    """Optional styling info for beginRendering."""

    model_config = ConfigDict(extra="allow")

    font: str | None = None
    primaryColor: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")


class BeginRenderingPayload(BaseModel):
    """A2UI beginRendering action."""

    model_config = ConfigDict(extra="allow")

    surfaceId: str
    root: str
    styles: BeginRenderingStyles | None = None


class SingleComponentWrapper(RootModel[dict[str, dict[str, Any]]]):
    """Wraps a component payload and enforces exactly one component type key."""

    @model_validator(mode="after")
    def validate_single_key(self) -> "SingleComponentWrapper":
        if len(self.root) != 1:
            raise ValueError("component must contain exactly one component type key")

        component_type, component_props = next(iter(self.root.items()))
        if not isinstance(component_type, str) or not component_type.strip():
            raise ValueError("component type key must be a non-empty string")
        if not isinstance(component_props, dict):
            raise ValueError("component payload must be an object")
        return self

    @property
    def component_type(self) -> str:
        return next(iter(self.root.keys()))

    @property
    def component_props(self) -> dict[str, Any]:
        return next(iter(self.root.values()))


class SurfaceComponent(BaseModel):
    """Single component entry in a surfaceUpdate message."""

    id: str
    weight: float | None = None
    component: SingleComponentWrapper


def _extract_component_references(component_type: str, props: dict[str, Any]) -> set[str]:
    refs: set[str] = set()

    if component_type in {"Row", "Column", "List"}:
        children = props.get("children")
        if isinstance(children, dict):
            explicit = children.get("explicitList")
            if isinstance(explicit, list):
                refs.update(str(child_id) for child_id in explicit if isinstance(child_id, str))
            template = children.get("template")
            if isinstance(template, dict):
                template_id = template.get("componentId")
                if isinstance(template_id, str) and template_id:
                    refs.add(template_id)

    child = props.get("child")
    if isinstance(child, str) and child:
        refs.add(child)

    if component_type == "Modal":
        entry = props.get("entryPointChild")
        content = props.get("contentChild")
        if isinstance(entry, str) and entry:
            refs.add(entry)
        if isinstance(content, str) and content:
            refs.add(content)

    if component_type == "Tabs":
        tab_items = props.get("tabItems")
        if isinstance(tab_items, list):
            for item in tab_items:
                if not isinstance(item, dict):
                    continue
                tab_child = item.get("child")
                if isinstance(tab_child, str) and tab_child:
                    refs.add(tab_child)

    return refs


class SurfaceUpdatePayload(BaseModel):
    """A2UI surfaceUpdate action for shell rendering."""

    surfaceId: str
    components: list[SurfaceComponent] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_component_graph(self) -> "SurfaceUpdatePayload":
        component_ids = [component.id for component in self.components]
        if len(component_ids) != len(set(component_ids)):
            raise ValueError("surfaceUpdate.components contains duplicate component ids")

        defined_ids = set(component_ids)
        referenced_ids: set[str] = set()
        for component in self.components:
            referenced_ids.update(
                _extract_component_references(
                    component.component.component_type,
                    component.component.component_props,
                )
            )

        unknown_ids = sorted(referenced_ids - defined_ids)
        if unknown_ids:
            raise ValueError(
                "surfaceUpdate references undefined component ids: "
                + ", ".join(unknown_ids)
            )
        return self


class ShellMessage(BaseModel):
    """Single shell message. Must contain exactly one shell action."""

    beginRendering: BeginRenderingPayload | None = None
    surfaceUpdate: SurfaceUpdatePayload | None = None

    # @model_validator(mode="after")
    # def validate_single_action(self) -> "ShellMessage":
    #     actions = [self.beginRendering, self.surfaceUpdate]
    #     if sum(action is not None for action in actions) != 1:
    #         raise ValueError("shell message must contain exactly one of beginRendering or surfaceUpdate")
    #     return self


def validate_shell_messages(
    shell_messages: list[dict[str, Any]],
    surface_id: str,
    root_component_id: str,
) -> list[dict[str, Any]]:
    """
    Validate and normalize shell messages to plain dicts.

    This keeps shell output flexible (any native/custom component payloads),
    while enforcing structure required to safely start rendering.
    """

    validated = TypeAdapter(list[ShellMessage]).validate_python(shell_messages)

    begin_messages = [message.beginRendering for message in validated if message.beginRendering is not None]
    surface_updates = [message.surfaceUpdate for message in validated if message.surfaceUpdate is not None]

    if not begin_messages:
        raise ValueError("shell_messages must include at least one beginRendering message")
    if not surface_updates:
        raise ValueError("shell_messages must include at least one surfaceUpdate message")

    for begin in begin_messages:
        if begin.surfaceId != surface_id:
            raise ValueError(
                f"beginRendering.surfaceId '{begin.surfaceId}' does not match surface_id '{surface_id}'"
            )
        if begin.root != root_component_id:
            raise ValueError(
                f"beginRendering.root '{begin.root}' does not match root_component_id '{root_component_id}'"
            )

    all_component_ids = {
        component.id
        for update in surface_updates
        for component in update.components
    }
    if root_component_id not in all_component_ids:
        raise ValueError(
            f"root_component_id '{root_component_id}' must be present in surfaceUpdate.components"
        )

    for update in surface_updates:
        if update.surfaceId != surface_id:
            raise ValueError(
                f"surfaceUpdate.surfaceId '{update.surfaceId}' does not match surface_id '{surface_id}'"
            )

    return [message.model_dump(mode="python") for message in validated]
