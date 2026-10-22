from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Literal

from a2ui.core.basic_catalog import BasicCatalog
from a2ui.core.catalog import Catalog

CADENZA_CATALOG_ID = (
    "https://okestro.dev/a2ui/catalogs/cadenza-composer-v0.9.json"
)
COMMON_TYPES = "https://a2ui.org/specification/v0_9/common_types.json#/$defs/"

ComponentKind = Literal[
    "accordion",
    "chart",
    "code",
    "container",
    "copy",
    "data",
    "empty",
    "feedback",
    "message",
    "navigation",
    "number",
    "overlay",
    "pagination",
    "select",
    "segmented",
    "step",
    "tag",
    "toggle",
    "tree",
    "uploader",
]


@dataclass(frozen=True)
class CadenzaComponentSpec:
    name: str
    data_comp: str
    kind: ComponentKind
    description: str


CADENZA_CUSTOM_COMPONENT_SPECS = (
    CadenzaComponentSpec("Accordion", "accordion", "accordion", "접고 펼칠 수 있는 콘텐츠 묶음"),
    CadenzaComponentSpec("AddTable", "add-table", "data", "행 추가 기능을 표현하는 데이터 표"),
    CadenzaComponentSpec("Alert", "alert", "message", "상태 또는 주의 메시지"),
    CadenzaComponentSpec("Drawer", "base-drawer", "overlay", "트리거로 여는 서랍형 패널"),
    CadenzaComponentSpec("Layout", "base-layout", "container", "일반 페이지 레이아웃"),
    CadenzaComponentSpec("Table", "base-table", "data", "열과 행으로 구성된 데이터 표"),
    CadenzaComponentSpec("Tooltip", "base-tooltip", "overlay", "트리거에 연결된 도움말"),
    CadenzaComponentSpec("ConfirmModal", "basic-confirm-modal", "overlay", "확인 작업을 위한 모달"),
    CadenzaComponentSpec(
        "FormItem",
        "basic-form-item",
        "container",
        "라벨과 입력 요소를 묶는 폼 항목",
    ),
    CadenzaComponentSpec("Tree", "basic-tree", "tree", "계층형 탐색 데이터"),
    CadenzaComponentSpec("Uploader", "basic-uploader", "uploader", "파일 업로드 입력"),
    CadenzaComponentSpec("Chart", "chart", "chart", "범주와 수치 계열을 표현하는 차트"),
    CadenzaComponentSpec("ChartLegend", "chart-legend", "navigation", "차트 계열 범례"),
    CadenzaComponentSpec("CodeView", "code-view", "code", "코드 또는 JSON 원문 표시"),
    CadenzaComponentSpec("Content", "content", "container", "페이지의 주 콘텐츠 영역"),
    CadenzaComponentSpec("ControlBar", "control-bar", "container", "조회 및 작업 컨트롤 모음"),
    CadenzaComponentSpec("CopyButton", "copy-button", "copy", "값 복사 버튼"),
    CadenzaComponentSpec("CreateLayout", "create-layout", "container", "생성 화면 레이아웃"),
    CadenzaComponentSpec("DashboardLayout", "dashboard-layout", "container", "대시보드 레이아웃"),
    CadenzaComponentSpec("DetailLayout", "detail-layout", "container", "상세 화면 레이아웃"),
    CadenzaComponentSpec("Dropdown", "dropdown", "overlay", "트리거로 여는 드롭다운"),
    CadenzaComponentSpec("Filter", "filter", "container", "검색 조건 영역"),
    CadenzaComponentSpec("FilterButton", "filter-button", "message", "필터 실행 또는 상태 버튼"),
    CadenzaComponentSpec("Form", "form", "container", "입력 항목 그룹"),
    CadenzaComponentSpec("FormLayout", "form-layout", "container", "폼 페이지 레이아웃"),
    CadenzaComponentSpec("InputNumber", "input-number", "number", "숫자 입력"),
    CadenzaComponentSpec("ListLayout", "list-layout", "container", "목록 화면 레이아웃"),
    CadenzaComponentSpec("ListBox", "listbox", "navigation", "선택 가능한 목록"),
    CadenzaComponentSpec("Loader", "loader", "feedback", "영역 로딩 상태"),
    CadenzaComponentSpec("MiniLineChart", "mini-line-chart", "chart", "간단한 추이 차트"),
    CadenzaComponentSpec("NoData", "no-data", "empty", "조회 결과가 없는 상태"),
    CadenzaComponentSpec("Pagination", "pagination", "pagination", "페이지 이동 컨트롤"),
    CadenzaComponentSpec("Popover", "popover", "overlay", "트리거에 연결된 팝오버"),
    CadenzaComponentSpec("Progress", "progress", "feedback", "진행률 표시"),
    CadenzaComponentSpec("Segmented", "segmented", "segmented", "세그먼트 단일 선택"),
    CadenzaComponentSpec("Select", "select", "select", "옵션 선택 입력"),
    CadenzaComponentSpec("SidePanel", "side-panel", "overlay", "측면 상세 패널"),
    CadenzaComponentSpec("SideStep", "side-step", "step", "측면 단계 표시"),
    CadenzaComponentSpec("Sider", "sider", "container", "사이드 탐색 영역"),
    CadenzaComponentSpec("Skeleton", "skeleton", "feedback", "콘텐츠 자리 표시자"),
    CadenzaComponentSpec("Spinner", "spinner", "feedback", "작업 진행 스피너"),
    CadenzaComponentSpec("StatusHeader", "status-header", "message", "상태 중심 헤더"),
    CadenzaComponentSpec("StatusTag", "status-tag", "tag", "상태 태그"),
    CadenzaComponentSpec("Step", "step", "step", "단계 진행 목록"),
    CadenzaComponentSpec("StepIndicator", "step-indicator", "step", "간단한 단계 인디케이터"),
    CadenzaComponentSpec("Switch", "switch", "toggle", "켜짐과 꺼짐 상태 입력"),
    CadenzaComponentSpec("Toast", "toast", "message", "일시적 결과 알림"),
)

