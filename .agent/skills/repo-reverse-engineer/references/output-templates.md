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


---

# Template 05: `05-DEPENDENCIES.md`

```markdown
# 05 - Dependencies & External Integrations: {{repo_name}}

## Dependency Graph Overview

```mermaid
{{mermaid_dep_graph}}
```

## Internal Module Dependencies & Hubs
- **Most Central Module**: `{{central_module_1}}` (In-degree: {{in_deg_1}}, Out-degree: {{out_deg_1}})
- **Circular Dependencies**: {{circular_dependency_report}}

## Key External Dependencies & Licenses

| Package / Library | Version | Purpose | License | Risk Level |
| :--- | :--- | :--- | :--- | :--- |
| `{{dep_1_name}}` | `{{dep_1_version}}` | {{dep_1_purpose}} | {{dep_1_license}} | {{dep_1_risk}} |
| `{{dep_2_name}}` | `{{dep_2_version}}` | {{dep_2_purpose}} | {{dep_2_license}} | {{dep_2_risk}} |

## Third-Party Integrations & Services
- `{{service_1}}`: {{service_1_desc}} (Citing `{{service_1_citation}}`)
- `{{service_2}}`: {{service_2_desc}} (Citing `{{service_2_citation}}`)
```

---

# Template 06: `06-CONFIG-AND-OPS.md`

```markdown
# 06 - Configuration & Operational Infrastructure: {{repo_name}}

## Environment Variables & Configuration Keys

| Variable / Key | Category | Default / Example | Required | Citation |
| :--- | :--- | :--- | :--- | :--- |
| `{{env_1_name}}` | {{env_1_category}} | `{{env_1_default}}` | {{env_1_required}} | `{{env_1_citation}}` |
| `{{env_2_name}}` | {{env_2_category}} | `{{env_2_default}}` | {{env_2_required}} | `{{env_2_citation}}` |

## Infrastructure & Containerization
- **Docker / Container Specs**: `{{docker_citation}}`
  - Base Image: `{{base_image}}`
  - Build Steps: {{docker_build_summary}}
- **Orchestration & Deployments**: {{orchestration_details}} (`{{orchestration_citation}}`)
- **CI/CD Pipelines**: `{{ci_pipeline_citation}}` running {{ci_jobs_summary}}

## Operational Observability & Health Checks
- **Health Check Endpoint**: `{{health_check_endpoint}}` at `{{health_check_citation}}`
- **Metrics & Logging**: {{metrics_details}}
```

---

# Template 07: `07-RISKS-AND-DEBT.md`

```markdown
# 07 - Technical Debt, Vulnerabilities & Risks: {{repo_name}}

## Security & Secrets Audit
- **Committed Secret Findings**: {{secret_findings_summary}}
  - Finding: `{{secret_finding_1_masked}}` in `{{secret_finding_1_citation}}`
- **Authentication & Authorization Gaps**: {{auth_gaps_details}} (Citing `{{auth_gap_citation}}`)

## Architectural Technical Debt & Anti-Patterns
1. **{{debt_1_title}}**: {{debt_1_desc}} (Citing `{{debt_1_citation}}`)
2. **{{debt_2_title}}**: {{debt_2_desc}} (Citing `{{debt_2_citation}}`)

## Missing or Fragile Components
- **Test Coverage Deficiencies**: {{test_gaps_details}}
- **Documentation Discrepancies**: {{doc_drift_details}}
```

---

# Template 08: `08-REBUILD-BLUEPRINT.md`

```markdown
# 08 - Clean-Room Rebuild Blueprint: {{repo_name}}

## System Architecture Blueprint
{{rebuild_architecture_overview}}

## Rebuild Milestones & Phased Plan

### Milestone 1: {{milestone_1_name}}
- **Objective**: {{milestone_1_objective}}
- **Key Deliverables**:
  - `{{m1_file_1}}`: {{m1_file_1_desc}}
  - `{{m1_file_2}}`: {{m1_file_2_desc}}
- **Implementation Prompt for Coding Agent**:
> {{m1_agent_prompt}}

### Milestone 2: {{milestone_2_name}}
- **Objective**: {{milestone_2_objective}}
- **Key Deliverables**:
  - `{{m2_file_1}}`: {{m2_file_1_desc}}
- **Implementation Prompt for Coding Agent**:
> {{m2_agent_prompt}}

### Milestone 3: {{milestone_3_name}}
- **Objective**: {{milestone_3_objective}}
- **Implementation Prompt for Coding Agent**:
> {{m3_agent_prompt}}

### Milestone 4: {{milestone_4_name}}
- **Objective**: {{milestone_4_objective}}
- **Implementation Prompt for Coding Agent**:
> {{m4_agent_prompt}}

## Critical Path & Complexity Pitfalls
- **Risk 1**: {{rebuild_risk_1}}
- **Risk 2**: {{rebuild_risk_2}}
```

---

# Template 09: `09-GLOSSARY-AND-QA.md`

```markdown
# 09 - Domain Glossary & Interrogation Q&A: {{repo_name}}

## Domain Terminology Glossary

| Term | Technical Definition in this Repository | Canonical File Citation |
| :--- | :--- | :--- |
| **`{{term_1}}`** | {{term_1_def}} | `{{term_1_citation}}` |
| **`{{term_2}}`** | {{term_2_def}} | `{{term_2_citation}}` |
| **`{{term_3}}`** | {{term_3_def}} | `{{term_3_citation}}` |

## Architecture Decisions & Interrogation Q&A

### Q1: Why does the system structure {{decision_1_topic}} this way?
**Answer**: {{decision_1_answer}} (Citing `{{decision_1_citation}}`).

### Q2: How does the system handle {{decision_2_topic}}?
**Answer**: {{decision_2_answer}} (Citing `{{decision_2_citation}}`).

### Q3: What happens when {{decision_3_failure_scenario}} occurs?
**Answer**: {{decision_3_answer}} (Citing `{{decision_3_citation}}`).
```
