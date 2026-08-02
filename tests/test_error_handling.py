from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.core.exceptions import (
    DomainException,
    EntityNotFoundException,
    domain_exception_handler,
    global_exception_handler
)

test_app = FastAPI()
test_app.add_exception_handler(DomainException, domain_exception_handler)
test_app.add_exception_handler(Exception, global_exception_handler)


@test_app.get("/test-not-found")
def raise_not_found():
    raise EntityNotFoundException("Requested item was not found")


@test_app.get("/test-server-error")
def raise_unhandled():
    raise RuntimeError("Unexpected failure")


client = TestClient(test_app, raise_server_exceptions=False)


def test_entity_not_found_handler():
    response = client.get("/test-not-found")
    assert response.status_code == 404
    data = response.json()
    assert data["error"] == "EntityNotFoundException"
    assert data["detail"] == "Requested item was not found"


def test_global_exception_handler():
    response = client.get("/test-server-error")
    assert response.status_code == 500
    data = response.json()
    assert data["error"] == "InternalServerError"
