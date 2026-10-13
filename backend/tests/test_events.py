def test_event_module_is_available() -> None:
    from app.services.event_service import process_event

    assert callable(process_event)
