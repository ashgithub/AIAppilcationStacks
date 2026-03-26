"""Modular Pydantic models for parallel, structured A2UI generation."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StructuredOutputBase(BaseModel):
    """Base model that preserves flexibility for creative UI design."""

    model_config = ConfigDict(extra="allow")


class SuggestedWidgetTask(StructuredOutputBase):
    """A single widget task selected by the planner/orchestrator."""

    widget_name: str = Field(description="Widget/component name from catalog.")
    slot_label: str = Field(
        default="",
        description="Human-friendly label for this slot (short, UI-safe).",
    )
    priority: int = Field(default=1, ge=1, le=10)


class ParallelWidgetPlan(StructuredOutputBase):
    """Structured output from orchestrator for downstream shell/widget agents."""

    summary: str = Field(default="", description="Brief explanation for user-facing text.")
    widget_tasks: list[SuggestedWidgetTask] = Field(
        default_factory=list, description="Widgets to render in parallel."
    )


class A2UIShellOutput(StructuredOutputBase):
    """Structured output for the shell/skeleton generation agent."""

    surface_id: str = Field(default="dashboard")
    root_id: str = Field(default="root-layout")
    surface_title: str = Field(default="Dashboard", description="Top-level UI title.")
    intro_text: str = Field(
        default="",
        description="Optional helper text that appears before widgets.",
    )
    layout_component: Literal["Column", "Row"] = "Column"
    use_card_sections: bool = Field(
        default=False, description="Wrap each section with native Card component."
    )
    section_alignment: Literal["start", "center", "end", "stretch"] = "stretch"
    section_distribution: Literal[
        "start",
        "center",
        "end",
        "spaceBetween",
        "spaceAround",
        "spaceEvenly",
    ] = "start"
    placeholder_usage_hint: Literal["caption", "body", "h4"] = "caption"
    style_font: str | None = Field(default=None)
    style_primary_color: str | None = Field(default=None)
    section_titles: list[str] = Field(
        default_factory=list,
        description="Optional titles aligned with widget task order.",
    )


class MetricPoint(StructuredOutputBase):
    label: str
    value: float
    details: dict[str, Any] = Field(default_factory=dict)


class BarGraphWidgetOutput(StructuredOutputBase):
    """Widget-level structured output for BarGraph generation."""

    title: str = "Comparison"
    orientation: Literal["vertical", "horizontal"] = "vertical"
    data: list[MetricPoint] = Field(default_factory=list, min_length=1)


class TimelineEvent(StructuredOutputBase):
    date: str
    title: str
    description: str = ""
    category: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class TimelineWidgetOutput(StructuredOutputBase):
    title: str = "Timeline"
    data: list[TimelineEvent] = Field(default_factory=list, min_length=1)


class KpiCardItem(StructuredOutputBase):
    key: str
    label: str
    value: float | int
    unit: str | None = None
    change: float | int | None = None
    changeLabel: str | None = None
    icon: str | None = None
    color: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class KpiWidgetOutput(StructuredOutputBase):
    title: str = "Key Metrics"
    data: list[KpiCardItem] = Field(default_factory=list, min_length=1)


class TableColumn(StructuredOutputBase):
    header: str
    field: str
    type: str = "string"


class TableRow(StructuredOutputBase):
    id: str
    values: dict[str, Any] = Field(default_factory=dict)
    details: dict[str, Any] = Field(default_factory=dict)


class TableWidgetOutput(StructuredOutputBase):
    title: str = "Details"
    columns: list[TableColumn] = Field(default_factory=list, min_length=1)
    rows: list[TableRow] = Field(default_factory=list, min_length=1)


class LineSeries(StructuredOutputBase):
    name: str
    color: str = "#00D4FF"
    values: list[float] = Field(default_factory=list, min_length=1)


class LineGraphWidgetOutput(StructuredOutputBase):
    title: str = "Trend"
    labels: list[str] = Field(default_factory=list, min_length=1)
    series: list[LineSeries] = Field(default_factory=list, min_length=1)
    details: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Optional per-label details aligned by index.",
    )


class MapMarker(StructuredOutputBase):
    name: str
    latitude: float
    longitude: float
    details: dict[str, Any] = Field(default_factory=dict)


class MapWidgetOutput(StructuredOutputBase):
    title: str = "Locations"
    center_lat: float = 0.0
    center_lng: float = 0.0
    zoom: int = 6
    markers: list[MapMarker] = Field(default_factory=list, min_length=1)


class TextWidgetOutput(StructuredOutputBase):
    title: str = "Details"
    body: str = ""
    usage_hint: Literal["h1", "h2", "h3", "h4", "h5", "caption", "body"] = "body"


class CardWidgetOutput(StructuredOutputBase):
    title: str = "Information"
    body: str = ""
    suggestions: list[str] = Field(default_factory=list)


class A2UIDataEntry(StructuredOutputBase):
    """Typed A2UI data entry, keeping structure close to protocol value* fields."""

    key: str
    valueString: str | None = None
    valueNumber: float | None = None
    valueBoolean: bool | None = None
    valueMap: list["A2UIDataEntry"] | None = None


A2UIDataEntry.model_rebuild()


class A2UIMessageEnvelope(StructuredOutputBase):
    """Final message wrapper to help validate assembled payloads."""

    messages: list[dict[str, Any]] = Field(default_factory=list)


class A2UIStreamingStep(StructuredOutputBase):
    """A single streamable step that can be replayed progressively."""

    step: Literal["begin", "shell", "widget", "data"]
    message: dict[str, Any]


class A2UIStreamingPlan(StructuredOutputBase):
    """Structured wrapper for ordered begin/surface/data streaming chunks."""

    steps: list[A2UIStreamingStep] = Field(default_factory=list)
