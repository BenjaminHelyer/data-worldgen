"""
Tests for the net worth generator module.
"""

import pytest
from dataclasses import dataclass
from pathlib import Path

from world_builder.population.net_worth_generator import NetWorth, generate_net_worth
from world_builder.population.net_worth_config import NetWorthConfig, load_config
from world_builder.distributions_config import (
    FunctionBasedDist,
    FunctionConfig,
    NoiseFunctionConfig,
    LinearParams,
    ExponentialParams,
    QuadraticParams,
    ConstantParams,
    BernoulliBasedDist,
)
from world_builder.population.character import Character


@dataclass
class MockCharacter:
    """Mock Character class for testing."""

    character_id: str
    profession: str
    age: int = 30  # Default age for testing


def test_networth_creation():
    """Test that NetWorth objects can be created with valid data."""
    net_worth = NetWorth(
        character_id="TEST123",
        liquid_currency=1000.0,
        currency_type="credits",
        owns_primary_residence=True,
        primary_residence_value=50000.0,
        owns_other_properties=True,
        other_properties_net_value=25000.0,
        owns_starships=True,
        starships_net_value=100000.0,
        owns_speeders=True,
        speeders_net_value=15000.0,
        owns_other_vehicles=True,
        other_vehicles_net_value=20000.0,
        owns_luxury_property=True,
        luxury_property_net_value=150000.0,
        owns_galactic_stock=True,
        galactic_stock_net_value=40000.0,
        owns_business=True,
        business_net_value=125000.0,
    )

    assert net_worth.character_id == "TEST123"
    assert net_worth.liquid_currency == 1000.0
    assert net_worth.currency_type == "credits"
    assert net_worth.owns_primary_residence is True
    assert net_worth.primary_residence_value == 50000.0
    assert net_worth.owns_other_properties is True
    assert net_worth.other_properties_net_value == 25000.0
    assert net_worth.owns_starships is True
    assert net_worth.starships_net_value == 100000.0
    assert net_worth.owns_speeders is True
    assert net_worth.speeders_net_value == 15000.0
    assert net_worth.owns_other_vehicles is True
    assert net_worth.other_vehicles_net_value == 20000.0
    assert net_worth.owns_luxury_property is True
    assert net_worth.luxury_property_net_value == 150000.0
    assert net_worth.owns_galactic_stock is True
    assert net_worth.galactic_stock_net_value == 40000.0
    assert net_worth.owns_business is True
    assert net_worth.business_net_value == 125000.0


def test_networth_immutability():
    """Test that NetWorth objects are immutable through properties."""
    net_worth = NetWorth(
        character_id="TEST123",
        liquid_currency=1000.0,
        currency_type="credits",
        owns_primary_residence=True,
        primary_residence_value=50000.0,
    )

    # Test that we can't set attributes directly
    with pytest.raises(AttributeError):
        net_worth.character_id = "NEW123"
    with pytest.raises(AttributeError):
        net_worth.liquid_currency = 2000.0
    with pytest.raises(AttributeError):
        net_worth.currency_type = "imperial_credits"
    with pytest.raises(AttributeError):
        net_worth.owns_primary_residence = False
    with pytest.raises(AttributeError):
        net_worth.primary_residence_value = 75000.0

    # Test that we can't add new attributes after initialization
    with pytest.raises(AttributeError):
        net_worth.new_attribute = "value"
    with pytest.raises(AttributeError):
        net_worth.owns_new_asset = True
    with pytest.raises(AttributeError):
        net_worth.new_asset_value = 100000.0


