"""Test for the chain code module."""

from uuid import UUID

from world_builder.chain_code import generate_chain_code, generate_uuidv7


def test_generate_uuidv7_smoke():
    """
    Test the generate_uuidv7 function to see if it even runs.
    """
    uuidv7 = generate_uuidv7()


def test_generate_chain_code_smoke():
    """
    Test the generate_chain_code function to see if it even runs.
    """
    chain_code = generate_chain_code("human", True)


def test_generate_uuidv7_uniqueness():
    """Tests the uniqueness of generated UUIDv7 values.

    In very, very rare circumstances, this test may fail due to a collision.
    This is extremely unlikely, but it is possible.
    """
    uuids = [generate_uuidv7() for _ in range(1000)]
    uuids.sort()  # sort to ensure that equivalent UUIDs are adjacent
    assert len(uuids) == len(set(uuids))
    for uuid in uuids:
        assert isinstance(uuid, UUID)
        if uuids.index(uuid) < len(uuids) - 1:
            assert uuid < uuids[uuids.index(uuid) + 1]
        if uuids.index(uuid) > 0:
            assert uuid > uuids[uuids.index(uuid) - 1]
