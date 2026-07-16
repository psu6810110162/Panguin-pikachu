from core.pause_state import PauseState


def test_fresh_state_is_not_paused():
    state = PauseState()
    assert state.is_paused is False
    assert state.reasons() == frozenset()


def test_pause_fires_on_pause_only_on_zero_to_one_transition():
    calls = []
    state = PauseState(on_pause=lambda: calls.append("pause"))

    assert state.pause("manual") is True
    assert state.is_paused is True
    assert calls == ["pause"]

    # Adding a second reason while already paused must not re-fire on_pause.
    assert state.pause("help") is False
    assert calls == ["pause"]

    # Re-adding an already-active reason is idempotent.
    assert state.pause("manual") is False
    assert calls == ["pause"]


def test_resume_fires_on_resume_only_once_every_reason_cleared():
    calls = []
    state = PauseState(on_resume=lambda: calls.append("resume"))
    state.pause("manual")
    state.pause("help")

    # Still paused: "manual" remains active.
    assert state.resume("help") is False
    assert state.is_paused is True
    assert calls == []

    assert state.resume("manual") is True
    assert state.is_paused is False
    assert calls == ["resume"]


def test_resume_unknown_reason_is_a_noop():
    calls = []
    state = PauseState(on_resume=lambda: calls.append("resume"))
    state.pause("manual")

    assert state.resume("nonexistent") is False
    assert state.is_paused is True
    assert calls == []


def test_help_only_pause_resumes_automatically_without_manual():
    pause_calls = []
    resume_calls = []
    state = PauseState(
        on_pause=lambda: pause_calls.append(1),
        on_resume=lambda: resume_calls.append(1),
    )

    state.pause("help")
    assert state.is_paused is True
    assert pause_calls == [1]

    state.resume("help")
    assert state.is_paused is False
    assert resume_calls == [1]


def test_clear_drops_all_reasons_without_firing_on_resume():
    resume_calls = []
    state = PauseState(on_resume=lambda: resume_calls.append(1))
    state.pause("manual")
    state.pause("help")

    state.clear()

    assert state.is_paused is False
    assert state.reasons() == frozenset()
    assert resume_calls == []


def test_has_reason():
    state = PauseState()
    assert state.has_reason("manual") is False
    state.pause("manual")
    assert state.has_reason("manual") is True
    assert state.has_reason("help") is False
