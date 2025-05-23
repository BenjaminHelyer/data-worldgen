"""
Tests for the net worth generator module.
"""

import pytest
from dataclasses import dataclass
from pathlib import Path

from world_builder.net_worth_generator import NetWorth, generate_net_worth
from world_builder.net_worth_config import NetWorthConfig, load_config
from world_builder.distributions_config import (
    FunctionBasedDist,
    FunctionConfig,
    NoiseFunctionConfig,
    LinearParams,
    ExponentialParams,
    QuadraticParams,
    ConstantParams,
)
from world_builder.character import Character


@dataclass
class MockCharacter:
    """Mock Character class for testing."""

    chain_code: str
    profession: str
    age: int = 30  # Default age for testing


def test_networth_creation():
    """Test that NetWorth objects can be created with valid data."""
    net_worth = NetWorth(
        chain_code="TEST123", liquid_currency=1000.0, currency_type="credits"
    )

    assert net_worth.chain_code == "TEST123"
    assert net_worth.liquid_currency == 1000.0
    assert net_worth.currency_type == "credits"


def test_networth_immutability():
    """Test that NetWorth objects are immutable through properties."""
    net_worth = NetWorth(
        chain_code="TEST123", liquid_currency=1000.0, currency_type="credits"
    )

    # Test that we can't set attributes directly
    with pytest.raises(AttributeError):
        net_worth.chain_code = "NEW123"
    with pytest.raises(AttributeError):
        net_worth.liquid_currency = 2000.0
    with pytest.raises(AttributeError):
        net_worth.currency_type = "imperial_credits"


def test_networth_equality():
    """Test that NetWorth objects can be compared for equality."""
    net_worth1 = NetWorth(
        chain_code="TEST123", liquid_currency=1000.0, currency_type="credits"
    )

    net_worth2 = NetWorth(
        chain_code="TEST123", liquid_currency=1000.0, currency_type="credits"
    )

    net_worth3 = NetWorth(
        chain_code="TEST456", liquid_currency=1000.0, currency_type="credits"
    )

    assert net_worth1 == net_worth2
    assert net_worth1 != net_worth3
    assert net_worth1 != "not a NetWorth object"


def test_networth_repr():
    """Test the string representation of NetWorth objects."""
    net_worth = NetWorth(
        chain_code="TEST123", liquid_currency=1000.0, currency_type="credits"
    )

    expected_repr = "NetWorth(chain_code='TEST123', liquid_currency=1000.0, currency_type='credits')"
    assert repr(net_worth) == expected_repr


def test_generate_net_worth_basic():
    """Test basic net worth generation with a simple function-based distribution."""
    # Create a mock character
    character = MockCharacter(chain_code="TEST123", profession="farmer", age=30)

    # Create a simple config with one profession
    config = NetWorthConfig(
        profession_liquid_currency={
            "farmer": FunctionBasedDist(
                field_name="age",
                mean_function=FunctionConfig(
                    type="linear", params=LinearParams(slope=5, intercept=100)
                ),
                noise_function=NoiseFunctionConfig(
                    type="normal",
                    params={
                        "field_name": "age",
                        "scale_factor": FunctionConfig(
                            type="linear", params=LinearParams(slope=0.1, intercept=0)
                        ),
                    },
                ),
            )
        },
        metadata={"currency": "credits"},
    )

    # Generate net worth
    net_worth = generate_net_worth(character, config)

    # Verify the result
    assert net_worth.chain_code == "TEST123"
    assert isinstance(net_worth.liquid_currency, float)
    assert net_worth.currency_type == "credits"
    # For age=30, mean should be 5*30 + 100 = 250
    assert 150 <= net_worth.liquid_currency <= 350  # mean ± 100


