"""
Tests for the net worth generator module.
"""

import pytest
from dataclasses import dataclass
from pathlib import Path

from world_builder.net_worth_generator import (
    NetWorth,
    generate_net_worth,
    evaluate_function,
)
from world_builder.net_worth_config import NetWorthConfig, load_config
from world_builder.distributions_config import (
    FunctionBasedDist,
    FunctionConfig,
    NoiseFunctionConfig,
    LinearParams,
    ExponentialParams,
    QuadraticParams,
    ConstantParams,
    BernoulliBasedDist,
    MultiLinearParams,
)
from world_builder.character import Character


@dataclass
class MockCharacter:
    """Mock Character class for testing."""

    chain_code: str
    profession: str
    age: int = 30  # Default age for testing
    liquid_currency: float = 100000  # Add liquid_currency for multi-variable tests


CONFIG_DIR = Path(__file__).resolve().parent / "config"


def test_networth_creation():
    """Test creating a NetWorth instance."""
    net_worth = NetWorth(
        chain_code="TEST123",
        liquid_currency=1000.0,
        currency_type="credits",
        owns_primary_residence=True,
        primary_residence_value=50000.0,
    )

    assert net_worth.chain_code == "TEST123"
    assert net_worth.liquid_currency == 1000.0
    assert net_worth.currency_type == "credits"
    assert net_worth.owns_primary_residence is True
    assert net_worth.primary_residence_value == 50000.0


def test_networth_immutability():
    """Test that NetWorth instances are immutable after creation."""
    net_worth = NetWorth(
        chain_code="TEST123", liquid_currency=1000.0, currency_type="credits"
    )

    # Should not be able to modify attributes after creation
    with pytest.raises(AttributeError):
        net_worth.liquid_currency = 2000.0

    with pytest.raises(AttributeError):
        net_worth.new_attribute = "test"


def test_networth_equality():
    """Test NetWorth equality comparison."""
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
    assert net_worth1 != "not a networth object"


def test_networth_repr():
    """Test NetWorth string representation."""
    net_worth = NetWorth(
        chain_code="TEST123",
        liquid_currency=1000.0,
        currency_type="credits",
        owns_primary_residence=True,
    )

    repr_str = repr(net_worth)
    assert "TEST123" in repr_str
    assert "1000.0" in repr_str
    assert "credits" in repr_str
    assert "True" in repr_str


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
    """Test net worth generation using a config file."""
    character = MockCharacter(chain_code="TEST123", profession="Jedi", age=30)

    # Load from actual config file
    config_path = CONFIG_DIR / "nw_config_micro_jedi.json"
    config = load_config(config_path)

    net_worth = generate_net_worth(character, config)
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


def test_generate_net_worth_with_all_assets():
    """Test net worth generation with all asset types."""
    # Create a mock character
    character = MockCharacter(chain_code="TEST123", profession="farmer", age=30)

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


def test_multi_linear_function_evaluation():
    """Test evaluation of multi-linear functions."""
    # Create a multi-linear function: 2*age + 0.000001*liquid_currency + 0.1
    func_config = FunctionConfig(
        type="multi_linear",
        params=MultiLinearParams(
            fields=["age", "liquid_currency"],
            coefficients={"age": 0.02, "liquid_currency": 0.000001},
            intercept=0.1,
        ),
    )

    # Test with specific values
    field_values = {"age": 30, "liquid_currency": 100000}
    result = evaluate_function(func_config, field_values)
    expected = 0.02 * 30 + 0.000001 * 100000 + 0.1  # 0.6 + 0.1 + 0.1 = 0.8
    assert abs(result - expected) < 1e-10, f"Expected {expected}, got {result}"

    # Test with different values
    field_values = {"age": 50, "liquid_currency": 500000}
    result = evaluate_function(func_config, field_values)
    expected = 0.02 * 50 + 0.000001 * 500000 + 0.1  # 1.0 + 0.5 + 0.1 = 1.6
    assert abs(result - expected) < 1e-10, f"Expected {expected}, got {result}"


def test_multi_linear_function_missing_field():
    """Test that multi-linear functions raise error when required field is missing."""
    func_config = FunctionConfig(
        type="multi_linear",
        params=MultiLinearParams(
            fields=["age", "liquid_currency"],
            coefficients={"age": 0.02, "liquid_currency": 0.000001},
            intercept=0.1,
        ),
    )

    # Missing liquid_currency field
    field_values = {"age": 30}
    with pytest.raises(ValueError, match="Missing required field 'liquid_currency'"):
        evaluate_function(func_config, field_values)


def test_multi_linear_function_wrong_input_type():
    """Test that multi-linear functions raise error with wrong input type."""
    func_config = FunctionConfig(
        type="multi_linear",
        params=MultiLinearParams(
            fields=["age", "liquid_currency"],
            coefficients={"age": 0.02, "liquid_currency": 0.000001},
            intercept=0.1,
        ),
    )

    # Passing single value instead of dictionary
    with pytest.raises(
        ValueError, match="Multi-linear function requires a dictionary of field values"
    ):
        evaluate_function(func_config, 30.0)


