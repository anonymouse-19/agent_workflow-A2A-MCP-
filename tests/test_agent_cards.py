"""Tests for A2A agent card endpoints."""

import os
import json
import pytest


def _load_card(agent_name: str) -> dict:
    card_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "agents", agent_name, "agent_card.json",
    )
    with open(card_path) as f:
        return json.load(f)


AGENTS = ["reader", "analyzer", "summarizer"]


@pytest.mark.parametrize("agent_name", AGENTS)
def test_card_exists(agent_name):
    card = _load_card(agent_name)
    assert "name" in card
    assert "url" in card
    assert "capabilities" in card


@pytest.mark.parametrize("agent_name", AGENTS)
def test_card_has_required_fields(agent_name):
    card = _load_card(agent_name)
    assert isinstance(card["name"], str) and len(card["name"]) > 0
    assert isinstance(card["url"], str) and card["url"].startswith("http")
    assert isinstance(card["capabilities"], list) and len(card["capabilities"]) > 0
    assert "inputModes" in card
    assert "outputModes" in card


@pytest.mark.parametrize("agent_name", AGENTS)
def test_card_capabilities_structure(agent_name):
    card = _load_card(agent_name)
    for cap in card["capabilities"]:
        assert isinstance(cap, dict)
        assert "name" in cap


def test_reader_capabilities():
    card = _load_card("reader")
    cap_names = [c["name"] for c in card["capabilities"]]
    assert "file_reading" in cap_names or "pdf_reading" in cap_names


def test_analyzer_capabilities():
    card = _load_card("analyzer")
    cap_names = [c["name"] for c in card["capabilities"]]
    assert "question_extraction" in cap_names or "data_analysis" in cap_names


def test_summarizer_capabilities():
    card = _load_card("summarizer")
    cap_names = [c["name"] for c in card["capabilities"]]
    assert "text_summarization" in cap_names or "clinical_brief" in cap_names
