from game.penguin import Penguin


def test_penguin_maps_gameplay_actions_to_generated_frames():
    penguin = Penguin()
    assert penguin.get_generated_frame_name() == "idle"

    penguin.action = "Jump"
    assert penguin.get_generated_frame_name() == "jump"
    penguin.action = "Hit"
    assert penguin.get_generated_frame_name() == "hit"
    penguin.action = "Fall"
    assert penguin.get_generated_frame_name() == "fall"
    penguin.action = "Victory"
    assert penguin.get_generated_frame_name() == "victory"


def test_penguin_run_direction_uses_explicit_left_and_right_cells():
    penguin = Penguin()
    penguin.action = "Run"
    penguin.facing_left = True
    assert penguin.get_generated_frame_name() == "run_left"
    penguin.facing_left = False
    assert penguin.get_generated_frame_name() == "run_right"
