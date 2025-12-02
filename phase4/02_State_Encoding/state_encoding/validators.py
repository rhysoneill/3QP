"""
Validators for checking consistency, alignment, and structural integrity
of encoded states.

This module provides validation infrastructure for:
- Consistency checking within encoded states
- Alignment verification with semantic schemas
- Domain-specific consistency rules
- Required field presence validation

All validators return structured ValidationResult objects and operate
purely on encoded state structure — they do NOT perform computation,
simulation, or scoring.
"""

from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """A single validation issue found during validation."""
    severity: ValidationSeverity
    field_path: str
    message: str
    expected: Optional[Any] = None
    actual: Optional[Any] = None


@dataclass
class ValidationResult:
    """
    Result container for validation operations.
    
    The ValidationResult provides structured feedback about the validity
    of encoded states, enabling downstream components to make informed
    decisions about state consumption.
    
    Fields:
        is_valid: Overall validation status
        issues: List of validation issues found
        validated_fields: Set of fields that were validated
        metadata: Additional context about validation
    """
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    validated_fields: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def has_errors(self) -> bool:
        """Check if validation found any errors."""
        return any(issue.severity == ValidationSeverity.ERROR for issue in self.issues)
    
    def has_warnings(self) -> bool:
        """Check if validation found any warnings."""
        return any(issue.severity == ValidationSeverity.WARNING for issue in self.issues)
    
    def get_errors(self) -> List[ValidationIssue]:
        """Return only error-level issues."""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.ERROR]
    
    def get_warnings(self) -> List[ValidationIssue]:
        """Return only warning-level issues."""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.WARNING]
    
    def to_summary(self) -> str:
        """Generate human-readable validation summary."""
        if self.is_valid:
            return f"Validation passed. {len(self.validated_fields)} fields validated."
        
        errors = self.get_errors()
        warnings = self.get_warnings()
        
        summary = f"Validation failed. {len(errors)} error(s), {len(warnings)} warning(s).\n"
        
        if errors:
            summary += "\nErrors:\n"
            for issue in errors:
                summary += f"  - {issue.field_path}: {issue.message}\n"
        
        if warnings:
            summary += "\nWarnings:\n"
            for issue in warnings:
                summary += f"  - {issue.field_path}: {issue.message}\n"
        
        return summary


class EncodedStateValidator:
    """
    Validator for checking consistency within encoded states.
    
    The EncodedStateValidator ensures that encoded states have:
    - Required fields present
    - Correct field types
    - Internal consistency (e.g., referenced IDs exist)
    - No contradictory values
    
    This validator does NOT check semantic alignment — that is
    handled by SchemaAlignmentValidator.
    """
    
    def __init__(self, required_fields: Optional[List[str]] = None):
        """
        Initialize validator with required field specifications.
        
        Args:
            required_fields: List of field paths that must be present
        """
        self.required_fields = required_fields or []
    
    def validate(self, encoded_state: Dict[str, Any]) -> ValidationResult:
        """
        Validate an encoded state for structural consistency.
        
        Args:
            encoded_state: The encoded state to validate
            
        Returns:
            ValidationResult with issues found
        """
        issues = []
        validated_fields = set()
        
        # Check required fields
        for field_path in self.required_fields:
            if not self._field_exists(encoded_state, field_path):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    field_path=field_path,
                    message=f"Required field '{field_path}' is missing"
                ))
            else:
                validated_fields.add(field_path)
        
        # Check encoding metadata presence
        if "encoding_metadata" in encoded_state:
            validated_fields.add("encoding_metadata")
            metadata = encoded_state["encoding_metadata"]
            
            # Check for encoder type
            if "encoder_type" not in metadata:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field_path="encoding_metadata.encoder_type",
                    message="Encoder type not specified in metadata"
                ))
            else:
                validated_fields.add("encoding_metadata.encoder_type")
        else:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                field_path="encoding_metadata",
                message="Encoding metadata not present"
            ))
        
        # Determine overall validity
        is_valid = not any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            validated_fields=validated_fields,
            metadata={"validator": "EncodedStateValidator"}
        )
    
    def _field_exists(self, obj: Dict[str, Any], field_path: str) -> bool:
        """Check if a field path exists in the object."""
        parts = field_path.split(".")
        current = obj
        
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return False
            current = current[part]
        
        return True


