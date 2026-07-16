"""Regression tests for the pure How to Play content model."""

from pathlib import Path

from core.how_to_play import HowToPlayPage, HowToPlayPager, load_how_to_play


def test_tutorial_has_required_pages_and_all_junction_zones() -> None:
    model = load_how_to_play()
    page_ids = {page.id for page in model.pages}

    assert {
        "goal_controls",
        "meters_hearts",
        "visual_scaffolding",
        "evidence_items",
        "carbon_baron",
        "win_loss",
        "scores_dag",
    } <= page_ids

    junction_pages = [page for page in model.pages if page.id.startswith("junctions_")]
    assert len(junction_pages) == 5
    assert sum(len(page.rows) for page in junction_pages) == 10
    assert all(
        "Heat" in row.body and "Anger" in row.body for page in junction_pages for row in page.rows
    )


def test_tutorial_derives_boss_and_scoring_rows() -> None:
    model = load_how_to_play()
    pages = {page.id: page for page in model.pages}

    boss_rows = pages["carbon_baron"].rows
    assert len(boss_rows) == 3
    assert "Albedo Data" in boss_rows[0].body
    assert "Methane Core" in boss_rows[1].body
    assert "Eco Seed" in boss_rows[2].body

    scoring_rows = pages["scores_dag"].rows
    assert any("13" in row.detail for row in scoring_rows)


def test_tutorial_mentions_all_four_visual_scaffolding_features() -> None:
    model = load_how_to_play()
    page = next(page for page in model.pages if page.id == "visual_scaffolding")
    titles = {row.title for row in page.rows}

    assert titles == {
        "Neon Pivot Tiles",
        "Physical Roadblocks",
        "Flashing Chevron Signs",
        "Holographic Guide Line",
    }


def test_pager_clamps_at_each_boundary() -> None:
    pages = (
        HowToPlayPage(id="one", title="One", body=""),
        HowToPlayPage(id="two", title="Two", body=""),
    )
    pager = HowToPlayPager(pages)

    assert pager.indicator == "1 / 2"
    assert not pager.previous_page()
    assert pager.next_page()
    assert pager.current.id == "two"
    assert pager.indicator == "2 / 2"
    assert not pager.next_page()
    assert pager.previous_page()
    assert pager.current.id == "one"


def test_how_to_play_core_module_has_no_kivy_dependency() -> None:
    import core.how_to_play as how_to_play

    source = Path(how_to_play.__file__).read_text(encoding="utf-8")
    assert "import kivy" not in source
