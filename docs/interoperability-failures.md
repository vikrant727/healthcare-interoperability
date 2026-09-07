# En Route Health

## FHIR Interoperability, Data Reconciliation & EHR Migration

### Overview

**En Route Health** is a healthcare interoperability project focused on a practical problem in EHR data exchange and migration: **moving clinical data between systems while resolving differences in identifiers, resource dependencies, references, and receiving-system data models.**

The initial implementation uses **Synthea synthetic EHR data** as the source and **HAPI FHIR** as the receiving FHIR server. The project is designed to evolve toward a flexible interoperability and reconciliation framework applicable to real-world EHR migration and integration scenarios.

### Problem

FHIR makes clinical data exchange technically standardized, but successful interoperability requires more than transmitting valid FHIR JSON.

A clinical resource may contain references to:

* Practitioners
* Organizations
* Locations
* Patients
* Encounters
* Other dependent resources

The receiving system may already contain a corresponding resource, may represent it differently, or may not contain it at all.

For example, during the initial transaction test, HAPI FHIR rejected a patient transaction because the referenced Practitioner could not be resolved using the source system's NPI identifier.

The Practitioner existed in a separate source dataset but was not present in the receiving system.

### Initial Interoperability Scenario

**Source**

Synthea FHIR transaction

**Referenced provider**

NPI: `9999962993`

**Source Practitioner**

Dr. Fernande593 Mosciski958

**Receiving system**

HAPI FHIR R4

**Initial result**

Provider reference could not be resolved.

**Resolution**

The source Practitioner was identified using its NPI, loaded into the receiving FHIR server, and subsequently verified through an identifier-based FHIR search.

The original transaction then progressed to the next unresolved dependency: a Location reference.

This demonstrates the project's core approach:

> **Use integration failures to identify, investigate, reconcile, and resolve cross-system dependencies.**

### Matching and Resolution Strategy

The eventual solution is not intended to simply copy missing resources from one system into another.

A receiving system may resolve an external reference through several strategies:

1. **Match** an existing resource using an identifier such as NPI.
2. **Map** the external identifier to an existing internal resource.
3. **Apply a configured default** when business rules permit it.
4. **Create** a resource when appropriate.
5. **Queue an exception** when the match is ambiguous or requires human reconciliation.

The framework is therefore being designed around **reference resolution and configurable matching strategies**, rather than simple resource replication.

### Current Architecture

```text
Synthea
   │
   │ FHIR data
   ▼
Python Interoperability Layer
   │
   ├── Analyze references
   ├── Identify dependencies
   ├── Match identifiers
   ├── Resolve missing resources
   └── Record interoperability failures
   │
   ▼
HAPI FHIR R4
   │
   └── Validate / process transaction
```

### Future Direction

The project will progressively explore:

* FHIR resource dependency analysis
* Provider and organization matching
* Cross-system identifier mapping
* Reference resolution
* Data reconciliation
* Migration sequencing
* Exception handling
* FHIR transaction processing
* C-CDA interoperability
* Automated interoperability testing
* Azure-based deployment using Azure Health Data Services
* Eventually, EHR migration scenarios involving real-world interoperability constraints

### Why This Matters

EHR migration and integration projects frequently involve systems that have different identifiers, different representations of the same entities, and different assumptions about which resources already exist.

The objective of En Route Health is to demonstrate that **interoperability is not simply an API problem—it is a data matching, reconciliation, dependency management, and business-rule problem as well.**

The project uses synthetic data during development so that these scenarios can be explored safely without exposing patient information.

### Current Status

**Phase 1 — FHIR interoperability investigation**

* Synthea configured as synthetic EHR source
* HAPI FHIR configured as receiving system
* Python interoperability tooling established
* FHIR transaction successfully submitted to HAPI
* Provider matching failure identified
* Practitioner resolved using NPI
* Practitioner loaded and verified in HAPI
* Next dependency failure identified: Location matching

The project is intentionally being developed **failure by failure**, documenting each interoperability issue, its root cause, resolution strategy, and verification result.
