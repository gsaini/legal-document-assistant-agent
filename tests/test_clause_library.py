"""Tests for the clause library."""

import pytest

from src.data.clause_library import (
    CLAUSE_LIBRARY,
    get_clause,
    get_all_clauses,
    list_clause_types,
)


class TestClauseLibrary:
    """Test clause library functionality."""
    
    def test_clause_library_not_empty(self):
        """Test that clause library has clauses."""
        assert len(CLAUSE_LIBRARY) > 0
    
    def test_list_clause_types(self):
        """Test listing clause types."""
        types = list_clause_types()
        assert isinstance(types, list)
        assert len(types) > 0
        assert "indemnification" in types
        assert "confidentiality" in types
    
    def test_get_clause_existing(self):
        """Test getting an existing clause."""
        clause = get_clause("indemnification")
        assert clause is not None
        assert isinstance(clause, str)
        assert len(clause) > 0
        assert "indemnify" in clause.lower()
    
    def test_get_clause_nonexistent(self):
        """Test getting a non-existent clause."""
        clause = get_clause("nonexistent_clause_type")
        assert clause is None
    
    def test_get_clause_case_insensitive(self):
        """Test that get_clause is case-insensitive."""
        clause_lower = get_clause("indemnification")
        clause_upper = get_clause("INDEMNIFICATION")
        assert clause_lower == clause_upper
    
    def test_get_all_clauses(self):
        """Test getting all clauses."""
        clauses = get_all_clauses()
        assert isinstance(clauses, dict)
        assert len(clauses) == len(CLAUSE_LIBRARY)
        
        # Ensure it's a copy
        clauses["test"] = "test"
        assert "test" not in CLAUSE_LIBRARY
    
    def test_standard_clauses_content(self):
        """Test that standard clauses contain expected content."""
        # Indemnification
        indemnification = get_clause("indemnification")
        assert "hold harmless" in indemnification.lower()
        
        # Limitation of liability
        liability = get_clause("limitation_of_liability")
        assert "consequential damages" in liability.lower()
        
        # Confidentiality
        confidentiality = get_clause("confidentiality")
        assert "confidential information" in confidentiality.lower()
        
        # Termination
        termination = get_clause("termination")
        assert "terminate" in termination.lower()
        
        # Data protection
        data_protection = get_clause("data_protection")
        assert "personal data" in data_protection.lower()
        
        # Dispute resolution
        dispute = get_clause("dispute_resolution")
        assert "arbitration" in dispute.lower()
