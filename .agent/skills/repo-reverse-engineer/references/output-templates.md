# Output Report Templates (00–09)

This reference defines the structured templates for the 10 reverse-engineering reports.
Placeholders use `{{placeholder}}` markers.

---

# Template 00: `00-SUMMARY.md`

```markdown
# 00 - Executive Summary: {{repo_name}}

## Repository Overview
- **Repository URL / Path**: `{{repo_url}}`
- **Analyzed Commit / Ref**: `{{commit_sha}}` (Branch: `{{branch}}`)
- **Primary Language & Stack**: {{primary_stack}}
- **License**: {{license_spdx}} (Detected in `{{license_file}}`)
- **Mode**: {{analysis_mode}} | **Target Audience**: {{audience}}

## Purpose & Problem Solved
{{purpose_description}}

## High-Level Architecture & Key Components
- **Core Architecture Style**: {{architecture_style}} (e.g. Layered Monolith, Microservices, Event-Driven)
- **Primary Subsystems**:
  1. `{{subsystem_1}}`: {{subsystem_1_desc}}
  2. `{{subsystem_2}}`: {{subsystem_2_desc}}
  3. `{{subsystem_3}}`: {{subsystem_3_desc}}

## Top 5 Things to Know Before Touching This Codebase
1. {{top_thing_1}} (Citing `{{citation_1}}`)
2. {{top_thing_2}} (Citing `{{citation_2}}`)
3. {{top_thing_3}} (Citing `{{citation_3}}`)
4. {{top_thing_4}} (Citing `{{citation_4}}`)
5. {{top_thing_5}} (Citing `{{citation_5}}`)

## Quick-Start Commands
- **Install Dependencies**: `{{install_cmd}}`
- **Run Locally**: `{{start_cmd}}`
- **Execute Tests**: `{{test_cmd}}`
```

---

# Template 01: `01-ARCHITECTURE.md`

```markdown
# 01 - System Architecture & Topology: {{repo_name}}

## Architectural Topology Diagram

```mermaid
{{mermaid_topology_diagram}}
```

## Core Architectural Boundaries & Modules
- **API & Presentation Layer**: `{{api_layer_path}}`
  - Responsibilities: {{api_responsibilities}}
- **Domain & Business Logic Layer**: `{{domain_layer_path}}`
  - Responsibilities: {{domain_responsibilities}}
- **Persistence & Data Storage Layer**: `{{persistence_layer_path}}`
  - Responsibilities: {{persistence_responsibilities}}
- **Infrastructure & Integrations**: `{{infra_layer_path}}`
  - Responsibilities: {{infra_responsibilities}}

## Component Interaction & Data Pathways
{{component_interaction_narrative}}

## Cross-Cutting Concerns
- **Authentication & Authorization**: Handled via `{{auth_mechanism}}` at `{{auth_citation}}`.
- **Error Handling Strategy**: {{error_handling_strategy}} at `{{error_citation}}`.
- **Telemetry & Logging**: {{logging_strategy}} at `{{logging_citation}}`.
```

---

# Template 02: `02-CODE-MAP.md`

```markdown
# 02 - Codebase Navigation Map: {{repo_name}}

## Directory Hierarchy & Purpose

| Directory Path | Role / Purpose | Dominant Technologies | Primary Entry / Key Files |
| :--- | :--- | :--- | :--- |
| `{{dir_1}}` | {{dir_1_purpose}} | {{dir_1_tech}} | `{{dir_1_key_file}}` |
| `{{dir_2}}` | {{dir_2_purpose}} | {{dir_2_tech}} | `{{dir_2_key_file}}` |
| `{{dir_3}}` | {{dir_3_purpose}} | {{dir_3_tech}} | `{{dir_3_key_file}}` |

## Ranked Entrypoints

| Rank | Path:Line | Type | Confidence | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `{{ep_1_path}}` | {{ep_1_type}} | {{ep_1_conf}} | {{ep_1_reason}} |
| 2 | `{{ep_2_path}}` | {{ep_2_type}} | {{ep_2_conf}} | {{ep_2_reason}} |
| 3 | `{{ep_3_path}}` | {{ep_3_type}} | {{ep_3_conf}} | {{ep_3_reason}} |

## Key File Index & Hotspots
- `{{hotspot_file_1}}`: {{hotspot_file_1_desc}} (Citing `{{hotspot_citation_1}}`)
- `{{hotspot_file_2}}`: {{hotspot_file_2_desc}} (Citing `{{hotspot_citation_2}}`)
```

---

# Template 03: `03-API-AND-DATA.md`

```markdown
# 03 - API Surface & Data Model: {{repo_name}}

## Public HTTP / RPC Routes

| Method | Route Path | Handler Citation | Auth Required | Description |
| :--- | :--- | :--- | :--- | :--- |
| `{{route_1_method}}` | `{{route_1_path}}` | `{{route_1_citation}}` | {{route_1_auth}} | {{route_1_desc}} |
| `{{route_2_method}}` | `{{route_2_path}}` | `{{route_2_citation}}` | {{route_2_auth}} | {{route_2_desc}} |

## Database Entity-Relationship Diagram

```mermaid
{{mermaid_erd_diagram}}
```

## Entity Catalog & Schema Definitions
### Entity: `{{entity_1_name}}`
- **Source**: `{{entity_1_file}}`
- **Fields**:
  - `{{field_1_name}}` (`{{field_1_type}}`): {{field_1_desc}}
  - `{{field_2_name}}` (`{{field_2_type}}`): {{field_2_desc}}
- **Relationships**: {{entity_1_relations}}
```

---

# Template 04: `04-FLOWS.md`

```markdown
# 04 - Critical Execution Flows & Sequences: {{repo_name}}

## Flow 1: {{flow_1_title}}

### Sequence Diagram
```mermaid
{{flow_1_sequence_mermaid}}
```

### Step-by-Step Execution Trace
1. **Initiation**: Request arrives at `{{flow_1_step_1_citation}}`.
2. **Processing & Validation**: Handled by `{{flow_1_step_2_citation}}`.
3. **Data Mutation**: Persisted at `{{flow_1_step_3_citation}}`.
4. **Response / Completion**: Returned via `{{flow_1_step_4_citation}}`.

## Flow 2: {{flow_2_title}}
{{flow_2_description}}
```
