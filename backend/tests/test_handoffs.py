def test_handoff_schema_is_available() -> None:
    from app.schemas.handoff import HandoffCreate

    assert HandoffCreate.model_fields["deadline_at"].is_required()