def test_networth_equality():
    """Test that NetWorth objects can be compared for equality."""
    net_worth1 = NetWorth(
        character_id="TEST123",
        liquid_currency=1000.0,
        currency_type="credits",
        owns_primary_residence=True,
        primary_residence_value=50000.0,
        owns_other_properties=True,
        other_properties_net_value=25000.0,
        owns_starships=True,
        starships_net_value=100000.0,
        owns_speeders=True,
        speeders_net_value=15000.0,
        owns_other_vehicles=True,
        other_vehicles_net_value=20000.0,
        owns_luxury_property=True,
        luxury_property_net_value=150000.0,
        owns_galactic_stock=True,
        galactic_stock_net_value=40000.0,
        owns_business=True,
        business_net_value=125000.0,
    )

    net_worth2 = NetWorth(
        character_id="TEST123",
        liquid_currency=1000.0,
        currency_type="credits",
        owns_primary_residence=True,
        primary_residence_value=50000.0,
        owns_other_properties=True,
        other_properties_net_value=25000.0,
        owns_starships=True,
        starships_net_value=100000.0,
        owns_speeders=True,
        speeders_net_value=15000.0,
        owns_other_vehicles=True,
        other_vehicles_net_value=20000.0,
        owns_luxury_property=True,
        luxury_property_net_value=150000.0,
        owns_galactic_stock=True,
        galactic_stock_net_value=40000.0,
        owns_business=True,
        business_net_value=125000.0,
    )

    net_worth3 = NetWorth(
        character_id="TEST456",
        liquid_currency=1000.0,
        currency_type="credits",
        owns_primary_residence=True,
        primary_residence_value=50000.0,
        owns_other_properties=True,
        other_properties_net_value=25000.0,
        owns_starships=True,
        starships_net_value=100000.0,
        owns_speeders=True,
        speeders_net_value=15000.0,
        owns_other_vehicles=True,
        other_vehicles_net_value=20000.0,
        owns_luxury_property=True,
        luxury_property_net_value=150000.0,
        owns_galactic_stock=True,
        galactic_stock_net_value=40000.0,
        owns_business=True,
        business_net_value=125000.0,
    )

    assert net_worth1 == net_worth2
    assert net_worth1 != net_worth3
    assert net_worth1 != "not a NetWorth object"


def test_networth_repr():
    """Test the string representation of NetWorth objects."""
    net_worth = NetWorth(
        character_id="TEST123",
        liquid_currency=1000.0,
        currency_type="credits",
        owns_primary_residence=True,
        primary_residence_value=50000.0,
        owns_other_properties=True,
        other_properties_net_value=25000.0,
        owns_starships=True,
        starships_net_value=100000.0,
        owns_speeders=True,
        speeders_net_value=15000.0,
        owns_other_vehicles=True,
        other_vehicles_net_value=20000.0,
        owns_luxury_property=True,
        luxury_property_net_value=150000.0,
        owns_galactic_stock=True,
        galactic_stock_net_value=40000.0,
        owns_business=True,
        business_net_value=125000.0,
    )

    repr_str = repr(net_worth)

    # Check that it starts with NetWorth( and ends with )
    assert repr_str.startswith("NetWorth(")
    assert repr_str.endswith(")")

    # Check that all expected attributes are present in the repr
    expected_attrs = [
        "character_id='TEST123'",
        "liquid_currency=1000.0",
        "currency_type='credits'",
        "owns_primary_residence=True",
        "primary_residence_value=50000.0",
        "owns_other_properties=True",
        "other_properties_net_value=25000.0",
        "owns_starships=True",
        "starships_net_value=100000.0",
        "owns_speeders=True",
        "speeders_net_value=15000.0",
        "owns_other_vehicles=True",
        "other_vehicles_net_value=20000.0",
        "owns_luxury_property=True",
        "luxury_property_net_value=150000.0",
        "owns_galactic_stock=True",
        "galactic_stock_net_value=40000.0",
        "owns_business=True",
        "business_net_value=125000.0",
    ]

    for attr in expected_attrs:
        assert (
            attr in repr_str
        ), f"Expected attribute {attr} not found in repr: {repr_str}"


def test_generate_net_worth_basic():
    """Test basic net worth generation with a simple function-based distribution."""
    # Create a mock character
    character = MockCharacter(character_id="TEST123", profession="farmer", age=30)

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
    assert net_worth.character_id == "TEST123"
    assert isinstance(net_worth.liquid_currency, float)
    assert net_worth.currency_type == "credits"
    # For age=30, mean should be 5*30 + 100 = 250
    assert 150 <= net_worth.liquid_currency <= 350  # mean ± 100


def test_generate_net_worth_unknown_profession():
    """Test that generating net worth for an unknown profession raises an error."""
    character = MockCharacter(character_id="TEST123", profession="unknown_profession")

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
    character = MockCharacter(character_id="TEST123", profession="farmer")

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
    character = MockCharacter(character_id="TEST123", profession="farmer")

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
        character_id="TEST123",
    )

    # Load config from file
    config_path = Path(__file__).parent / "config" / "nw_config_micro.json"
    config = load_config(config_path)

    # Generate net worth
    net_worth = generate_net_worth(character, config)

    # Verify the result
    assert net_worth.character_id == "TEST123"
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
        character = MockCharacter(character_id="TEST123", profession="Sith", age=age)
        net_worth = generate_net_worth(character, config)

        # Verify the result
        assert net_worth.character_id == "TEST123"
        assert (
            net_worth.liquid_currency == 100000
        )  # Should be exactly 100000 with no noise
        assert net_worth.currency_type == "imperial_credits"