CADENZA_CUSTOM_COMPONENT_NAMES = tuple(
    spec.name for spec in CADENZA_CUSTOM_COMPONENT_SPECS
)
CADENZA_RENDERER_BY_COMPONENT = {
    spec.name: spec.data_comp for spec in CADENZA_CUSTOM_COMPONENT_SPECS
}


def _ref(name: str) -> dict[str, str]:
    return {"$ref": f"{COMMON_TYPES}{name}"}


def _array(item_schema: dict[str, Any], *, min_items: int = 0) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": "array", "items": item_schema}
    if min_items:
        schema["minItems"] = min_items
    return schema


def _option_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "label": {"type": "string"},
            "value": {"type": "string"},
            "description": {"type": "string"},
        },
        "required": ["label", "value"],
        "additionalProperties": False,
    }


def _properties_for(kind: ComponentKind) -> tuple[dict[str, Any], list[str]]:
    if kind == "container":
        return {
            "title": {"type": "string"},
            "description": {"type": "string"},
            "children": _ref("ChildList"),
            "variant": {"type": "string"},
        }, ["children"]
    if kind == "overlay":
        return {
            "title": {"type": "string"},
            "trigger": _ref("ComponentId"),
            "content": _ref("ComponentId"),
            "placement": {
                "enum": ["top", "right", "bottom", "left", "center"],
                "type": "string",
            },
        }, ["trigger", "content"]
    if kind == "message":
        return {
            "title": {"type": "string"},
            "description": {"type": "string"},
            "tone": {
                "enum": ["info", "success", "warning", "error", "neutral"],
                "type": "string",
            },
            "action": _ref("Action"),
        }, ["title"]
    if kind == "data":
        return {
            "title": {"type": "string"},
            "columns": _array({"type": "string"}, min_items=1),
            "rows": _array(
                {
                    "type": "object",
                    "additionalProperties": {
                        "type": ["string", "number", "boolean", "null"]
                    },
                }
            ),
            "action": _ref("Action"),
        }, ["columns", "rows"]
    if kind == "accordion":
        return {
            "items": _array(
                {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "content": _ref("ComponentId"),
                        "open": {"type": "boolean"},
                    },
                    "required": ["title", "content"],
                    "additionalProperties": False,
                },
                min_items=1,
            )
        }, ["items"]
    if kind == "tree":
        return {
            "nodes": _array(
                {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "label": {"type": "string"},
                        "parentId": {"type": "string"},
                        "status": {"type": "string"},
                    },
                    "required": ["id", "label"],
                    "additionalProperties": False,
                },
                min_items=1,
            ),
            "selectedId": {"type": "string"},
            "action": _ref("Action"),
        }, ["nodes"]
    if kind == "uploader":
        return {
            "label": {"type": "string"},
            "description": {"type": "string"},
            "accept": {"type": "string"},
            "multiple": {"type": "boolean"},
            "action": _ref("Action"),
        }, ["label"]
    if kind == "chart":
        return {
            "title": {"type": "string"},
            "labels": _array({"type": "string"}, min_items=1),
            "series": _array(
                {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "values": _array({"type": "number"}, min_items=1),
                    },
                    "required": ["name", "values"],
                    "additionalProperties": False,
                },
                min_items=1,
            ),
        }, ["labels", "series"]
    if kind == "navigation":
        return {
            "label": {"type": "string"},
            "items": _array(_option_schema(), min_items=1),
            "selected": {"type": "string"},
            "action": _ref("Action"),
        }, ["items"]
    if kind == "code":
        return {
            "code": {"type": "string"},
            "language": {"type": "string"},
            "title": {"type": "string"},
        }, ["code"]
    if kind == "copy":
        return {
            "value": {"type": "string"},
            "label": {"type": "string"},
        }, ["value"]
    if kind == "empty":
        return {
            "title": {"type": "string"},
            "description": {"type": "string"},
            "action": _ref("Action"),
        }, ["title"]
    if kind == "feedback":
        return {
            "label": {"type": "string"},
            "value": {"type": "number", "minimum": 0},
            "max": {"type": "number", "exclusiveMinimum": 0},
            "variant": {"type": "string"},
        }, []
    if kind == "pagination":
        return {
            "page": {"type": "integer", "minimum": 1},
            "totalPages": {"type": "integer", "minimum": 1},
            "action": _ref("Action"),
        }, ["page", "totalPages"]
    if kind in {"select", "segmented"}:
        return {
            "label": {"type": "string"},
            "options": _array(_option_schema(), min_items=1),
            "value": {"type": "string"},
            "action": _ref("Action"),
        }, ["options"]
    if kind == "number":
        return {
            "label": {"type": "string"},
            "value": {"type": "number"},
            "min": {"type": "number"},
            "max": {"type": "number"},
            "step": {"type": "number", "exclusiveMinimum": 0},
            "action": _ref("Action"),
        }, ["value"]
    if kind == "step":
        return {
            "items": _array(
                {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "status": {
                            "enum": ["pending", "active", "complete", "error"],
                            "type": "string",
                        },
                    },
                    "required": ["title", "status"],
                    "additionalProperties": False,
                },
                min_items=1,
            )
        }, ["items"]
    if kind == "tag":
        return {
            "text": {"type": "string"},
            "tone": {
                "enum": ["gray", "green", "blue", "yellow", "red"],
                "type": "string",
            },
        }, ["text"]
    if kind == "toggle":
        return {
            "label": {"type": "string"},
            "value": {"type": "boolean"},
            "action": _ref("Action"),
        }, ["value"]
    raise ValueError(f"Unsupported Cadenza component kind: {kind}")