def test_generate_net_worth_unknown_profession():
    """Test that generating net worth for an unknown profession raises an error."""
    character = MockCharacter(chain_code="TEST123", profession="unknown_profession")

    config = NetWorthConfig(
        profession_liquid_currency={
            "farmer": FunctionBasedDist(
                field_name="age",
                mean_function=FunctionConfig(
                    type="linear", params=LinearParams(slope=5, intercept=100)
                ),
                noise_function=NoiseFunctionConfig(
                    type="normal",
                    params={
                        "field_name": "age",
                        "scale_factor": FunctionConfig(
                            type="linear", params=LinearParams(slope=0.1, intercept=0)
                        ),
                    },
                ),
            )
        },
        metadata={"currency": "credits"},
    )

    with pytest.raises(
        ValueError,
        match="Character profession 'unknown_profession' not found in net worth config",
    ):
        generate_net_worth(character, config)


def test_generate_net_worth_default_currency():
    """Test that net worth generation uses default currency when not specified in config."""
    character = MockCharacter(chain_code="TEST123", profession="farmer")

    config = NetWorthConfig(
        profession_liquid_currency={
            "farmer": FunctionBasedDist(
                field_name="age",
                mean_function=FunctionConfig(
                    type="linear", params=LinearParams(slope=5, intercept=100)
                ),
                noise_function=NoiseFunctionConfig(
                    type="normal",
                    params={
                        "field_name": "age",
                        "scale_factor": FunctionConfig(
                            type="linear", params=LinearParams(slope=0.1, intercept=0)
                        ),
                    },
                ),
            )
        },
        metadata={},  # No currency specified
    )

    net_worth = generate_net_worth(character, config)
    assert net_worth.currency_type == "credits"  # Should use default


def test_generate_net_worth_custom_currency():
    """Test that net worth generation uses custom currency from config."""
    character = MockCharacter(chain_code="TEST123", profession="farmer")

    config = NetWorthConfig(
        profession_liquid_currency={
            "farmer": FunctionBasedDist(
                field_name="age",
                mean_function=FunctionConfig(
                    type="linear", params=LinearParams(slope=5, intercept=100)
                ),
                noise_function=NoiseFunctionConfig(
                    type="normal",
                    params={
                        "field_name": "age",
                        "scale_factor": FunctionConfig(
                            type="linear", params=LinearParams(slope=0.1, intercept=0)
                        ),
                    },
                ),
            )
        },
        metadata={"currency": "imperial_credits"},
    )

    net_worth = generate_net_worth(character, config)
    assert net_worth.currency_type == "imperial_credits"


def test_generate_net_worth_from_file():
    """Test the full net worth generation process using a real Character and config file."""
    # Create a real character
    character = Character(
        species="human",
        age=30,
        profession="farmer",
        chain_code="TEST123",
    )

    # Load config from file
    config_path = Path(__file__).parent / "config" / "nw_config_micro.json"
    config = load_config(config_path)

    # Generate net worth
    net_worth = generate_net_worth(character, config)

    # Verify the result
    assert net_worth.chain_code == "TEST123"
    assert isinstance(net_worth.liquid_currency, float)
    assert net_worth.currency_type == "credits"


def test_generate_net_worth_constant():
    """Test net worth generation with a constant function."""
    # Test with different ages to ensure net worth remains constant
    ages = [20, 30, 40, 50]

    config = NetWorthConfig(
        profession_liquid_currency={
            "Sith": FunctionBasedDist(
                field_name="age",
                mean_function=FunctionConfig(
                    type="constant", params=ConstantParams(value=100000)
                ),
                noise_function=NoiseFunctionConfig(
                    type="normal",
                    params={
                        "field_name": "age",
                        "scale_factor": FunctionConfig(
                            type="constant", params=ConstantParams(value=0)
                        ),
                    },
                ),
            )
        },
        metadata={"currency": "imperial_credits"},
    )

    # Generate net worth for each age
    for age in ages:
        character = MockCharacter(chain_code="TEST123", profession="Sith", age=age)
        net_worth = generate_net_worth(character, config)

        # Verify the result
        assert net_worth.chain_code == "TEST123"
        assert (
            net_worth.liquid_currency == 100000
        )  # Should be exactly 100000 with no noise
        assert net_worth.currency_type == "imperial_credits"
