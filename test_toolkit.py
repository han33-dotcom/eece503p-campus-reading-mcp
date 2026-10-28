"""Domain and real subprocess MCP integration tests; no paid model required."""
import asyncio
import json
import sqlite3

import pytest

import library
from agent import EXPECTED_TOOLS, connect, run_demo


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    db = tmp_path / "reading.sqlite3"
    monkeypatch.setenv("LIBRARY_DB", str(db))
    return db


def test_data_lookup_is_read_only(isolated_database):
    result = library.search_catalog("ARTIFICIAL intelligence")
    assert [b.book_id for b in result.books] == ["B001", "B004"]
    assert not isolated_database.exists()


@pytest.mark.parametrize("query", ["", "   ", "x" * 121])
def test_data_invalid_query(query):
    with pytest.raises(library.LibraryError, match="INVALID_QUERY"):
        library.search_catalog(query)


@pytest.mark.parametrize("limit", [0, 11, True, 1.5])
def test_data_invalid_limit(limit):
    with pytest.raises(library.LibraryError, match="INVALID_LIMIT"):
        library.search_catalog("agents", limit)


def test_data_no_match():
    assert library.search_catalog("quantum gardening").count == 0


def test_data_catalogue_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(library, "ROOT", tmp_path)
    with pytest.raises(library.LibraryError, match="CATALOG_UNAVAILABLE"):
        library.search_catalog("agents")


def test_action_persists_and_is_idempotent(isolated_database):
    first = library.save_reading_item("B003", "course")
    second = library.save_reading_item("B003", "course")
    assert first.status == "saved"
    assert second.status == "already_saved"
    assert first.saved_at == second.saved_at
    with sqlite3.connect(isolated_database) as conn:
        assert conn.execute("SELECT book_id FROM reading_items").fetchall() == [("B003",)]


def test_action_unknown_book_has_no_write(isolated_database):
    with pytest.raises(library.LibraryError, match="UNKNOWN_BOOK"):
        library.save_reading_item("B999")
    assert not isolated_database.exists()


def test_action_invalid_list():
    with pytest.raises(library.LibraryError, match="INVALID_LIST"):
        library.save_reading_item("B001", "../outside")


def test_action_storage_failure(monkeypatch, tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("not a directory")
    monkeypatch.setenv("LIBRARY_DB", str(blocker / "reading.sqlite3"))
    with pytest.raises(library.LibraryError, match="STORAGE_UNAVAILABLE"):
        library.save_reading_item("B001")


def test_orchestration_calls_data_then_action(monkeypatch):
    calls = []
    search, save = library.search_catalog, library.save_reading_item
    def traced_search(*args, **kwargs):
        calls.append("search_catalog")
        return search(*args, **kwargs)
    def traced_save(*args, **kwargs):
        calls.append("save_reading_item")
        return save(*args, **kwargs)
    monkeypatch.setattr(library, "search_catalog", traced_search)
    monkeypatch.setattr(library, "save_reading_item", traced_save)
    result = library.plan_reading("agents")
    assert calls == ["search_catalog", "save_reading_item"]
    assert result.matches == 2 and result.saved.book.book_id == "B001"


def test_orchestration_no_match_has_no_write(isolated_database):
    with pytest.raises(library.LibraryError, match="NO_MATCH"):
        library.plan_reading("quantum gardening")
    assert not isolated_database.exists()


def test_stdio_discovery_schemas_results_errors_and_persistence(isolated_database):
    async def check():
        async with connect() as server:
            tools = await server.list_tools()
            assert {t.name for t in tools} == EXPECTED_TOOLS
            assert all(t.description and t.input_schema and t.output_schema for t in tools)
            result = await server.call_tool("search_catalog", {"query": "python"})
            assert not result.is_error
            assert result.structured_content["books"][0]["book_id"] == "B003"
            assert not isolated_database.exists()
            saved = await server.call_tool("save_reading_item", {"book_id": "B003"})
            assert saved.structured_content["status"] == "saved"
            for name, args, code in [
                ("search_catalog", {"query": " "}, "INVALID_QUERY"),
                ("save_reading_item", {"book_id": "B999"}, "UNKNOWN_BOOK"),
                ("plan_reading", {"query": "quantum gardening"}, "NO_MATCH"),
            ]:
                failed = await server.call_tool(name, args)
                assert failed.is_error and code in str(failed.content)
            invalid = await server.call_tool("search_catalog", {"query": "python", "limit": 0})
            assert invalid.is_error
            plan = await server.call_tool("plan_reading", {"query": "agents"})
            assert plan.structured_content["steps"] == ["search_catalog", "save_reading_item"]
        # New server process, same database: persistence survives server restart.
        async with connect() as restarted:
            duplicate = await restarted.call_tool("save_reading_item", {"book_id": "B003"})
            assert duplicate.structured_content["status"] == "already_saved"
        with sqlite3.connect(isolated_database) as conn:
            assert conn.execute("SELECT COUNT(*) FROM reading_items").fetchone()[0] == 2
    asyncio.run(check())


def test_agents_sdk_runner_round_trip():
    records = asyncio.run(run_demo(offline=True))
    assert [r["calls"][0]["name"] for r in records] == [
        "search_catalog", "save_reading_item", "plan_reading", "plan_reading"]
    assert "NO_MATCH" in records[-1]["final_output"]