def _component_schema(spec: CadenzaComponentSpec) -> dict[str, Any]:
    properties, required = _properties_for(spec.kind)
    return {
        "type": "object",
        "description": spec.description,
        "allOf": [
            _ref("ComponentCommon"),
            {
                "type": "object",
                "properties": {
                    "component": {"const": spec.name},
                    **properties,
                },
                "required": ["component", *required],
            },
        ],
        "unevaluatedProperties": False,
    }


def create_cadenza_catalog(locale: str = "ko-KR"):
    basic_catalog = BasicCatalog("0.9", locale=locale)
    document = deepcopy(basic_catalog.to_json())
    document["catalogId"] = CADENZA_CATALOG_ID
    document["title"] = "Cadenza Composer Catalog"
    document["description"] = (
        "A2UI v0.9 Basic components and Cadenza Composer custom components."
    )
    document["instructions"] = (
        "Use standard A2UI components for common content and controls. "
        "Use Cadenza custom components only when their named enterprise UI pattern "
        "matches the request. Component children must always be referenced by ID."
    )
    document["components"].update(
        {
            spec.name: _component_schema(spec)
            for spec in CADENZA_CUSTOM_COMPONENT_SPECS
        }
    )
    document["$defs"]["anyComponent"] = {
        "oneOf": [
            {"$ref": f"#/components/{name}"}
            for name in document["components"]
        ],
        "discriminator": {"propertyName": "component"},
    }
    return Catalog.from_json(document)
