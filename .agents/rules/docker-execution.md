---
name: docker-execution-only
description: Mandates that all frontend/backend builds, package installations, and type checks must run exclusively inside Docker containers, keeping the local host clean of node_modules, and deferring rebuilds until all edits are complete.
---

# Docker-Only Execution Guardrail

## Invariants
1. **No Local `node_modules`**: Never install, generate, or maintain `node_modules` on the local Windows host. If accidentally created, remove it immediately.
2. **Container As Execution Engine**:
   - Typechecking: `docker exec procurement_frontend npx tsc --noEmit`
   - Production Build: `docker exec procurement_frontend npm run build`
   - Package Management: `docker exec procurement_frontend npm install <package>`
   - Backend Commands: `docker exec procurement_backend <command>`
3. **Ignore Host Type Server Module Warnings**: Host IDE warnings indicating `Cannot find module 'react'` or `Cannot find module 'vite'` are expected because dependencies live strictly inside the container volume. Always use the container's `tsc` exit status as the single source of truth for TypeScript errors.
4. **No Intermediate Rebuilds**: Never trigger production builds (`docker exec procurement_frontend npm run build` or Docker container rebuilds) after intermediate or single-file edits. Rely on development server HMR/live-reloads and only run a build validation step once at the very end when all edits across the entire task are fully complete.
