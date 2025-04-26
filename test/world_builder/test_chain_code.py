"""Test for the chain code module."""

from world_builder.chain_code import generate_chain_code, generate_uuidv7

def test_generate_uuidv7_smoke():
    """Test the generate_uuidv7 function to see if it even runs."""
    uuidv7 = generate_uuidv7()

def test_generate_chain_code_smoke():
    """
    Test the generate_chain_code function to see if it even runs.
    """
    chain_code = generate_chain_code("human", True)