import pytest

from app.core.exceptions import CareLoopError
from app.services.state_machine import transition


def test_valid_transition() -> None:
    assert transition("READY", "IN_PROGRESS") == "IN_PROGRESS"


def test_invalid_transition_is_rejected() -> None:
    with pytest.raises(CareLoopError) as error:
        transition("PENDING", "VERIFIED_COMPLETE")
    assert error.value.code == "INVALID_STATE_TRANSITION"
