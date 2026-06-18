---
req_ids: [FR-001, FR-002]
diagram_type: flowchart
slug: test-slug
---

# Order Processing Flow

```mermaid
flowchart TD
    A[Start] --> B[Receive Order]
    B --> C{Valid?}
    C -->|Yes| D[Process Payment]
    C -->|No| E[Reject Order]
    D --> F[Ship Order]
    F --> G[End]
    E --> G
```