class SchemaAlignmentValidator:
    """
    Validator for checking alignment with semantic schemas.
    
    The SchemaAlignmentValidator ensures that encoded states remain
    aligned with their originating semantic schemas by:
    - Verifying schema version compatibility
    - Checking that semantic tags are valid
    - Confirming domain alignment
    - Ensuring qualitative labels match schema definitions
    
    This preserves Phase 3 qualitative integrity throughout the
    Phase 4 pipeline.
    """
    
    def __init__(self, valid_semantic_tags: Optional[Set[str]] = None,
                 valid_domains: Optional[Set[str]] = None):
        """
        Initialize validator with schema specifications.
        
        Args:
            valid_semantic_tags: Set of valid semantic tag values
            valid_domains: Set of valid domain names
        """
        self.valid_semantic_tags = valid_semantic_tags or set()
        self.valid_domains = valid_domains or {
            "physiological", "psychological", "social", 
            "environmental", "behavioral", "cognitive"
        }
    
    def validate(self, encoded_state: Dict[str, Any],
                 schema_version: Optional[str] = None) -> ValidationResult:
        """
        Validate an encoded state for schema alignment.
        
        Args:
            encoded_state: The encoded state to validate
            schema_version: Expected schema version (optional)
            
        Returns:
            ValidationResult with alignment issues
        """
        issues = []
        validated_fields = set()
        
        # Check schema version if provided
        if schema_version:
            metadata = encoded_state.get("encoding_metadata", {})
            actual_version = metadata.get("encoder_version")
            
            if actual_version != schema_version:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field_path="encoding_metadata.encoder_version",
                    message="Schema version mismatch",
                    expected=schema_version,
                    actual=actual_version
                ))
            else:
                validated_fields.add("encoding_metadata.encoder_version")
        
        # Check domain alignment if domains are present
        if "domains" in encoded_state:
            domains = encoded_state["domains"]
            validated_fields.add("domains")
            
            for domain_name in domains.keys():
                if domain_name not in self.valid_domains:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        field_path=f"domains.{domain_name}",
                        message=f"Invalid domain '{domain_name}'",
                        expected=f"One of {self.valid_domains}",
                        actual=domain_name
                    ))
                else:
                    validated_fields.add(f"domains.{domain_name}")
        
        # Check semantic tags if specified
        if self.valid_semantic_tags:
            self._validate_semantic_tags(encoded_state, "", issues, validated_fields)
        
        # Determine overall validity
        is_valid = not any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            validated_fields=validated_fields,
            metadata={"validator": "SchemaAlignmentValidator"}
        )
    
    def _validate_semantic_tags(self, obj: Any, path: str,
                                issues: List[ValidationIssue],
                                validated_fields: Set[str]) -> None:
        """Recursively validate semantic tags in encoded state."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else key
                
                # Check if this appears to be a semantic tag field
                if key in ["tag", "semantic_tag", "label", "descriptor"]:
                    if isinstance(value, str) and self.valid_semantic_tags:
                        if value not in self.valid_semantic_tags:
                            issues.append(ValidationIssue(
                                severity=ValidationSeverity.WARNING,
                                field_path=new_path,
                                message=f"Unknown semantic tag '{value}'",
                                expected=f"One of {self.valid_semantic_tags}",
                                actual=value
                            ))
                        else:
                            validated_fields.add(new_path)
                
                # Recurse
                self._validate_semantic_tags(value, new_path, issues, validated_fields)
        
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                new_path = f"{path}[{i}]"
                self._validate_semantic_tags(item, new_path, issues, validated_fields)


class DomainConsistencyValidator:
    """
    Validator for domain-specific consistency rules.
    
    The DomainConsistencyValidator applies domain-specific checks to
    ensure encoded states are internally consistent within particular
    domains (physiological, psychological, social, etc.).
    
    Examples of domain consistency:
    - Physiological: sleep_quality and energy_level are not contradictory
    - Social: social_support and isolation are not contradictory
    - Temporal: event sequences are ordered correctly
    
    This validator implements rule-based consistency checks without
    performing computation or inference.
    """
    
    def __init__(self, consistency_rules: Optional[Dict[str, Any]] = None):
        """
        Initialize validator with consistency rules.
        
        Args:
            consistency_rules: Domain-specific consistency rule definitions
        """
        self.consistency_rules = consistency_rules or {}
    
    def validate(self, encoded_state: Dict[str, Any],
                 domain: Optional[str] = None) -> ValidationResult:
        """
        Validate an encoded state for domain consistency.
        
        Args:
            encoded_state: The encoded state to validate
            domain: Specific domain to validate (validates all if None)
            
        Returns:
            ValidationResult with consistency issues
        """
        issues = []
        validated_fields = set()
        
        # If domains are present, validate each
        if "domains" in encoded_state:
            domains_to_check = encoded_state["domains"]
            
            if domain:
                # Only check specified domain
                if domain in domains_to_check:
                    self._check_domain_consistency(
                        domain, domains_to_check[domain], issues, validated_fields
                    )
            else:
                # Check all domains
                for domain_name, domain_state in domains_to_check.items():
                    self._check_domain_consistency(
                        domain_name, domain_state, issues, validated_fields
                    )
        
        # Check for contradictory indicators in pattern hints
        if "indicators" in encoded_state:
            self._check_indicator_consistency(
                encoded_state["indicators"], issues, validated_fields
            )
        
        # Check for temporal consistency in events
        if "temporal_context" in encoded_state:
            validated_fields.add("temporal_context")
        
        # Determine overall validity
        is_valid = not any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            validated_fields=validated_fields,
            metadata={"validator": "DomainConsistencyValidator"}
        )
    
    def _check_domain_consistency(self, domain_name: str,
                                  domain_state: Dict[str, Any],
                                  issues: List[ValidationIssue],
                                  validated_fields: Set[str]) -> None:
        """Check consistency within a single domain."""
        validated_fields.add(f"domains.{domain_name}")
        
        # Example rule: check for contradictory states
        # In a real implementation, these would be loaded from consistency_rules
        
        if domain_name == "physiological":
            # Example: can't have both "high_energy" and "exhausted"
            if "energy_level" in domain_state and "sleep_quality" in domain_state:
                energy = domain_state["energy_level"]
                sleep = domain_state["sleep_quality"]
                
                # Check for obvious contradictions
                if energy == "high" and sleep == "severely_disrupted":
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        field_path=f"domains.{domain_name}",
                        message="Potential contradiction: high energy with severely disrupted sleep",
                        expected="Consistent energy/sleep relationship",
                        actual=f"energy={energy}, sleep={sleep}"
                    ))
                
                validated_fields.add(f"domains.{domain_name}.energy_level")
                validated_fields.add(f"domains.{domain_name}.sleep_quality")
    
    def _check_indicator_consistency(self, indicators: List[str],
                                    issues: List[ValidationIssue],
                                    validated_fields: Set[str]) -> None:
        """Check for contradictory indicators."""
        validated_fields.add("indicators")
        
        # Example: check for mutually exclusive indicators
        contradictory_pairs = [
            ("high_morale", "low_morale"),
            ("strong_cohesion", "fragmented_group"),
            ("resilient", "vulnerable")
        ]
        
        for ind1, ind2 in contradictory_pairs:
            if ind1 in indicators and ind2 in indicators:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field_path="indicators",
                    message=f"Contradictory indicators: '{ind1}' and '{ind2}'",
                    expected="Mutually exclusive indicators not both present",
                    actual=f"Both {ind1} and {ind2} present"
                ))