def test_generate_net_worth_with_multi_variable_assets():
    """Test net worth generation with multi-variable asset ownership."""
    # Create a character with both age and liquid_currency
    character = MockCharacter(
        chain_code="TEST123",
        profession="bounty hunter",
        age=30,
        liquid_currency=100000,  # This will be overridden by the actual generated value
    )

    # Create config with multi-linear asset ownership
    config = NetWorthConfig(
        profession_liquid_currency={
            "bounty hunter": FunctionBasedDist(
                field_name="age",
                mean_function=FunctionConfig(
                    type="linear", params=LinearParams(slope=100, intercept=1000)
                ),
                noise_function=NoiseFunctionConfig(
                    type="normal",
                    params={
                        "field_name": "age",
                        "scale_factor": FunctionConfig(
                            type="constant", params=ConstantParams(value=100)
                        ),
                    },
                ),
            )
        },
        profession_has={
            "primary_residence": {
                "bounty hunter": BernoulliBasedDist(
                    field_name="age",
                    mean_function=FunctionConfig(
                        type="multi_linear",
                        params=MultiLinearParams(
                            fields=["age", "liquid_currency"],
                            coefficients={"age": 0.02, "liquid_currency": 0.000001},
                            intercept=0.1,
                        ),
                    ),
                )
            }
        },
        profession_value={
            "primary_residence": {
                "bounty hunter": FunctionBasedDist(
                    field_name="age",
                    mean_function=FunctionConfig(
                        type="linear", params=LinearParams(slope=1000, intercept=50000)
                    ),
                    noise_function=NoiseFunctionConfig(
                        type="normal",
                        params={
                            "field_name": "age",
                            "scale_factor": FunctionConfig(
                                type="constant", params=ConstantParams(value=5000)
                            ),
                        },
                    ),
                )
            }
        },
        metadata={"currency": "credits"},
    )

    # Generate net worth multiple times to test probability behavior
    results = [generate_net_worth(character, config) for _ in range(1000)]

    # Calculate the actual expected probability based on generated values
    # For age=30, the liquid_currency will be approximately 100*30 + 1000 = 4000
    # So expected probability = 0.02*30 + 0.000001*4000 + 0.1 = 0.6 + 0.004 + 0.1 = 0.704
    expected_probability = 0.704
    ownership_count = sum(1 for r in results if r.owns_primary_residence)
    ownership_rate = ownership_count / len(results)

    # Should be around 70.4% with some variance (±5%)
    assert (
        0.65 < ownership_rate < 0.75
    ), f"Expected ownership rate around {expected_probability}, got {ownership_rate}"

    # Test that all results have the correct structure
    for result in results[:10]:  # Test first 10
        assert result.chain_code == "TEST123"
        assert isinstance(result.liquid_currency, float)
        assert result.currency_type == "credits"
        assert isinstance(result.owns_primary_residence, bool)
        if result.owns_primary_residence:
            assert isinstance(result.primary_residence_value, float)
            assert result.primary_residence_value > 0

    # Test that the multi-variable function is actually being used
    # The liquid_currency should vary around 4000 ± some noise
    liquid_currencies = [r.liquid_currency for r in results]
    mean_liquid_currency = sum(liquid_currencies) / len(liquid_currencies)
    assert (
        3800 < mean_liquid_currency < 4200
    ), f"Expected mean liquid currency around 4000, got {mean_liquid_currency}"


def test_multi_linear_params_validation():
    """Test validation of MultiLinearParams."""
    # Valid params
    valid_params = MultiLinearParams(
        fields=["age", "income"],
        coefficients={"age": 0.1, "income": 0.000001},
        intercept=0.5,
    )
    assert valid_params.fields == ["age", "income"]

    # Invalid params - mismatched fields and coefficients
    with pytest.raises(
        ValueError, match="Fields and coefficients keys must match exactly"
    ):
        MultiLinearParams(
            fields=["age", "income"],
            coefficients={
                "age": 0.1,
                "wealth": 0.000001,
            },  # 'wealth' instead of 'income'
            intercept=0.5,
        )


def test_function_config_get_required_fields():
    """Test the get_required_fields method of FunctionConfig."""
    # Single-variable function should return empty list
    linear_func = FunctionConfig(
        type="linear", params=LinearParams(slope=1, intercept=0)
    )
    assert linear_func.get_required_fields() == []

    # Multi-variable function should return its fields
    multi_linear_func = FunctionConfig(
        type="multi_linear",
        params=MultiLinearParams(
            fields=["age", "liquid_currency"],
            coefficients={"age": 0.02, "liquid_currency": 0.000001},
            intercept=0.1,
        ),
    )
    assert multi_linear_func.get_required_fields() == ["age", "liquid_currency"]


def test_backwards_compatibility_with_single_variable_functions():
    """Test that existing single-variable functions still work exactly as before."""
    character = MockCharacter(chain_code="TEST123", profession="farmer", age=30)

    # This is the same config from an existing test
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
            }
        },
        metadata={"currency": "credits"},
    )

    # Generate net worth
    net_worth = generate_net_worth(character, config)

    # Verify the result - same assertions as in existing tests
    assert net_worth.chain_code == "TEST123"
    assert isinstance(net_worth.liquid_currency, float)
    assert net_worth.currency_type == "credits"
    # For age=30, mean should be 5*30 + 100 = 250
    assert 150 <= net_worth.liquid_currency <= 350  # mean ± 100
    # For age=30, probability should be 0.02*30 + 0.1 = 0.7
    # Can't test exact ownership since it's probabilistic, but can verify type
    assert isinstance(net_worth.owns_primary_residence, bool)
