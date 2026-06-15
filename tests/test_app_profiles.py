"""Tests for app profiles and region masks (T2.4)."""

from windows_computer_use_mcp.app_profiles import get_profile, get_profile_region, list_profiles, region_dict_for_app


def test_vroid_profile_has_stable_region():
    p = get_profile("vroidstudio")
    assert p is not None
    assert p.stable_region is not None
    assert p.stable_region.label == "editor_canvas"


def test_get_profile_region_tuple():
    region = get_profile_region("vroidstudio")
    assert region == (280, 120, 1640, 980)


def test_list_profiles_includes_region():
    profiles = list_profiles()
    vroid = next(p for p in profiles if p["app_id"] == "vroidstudio")
    assert "stable_region" in vroid
    assert vroid["stable_region"]["region_left"] == 280


def test_region_dict_for_app():
    d = region_dict_for_app("vroidstudio")
    assert d is not None
    assert d["region_bottom"] == 980
