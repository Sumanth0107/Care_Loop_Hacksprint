def test_exception_schema_is_available() -> None:
    from app.schemas.exception import ExceptionPatch

    assert "status" in ExceptionPatch.model_fields
