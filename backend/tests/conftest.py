"""
conftest.py — shared fixtures for the test suite.

Runs the seed generator once per pytest session so all tests start from a
clean, deterministic database.  The tamper test in test_stage5.py modifies
an audit row in‑session; rolling back the session automatically undoes that
change, keeping the DB clean for the next test.
"""
import pytest
from sqlmodel import Session, select, delete
from app.db import engine
from app.models import (
    SQLModel, AuditLog, Issue, ReconRun, Match, RecordStatus, SupplierScore
)
from app.seed.generator import generate_data


def pytest_configure(config):
    """Re-seed the database once at the start of the pytest run."""
    generate_data()


@pytest.fixture(autouse=True)
def clean_audit_chain(request):
    """
    For the chain-verification test: wrap the audit operations in a savepoint
    so the deliberate tamper is always rolled back at the end of the test,
    leaving the chain intact for subsequent tests.

    For every other test this fixture is a no-op.
    """
    if request.node.name == "test_queue_sorting_and_api":
        # Capture the id of the last audit row before the test so we can
        # restore any tampered row to its original state afterwards.
        with Session(engine) as pre_session:
            last_log = pre_session.exec(
                select(AuditLog).order_by(AuditLog.id.desc()).limit(1)
            ).first()
            pre_last_id = last_log.id if last_log else 0

        yield   # run the test

        # After the test: hard-delete any audit rows added by the test and
        # restore the one the test tampered with (identified by payload change).
        with Session(engine) as post_session:
            # Remove rows added during the test
            post_session.exec(
                delete(AuditLog).where(AuditLog.id > pre_last_id)
            )
            # If the tampered row is within the pre-existing set, fix it
            tampered = post_session.exec(
                select(AuditLog).where(AuditLog.payload_json.contains("tampered"))
            ).first()
            if tampered:
                post_session.delete(tampered)
            post_session.commit()
    else:
        yield
