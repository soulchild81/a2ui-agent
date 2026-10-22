# A2UI Agent

사용자 요청과 선택된 컴포넌트 Catalog를 결합해 LLM에 전달하고, 응답을 A2UI v0.9 메시지로 파싱·검증하여 SSE로 전송하는 FastAPI Agent입니다.

## 주요 기능

- `a2ui-agent-sdk` 기반 Catalog 프롬프트 생성
- A2UI Basic Catalog 및 전체 18개 표준 타입의 Cadenza Composer Renderer 지원
- Gemini OpenAI 호환 API와 Local Codex CLI 선택 지원
- `<a2ui-json>` 응답 파싱 및 Catalog 스키마 검증
- 잘못된 LLM 응답 재시도
- A2UI 메시지와 단계별 처리 시간 SSE 전송
- 사용자 액션 처리 후 Data Model 갱신
- LLM 요청 본문과 원문 응답을 확인할 수 있는 Generation Trace 제공

## 처리 흐름

```text
Client Query + Renderer Capabilities
              ↓
        FastAPI Controller
              ↓
      Catalog Profile 선택
              ↓
 A2UI SDK prompt_snippet 생성
              ↓
   Gemini API / Local Codex 호출
              ↓
 <a2ui-json> 파싱 및 스키마 검증
              ↓
 generation_context + timing + A2UI SSE
              ↓
         Client Renderer
```

## 기술 스택

- Python 3.13
- FastAPI 0.115
- `a2ui-agent-sdk` 0.9.0
- Pydantic Settings
- HTTPX
- uv
- pytest, Ruff

## 실행 방법

### 1. 요구사항

- Python 3.13
- [uv](https://docs.astral.sh/uv/)
- LLM 모드 사용 시 Gemini API 키 또는 로그인된 Codex CLI

### 2. 의존성 설치

```bash
uv sync --python 3.13
```

### 3. 환경변수 설정

```bash
cp .env.example .env
```

API 키는 `.env`에만 저장하고 Git에 커밋하지 않습니다.

#### Mock 모드

```dotenv
A2UI_MODE=mock
```

#### Gemini API

Gemini의 OpenAI 호환 Chat Completions API를 사용합니다.

```dotenv
A2UI_MODE=llm
LLM_PROVIDER=api
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_MODEL=your-gemini-model
LLM_API_KEY=your-api-key
LLM_TIMEOUT_SECONDS=30
```

#### Local Codex CLI

```dotenv
A2UI_MODE=llm
LLM_PROVIDER=codex_cli
CODEX_CLI_EXECUTABLE=codex
CODEX_CLI_MODEL=
CODEX_CLI_TIMEOUT_SECONDS=120
```

Local Codex는 임시 디렉터리, 임시 세션, 읽기 전용 Sandbox에서 실행하며 API 키를 하위 프로세스 환경에 전달하지 않습니다.

### 4. 서버 실행

```bash
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health Check:

```bash
curl http://127.0.0.1:8000/health
```

## API

### A2UI 생성

```http
POST /api/v1/a2ui/stream
Content-Type: application/json
```

```json
{
  "query": "10만 원 이하 무선 이어폰을 추천해줘",
  "mode": "llm",
  "llm_provider": "api",
  "catalog_profile": "cadenza",
  "renderer_capabilities": {}
}
```

SSE 이벤트는 다음 순서로 전달됩니다.

```text
generation_context
timing
a2ui
done
```

오류가 발생하면 `error` 이벤트로 코드와 메시지를 전달합니다.

### 사용자 액션 처리

```http
POST /api/v1/a2ui/actions
Content-Type: application/json
```

```json
{
  "name": "select_product",
  "surfaceId": "recommendation-surface",
  "sourceComponentId": "button-0",
  "context": {
    "productId": "soundfit-air",
    "productName": "SoundFit Air"
  }
}
```

## Catalog 프로필

| 프로필 | 허용 범위 |
|---|---|
| `cadenza` | 표준 18개와 Composer 전용 47개를 합친 65개 타입을 JSON Schema로 제한·검증 |
| `basic` | A2UI Basic Catalog 전체 |

Agent는 클라이언트가 전달한 Renderer Capabilities와 선택된 Catalog ID가 일치하는지 확인합니다. LLM이 미등록 컴포넌트를 반환하면 검증 단계에서 차단합니다.

### Cadenza Custom Schema 구성

`app/a2ui/catalog/cadenza.py`가 Cadenza Catalog의 단일 Agent 계약입니다.

- 공식 Basic Catalog 문서에 47개 Composer 전용 컴포넌트 스키마를 추가합니다.
- 최종 Catalog ID는 `https://okestro.dev/a2ui/catalogs/cadenza-composer-v0.9.json`입니다.
- 컨테이너, 오버레이, 데이터, 입력, 진행 상태 등 역할별로 필수 속성을 검증합니다.
- `ComponentId`, `ChildList`, `Action`, `ComponentCommon`은 A2UI v0.9 공통 타입을 참조합니다.
- SDK가 확장된 Catalog Schema를 LLM 시스템 프롬프트에 포함하고, 동일한 Schema로 LLM 응답을 다시 검증합니다.

따라서 Custom 타입은 단순 CSS 클래스 문자열이 아니라 Agent JSON Schema와 Client Renderer 양쪽에 모두 등록되어야 사용할 수 있습니다.

생성된 Catalog JSON 문서는 다음 API로 직접 확인할 수 있습니다.

```bash
curl http://127.0.0.1:8000/api/v1/a2ui/catalogs/cadenza
```

## 프로젝트 구조

```text
app/
├── a2ui/
│   ├── controller/     # REST/SSE API
│   ├── catalog/        # Cadenza Custom Catalog와 JSON Schema 생성
│   ├── domain/         # 요청, 결과, 액션 모델
│   └── service/        # Catalog, Generator, 검증
├── common/
│   ├── config/         # 환경 설정
│   └── error/          # 애플리케이션 오류
└── main.py             # FastAPI 진입점
tests/                  # API 및 Generator 테스트
```

## 검증

```bash
uv run ruff check .
uv run pytest -q
```

## 보안 원칙

- API 키와 인증정보를 코드·로그·SSE에 포함하지 않습니다.
- LLM이 생성한 HTML이나 JavaScript를 실행하지 않습니다.
- LLM 응답은 A2UI SDK와 선택된 Catalog로 검증합니다.
- Local Codex에는 필요한 최소 환경변수만 전달합니다.

