"""Tests for crawl_scroll dedup, extract_table grouping, and tray shape."""

import pytest

from windows_computer_use_mcp.tools.portmanteau_analyze import _element_key, _rows_from_cells


def _cell(name, x, y, w=60, h=20, type="Text"):
    return {"name": name, "type": type, "bounds": {"x": x, "y": y, "width": w, "height": h}}


class TestElementKey:
    def test_named_key_ignores_bounds(self):
        a = {
            "type": "ListItem",
            "name": "Report.docx",
            "id": "7",
            "bounds": {"x": 0, "y": 100, "width": 60, "height": 20},
        }
        b = {
            "type": "ListItem",
            "name": "Report.docx",
            "id": "7",
            "bounds": {"x": 0, "y": 400, "width": 60, "height": 20},
        }
        assert _element_key(a) == _element_key(b)

    def test_different_names_differ(self):
        a = {"type": "ListItem", "name": "a.txt", "bounds": {}}
        b = {"type": "ListItem", "name": "b.txt", "bounds": {}}
        assert _element_key(a) != _element_key(b)

    def test_nameless_falls_back_to_bounds(self):
        a = {"type": "Pane", "name": "", "bounds": {"x": 0, "y": 0, "width": 10, "height": 10}}
        b = {"type": "Pane", "name": "", "bounds": {"x": 0, "y": 50, "width": 10, "height": 10}}
        assert _element_key(a) != _element_key(b)


class TestRowsFromCells:
    def _grid(self):
        cells = []
        for r in range(3):
            for c, label in enumerate(["Name", "Size", "Date"]):
                cells.append(_cell(f"{label}{r}" if r else label, x=10 + c * 70, y=10 + r * 24))
        return cells

    def test_grid_groups_into_rows(self):
        rows = _rows_from_cells(self._grid())
        assert rows == [
            ["Name", "Size", "Date"],
            ["Name1", "Size1", "Date1"],
            ["Name2", "Size2", "Date2"],
        ]

    def test_unbanded_cells_split_rows(self):
        cells = [_cell("a", 10, 10), _cell("b", 200, 100)]
        rows = _rows_from_cells(cells)
        assert rows == [["a"], ["b"]]

    def test_min_cols_drops_strays(self):
        cells = [*self._grid(), _cell("stray title", 10, 500)]
        rows = _rows_from_cells(cells, min_cols=2)
        assert ["stray title"] not in rows
        assert len(rows) == 3

    def test_empty_name_and_zero_area_skipped(self):
        cells = [_cell("", 10, 10), _cell("ok", 10, 30, w=0, h=0), _cell("kept", 10, 50)]
        assert _rows_from_cells(cells) == [["kept"]]

    def test_left_to_right_order(self):
        cells = [_cell("b", 100, 10), _cell("a", 10, 12)]
        assert _rows_from_cells(cells) == [["a", "b"]]


class TestTrayShape:
    @pytest.mark.requires_hardware
    def test_tray_list_shape(self):
        from windows_computer_use_mcp.tray_icons import list_tray_icons

        result = list_tray_icons(overflow=False)
        assert set(result) >= {"success"}
        if result.get("success"):
            assert isinstance(result["icons"], list)
            assert result["count"] == len(result["icons"])

    def test_tray_click_needs_target(self):
        from windows_computer_use_mcp.tray_icons import click_tray_icon

        result = click_tray_icon()
        assert result["success"] is False
        assert "index or text" in result["error"]


class TestWindowTrayModels:
    def test_tray_ops_accepted(self):
        from windows_computer_use_mcp.tools.models import WindowOperationRequest

        assert WindowOperationRequest(operation="tray_list").operation == "tray_list"
        req = WindowOperationRequest(operation="tray_click", tray_text="volume", tray_overflow=True)
        assert req.tray_text == "volume"
        assert req.tray_overflow is True
