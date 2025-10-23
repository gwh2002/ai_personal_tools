<!-- Save this plan at the repo root as `YYYY.MM.DD_WORK_[service_name_or_component_name].md` (created from this template). -->
# WORK: [Problem Title]
**Date**: [Current Date]
**Status**: PLANNING

## 🎯 Problem Statement
[User-reported issue verbatim]

## 🔍 Root Cause Analysis
- **Symptom**: [What user sees]
- **Root Cause**: [Actual underlying issue]
- **Evidence**: [Code snippets, logs, schema]
- **Affected Systems**:
  - Components: [List affected components]
  - Services: [List affected services]
  - Database: [Tables/RLS/Functions]

## 📚 Required Documentation
[CRITICAL - Link documentation that EXECUTER MUST read before implementation:]

### Primary Documentation (Read First)
- **For [Problem Area]**: `docs/[category]/[SPECIFIC-DOC.md]` - [Why this is needed]
- **Architecture Pattern**: `docs/architecture/[RELEVANT.md]` - [Specific section]

### Supporting Documentation
- **LEARNINGS.md**: [Specific learning entries that apply]
- **SYSTEMS.md**: [Specific sections: e.g., #22-module-system]
- `agent_rules.md`: [Specific rules that apply]
- **Schema**: [Database tables and RLS policies involved]

### Code References
- **Similar Implementation**: `[repo path to similar code]` - [How it relates]
- **Pattern Example**: `[repo path to pattern usage]` - [What to follow]

## 🛠 Solution Design
- **Strategy**: [How to fix properly]
- **Patterns to Apply**: [From documentation]
- **Database Changes**: [Migrations/RLS/Triggers]
- **Validation Approach**: [How to ensure it works]
- **Potential Risks**: [What could break]

## ⚠ Common Violations to Prevent
[Proactively identify and plan to prevent these violations:]
- **Console.log**: All debugging statements must be wrapped in `if (__DEV__)`
- **Error Handling**: All catch blocks must import and use logger
- **Type Safety**: No 'any' types, especially in catch blocks
- **i18n**: All user-facing text must use namespace functions
- **Import Order**: React → Third-party → Internal → Relative

## 📊 Execution Plan
[Phases go here]
