# Healthcare Interoperability Failures: A Practical Gist

Healthcare interoperability fails when systems exchange data successfully at the transport level but disagree about its meaning, structure, identity, or context.

## Common Failure Modes

### 1. Patient and Practitioner Identity Mismatch

- The same person is represented by different identifiers across systems.
- Identifiers are reused, missing, malformed, or assigned by the wrong authority.
- A practitioner reference points to a display name but not a resolvable resource.

**Result:** records are linked to the wrong person or cannot be linked at all.

### 2. Invalid or Incomplete FHIR Resources

- Required fields are missing.
- Resource types do not match the referenced data.
- Profiles, extensions, or terminology bindings are ignored.
- JSON is syntactically valid but violates the applicable FHIR profile.

**Result:** ingestion rejects the resource, or downstream systems interpret it inconsistently.

### 3. Terminology and Coding Differences

- Systems use different code systems for the same concept.
- Local codes are sent without a translation or namespace.
- Display text is treated as authoritative instead of the coded value.
- Units and value-set versions differ.

**Result:** analytics, decision support, and clinical workflows produce incomplete or misleading results.

### 4. Reference and Endpoint Problems

- References are relative when an absolute URL is required, or vice versa.
- URLs point to unstable, inaccessible, or environment-specific endpoints.
- A resource is referenced before it is available to the receiving system.
- Authentication and authorization rules differ between environments.

**Result:** valid-looking resources cannot be resolved or retrieved.

### 5. Date, Time, and Context Loss

- Time zones are omitted or converted incorrectly.
- Event time, recording time, and effective time are conflated.
- Encounter, facility, or practitioner context is dropped during transformation.

**Result:** events appear in the wrong order or are attributed to the wrong setting.

### 6. Silent Data Loss During Transformation

- Unsupported fields are discarded without a warning.
- Arrays are flattened into a single value.
- Unknown extensions are removed.
- Null, absent, and empty values are treated as equivalent.

**Result:** the message is delivered successfully but no longer represents the source record.

## Detection Checklist

Before accepting an exchange, verify:

1. The payload is valid JSON and conforms to the expected FHIR resource type.
2. Required identifiers have the correct system, value, and assigning authority.
3. References resolve in the target environment.
4. Codes, units, and value sets are from agreed terminology systems.
5. Dates include the required precision and time-zone information.
6. Profiles and extensions are preserved or explicitly mapped.
7. Validation failures, warnings, and dropped fields are observable.
8. The transformed output can be traced back to its source record.

## Prevention Pattern

Treat interoperability as a contract, not a file-transfer problem:

- Define resource profiles and examples before implementation.
- Validate at both the sending and receiving boundaries.
- Maintain an identifier and terminology mapping registry.
- Use deterministic transformation rules with explicit loss reporting.
- Test real edge cases: duplicates, missing references, conflicting identifiers, time zones, and unknown extensions.
- Monitor rejection rates, unresolved references, validation warnings, and data-loss events.

## Key Takeaway

An exchange is interoperable only when the receiving system can identify the subject, understand the meaning, resolve the references, preserve the clinical context, and detect what could not be carried across.
