"""Tests for MCP server tools (unit tests, no server required)."""

import os
import sys
import pytest

# Ensure project root on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server.server import (
    read_text,
    extract_questions,
    summarize_text,
    extract_keywords,
    analyze_tabular_data,
)


SAMPLE_TEXT = """Patient shows elevated blood pressure of 150/95 mmHg.
What is the recommended treatment for hypertension?
Blood glucose level is 180 mg/dL, indicating hyperglycemia.
Is the patient at risk for diabetic complications?
Heart rate is stable at 72 bpm. Weight: 85 kg. Temperature: 37.2°C."""


def test_read_text_file_not_found():
    result = read_text("nonexistent_file_123.txt")
    assert "error" in result


def test_read_text_success():
    sample_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_data", "sample.txt")
    if os.path.exists(sample_path):
        result = read_text(sample_path)
        assert "content" in result
        assert len(result["content"]) > 0


def test_extract_questions():
    result = extract_questions(SAMPLE_TEXT)
    assert "questions" in result
    questions = result["questions"]
    assert len(questions) >= 2
    assert any("hypertension" in q.lower() or "treatment" in q.lower() for q in questions)


def test_summarize_text():
    result = summarize_text(SAMPLE_TEXT, num_sentences=2)
    assert "summary" in result
    assert result["sentences_selected"] <= 2
    assert len(result["summary"]) > 0


def test_extract_keywords():
    result = extract_keywords(SAMPLE_TEXT, top_n=5)
    assert "keywords" in result
    assert len(result["keywords"]) <= 5


def test_analyze_tabular_data():
    headers = ["Name", "Age", "BP_Systolic", "BP_Diastolic"]
    rows = [["Alice", 45, 130, 85], ["Bob", 60, 155, 95], ["Charlie", 38, 120, 80]]
    result = analyze_tabular_data(headers, rows)
    assert "column_count" in result
    assert "row_count" in result
    assert result["row_count"] == 3
    assert "column_stats" in result


def test_analyze_tabular_data_with_anomalies():
    headers = ["Name", "Value"]
    rows = [["A", 10], ["B", 12], ["C", 11], ["D", 100], ["E", 9]]
    result = analyze_tabular_data(headers, rows)
    assert "column_stats" in result
    # Check that the Value column stats are computed
    value_stats = result["column_stats"].get("Value", {})
    assert value_stats.get("type") == "numeric"
    assert value_stats.get("max") == 100.0
