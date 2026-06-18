---
req_ids: [FR-001, FR-002]
fidelity: wireframe
slug: test-slug
screen: login
---

# Login

> Wireframe — req_ids: [FR-001, FR-002]

## Layout

### Header

- **Logo** [left]
- **App title**: BA Daily Ops [center]

### Main Content

#### Section: Credential Form

| Region | Type | Content |
|--------|------|---------|
| Center panel | form | Username field, Password field, Sign-in button |

#### Actions

- [Primary CTA] Sign in — submits credentials
- [Secondary CTA] Forgot password — opens recovery flow

### Footer

- Status info [left]: Version 1.0
- Support link [right]: Help

## Interaction Notes

- Username and Password fields are required (marked with *).
- Sign-in button is disabled until both fields are non-empty.
- Form validation: error message displayed inline below the field on failure.