def test_generate_net_worth_with_all_assets():
    """Test net worth generation with all asset types."""
    # Create a mock character
    character = MockCharacter(character_id="TEST123", profession="farmer", age=30)

    # Create a config with all asset types
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
        profession_has={
            "primary_residence": {
                "farmer": BernoulliBasedDist(
                    field_name="age",
                    mean_function=FunctionConfig(
                        type="linear", params=LinearParams(slope=0.02, intercept=0.1)
                    ),
                )
            },
            "other_properties": {
                "farmer": BernoulliBasedDist(
                    field_name="age",
                    mean_function=FunctionConfig(
                        type="linear", params=LinearParams(slope=0.01, intercept=0.05)
                    ),
                )
            },
            "starships": {
                "farmer": BernoulliBasedDist(
                    field_name="age",
                    mean_function=FunctionConfig(
                        type="linear", params=LinearParams(slope=0.005, intercept=0.01)
                    ),
                )
            },
            "speeders": {
                "farmer": BernoulliBasedDist(
                    field_name="age",
                    mean_function=FunctionConfig(
                        type="linear", params=LinearParams(slope=0.015, intercept=0.05)
                    ),
                )
            },
            "other_vehicles": {
                "farmer": BernoulliBasedDist(
                    field_name="age",
                    mean_function=FunctionConfig(
                        type="linear", params=LinearParams(slope=0.01, intercept=0.03)
                    ),
                )
            },
            "luxury_property": {
                "farmer": BernoulliBasedDist(
                    field_name="age",
                    mean_function=FunctionConfig(
                        type="linear", params=LinearParams(slope=0.008, intercept=0.02)
                    ),
                )
            },
            "galactic_stock": {
                "farmer": BernoulliBasedDist(
                    field_name="age",
                    mean_function=FunctionConfig(
                        type="linear", params=LinearParams(slope=0.012, intercept=0.04)
                    ),
                )
            },
            "business": {
                "farmer": BernoulliBasedDist(
                    field_name="age",
                    mean_function=FunctionConfig(
                        type="linear", params=LinearParams(slope=0.01, intercept=0.03)
                    ),
                )
            },
        },
        profession_value={
            "primary_residence": {
                "farmer": FunctionBasedDist(
                    field_name="age",
                    mean_function=FunctionConfig(
                        type="linear", params=LinearParams(slope=1000, intercept=50000)
                    ),
                    noise_function=NoiseFunctionConfig(
                        type="normal",
                        params={
                            "field_name": "age",
                            "scale_factor": FunctionConfig(
                                type="linear",
                                params=LinearParams(slope=100, intercept=5000),
                            ),
                        },
                    ),
                )
            },
            "other_properties": {
                "farmer": FunctionBasedDist(
                    field_name="age",
                    mean_function=FunctionConfig(
                        type="linear", params=LinearParams(slope=500, intercept=25000)
                    ),
                    noise_function=NoiseFunctionConfig(
                        type="normal",
                        params={
                            "field_name": "age",
                            "scale_factor": FunctionConfig(
                                type="linear",
                                params=LinearParams(slope=50, intercept=2500),
                            ),
                        },
                    ),
                )
            },
            "starships": {
                "farmer": FunctionBasedDist(
                    field_name="age",
                    mean_function=FunctionConfig(
                        type="linear", params=LinearParams(slope=2000, intercept=100000)
                    ),
                    noise_function=NoiseFunctionConfig(
                        type="normal",
                        params={
                            "field_name": "age",
                            "scale_factor": FunctionConfig(
                                type="linear",
                                params=LinearParams(slope=200, intercept=10000),
                            ),
                        },
                    ),
                )
            },
            "speeders": {
                "farmer": FunctionBasedDist(
                    field_name="age",
                    mean_function=FunctionConfig(
                        type="linear", params=LinearParams(slope=300, intercept=15000)
                    ),
                    noise_function=NoiseFunctionConfig(
                        type="normal",
                        params={
                            "field_name": "age",
                            "scale_factor": FunctionConfig(
                                type="linear",
                                params=LinearParams(slope=30, intercept=1500),
                            ),
                        },
                    ),
                )
            },
            "other_vehicles": {
                "farmer": FunctionBasedDist(
                    field_name="age",
                    mean_function=FunctionConfig(
                        type="linear", params=LinearParams(slope=400, intercept=20000)
                    ),
                    noise_function=NoiseFunctionConfig(
                        type="normal",
                        params={
                            "field_name": "age",
                            "scale_factor": FunctionConfig(
                                type="linear",
                                params=LinearParams(slope=40, intercept=2000),
                            ),
                        },
                    ),
                )
            },
            "luxury_property": {
                "farmer": FunctionBasedDist(
                    field_name="age",
                    mean_function=FunctionConfig(
                        type="linear", params=LinearParams(slope=3000, intercept=150000)
                    ),
                    noise_function=NoiseFunctionConfig(
                        type="normal",
                        params={
                            "field_name": "age",
                            "scale_factor": FunctionConfig(
                                type="linear",
                                params=LinearParams(slope=300, intercept=15000),
                            ),
                        },
                    ),
                )
            },
            "galactic_stock": {
                "farmer": FunctionBasedDist(
                    field_name="age",
                    mean_function=FunctionConfig(
                        type="linear", params=LinearParams(slope=800, intercept=40000)
                    ),
                    noise_function=NoiseFunctionConfig(
                        type="normal",
                        params={
                            "field_name": "age",
                            "scale_factor": FunctionConfig(
                                type="linear",
                                params=LinearParams(slope=80, intercept=4000),
                            ),
                        },
                    ),
                )
            },
            "business": {
                "farmer": FunctionBasedDist(
                    field_name="age",
                    mean_function=FunctionConfig(
                        type="linear", params=LinearParams(slope=2500, intercept=125000)
                    ),
                    noise_function=NoiseFunctionConfig(
                        type="normal",
                        params={
                            "field_name": "age",
                            "scale_factor": FunctionConfig(
                                type="linear",
                                params=LinearParams(slope=250, intercept=12500),
                            ),
                        },
                    ),
                )
            },
        },
        metadata={"currency": "credits"},
    )

    # Generate net worth multiple times to test probability
    results = [generate_net_worth(character, config) for _ in range(1000)]

    # For age=30, test each asset type's probability and value distribution
    asset_configs = [
        (
            "owns_primary_residence",
            "primary_residence_value",
            0.02,
            30,
            0.1,
            1000,
            50000,
        ),  # slope, age, intercept, value_slope, value_intercept
        (
            "owns_other_properties",
            "other_properties_net_value",
            0.01,
            30,
            0.05,
            500,
            25000,
        ),
        (
            "owns_starships",
            "starships_net_value",
            0.005,
            30,
            0.01,
            2000,
            100000,
        ),
        (
            "owns_speeders",
            "speeders_net_value",
            0.015,
            30,
            0.05,
            300,
            15000,
        ),
        (
            "owns_other_vehicles",
            "other_vehicles_net_value",
            0.01,
            30,
            0.03,
            400,
            20000,
        ),
        (
            "owns_luxury_property",
            "luxury_property_net_value",
            0.008,
            30,
            0.02,
            3000,
            150000,
        ),
        (
            "owns_galactic_stock",
            "galactic_stock_net_value",
            0.012,
            30,
            0.04,
            800,
            40000,
        ),
        (
            "owns_business",
            "business_net_value",
            0.01,
            30,
            0.03,
            2500,
            125000,
        ),
    ]

    for (
        owns_attr,
        value_attr,
        slope,
        age,
        intercept,
        value_slope,
        value_intercept,
    ) in asset_configs:
        # Check ownership probability
        expected_probability = slope * age + intercept
        true_count = sum(1 for r in results if getattr(r, owns_attr))
        actual_probability = true_count / len(results)
        # Allow for 5% variation from expected probability
        assert abs(actual_probability - expected_probability) < 0.05

        # Check value distribution for owned assets
        values = [getattr(r, value_attr) for r in results if getattr(r, owns_attr)]
        if values:  # Only check if we have some values
            expected_mean = value_slope * age + value_intercept
            actual_mean = sum(values) / len(values)
            # Allow for 10% variation from expected mean
            assert abs(actual_mean - expected_mean) / expected_mean < 0.1
