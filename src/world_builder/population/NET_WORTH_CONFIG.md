# Net Worth Configuration

This document describes the configuration format for net worth generation in the world builder.

## Overview

The net worth configuration file is a JSON file that defines how net worth values are generated for characters based on their professions. The configuration allows for flexible, profession-specific distributions that can take into account character attributes like age or experience.

## Configuration Format

The configuration file has the following main sections:

1. `profession_liquid_currency`: Defines the liquid currency generation rules for each profession
2. `profession_has`: Defines ownership probabilities for various asset types by profession
3. `profession_value`: Defines value distributions for owned assets by profession
4. `metadata`: Contains additional configuration metadata

### Asset Types

The following asset types are supported in both `profession_has` and `profession_value`:

- `primary_residence`: Primary living quarters
- `other_properties`: Additional real estate holdings
- `starships`: Owned starships
- `speeders`: Personal speeders
- `other_vehicles`: Additional vehicles
- `luxury_property`: High-value luxury items
- `galactic_stock`: Stock market investments
- `business`: Business ownership

### Example Configuration

```json
{
    "profession_liquid_currency": {
        "farmer": {
            "field_name": "age",
            "mean_function": {
                "type": "linear",
                "params": {
                    "slope": 5,
                    "intercept": 100
                }
            },
            "noise_function": {
                "type": "normal",
                "params": {
                    "field_name": "age",
                    "scale_factor": {
                        "type": "linear",
                        "params": {
                            "slope": 0.1,
                            "intercept": 0
                        }
                    }
                }
            }
        }
    },
    "profession_has": {
        "primary_residence": {
            "farmer": {
                "field_name": "age",
                "mean_function": {
                    "type": "linear",
                    "params": {
                        "slope": 0.02,
                        "intercept": 0.1
                    }
                }
            }
        },
        "starships": {
            "farmer": {
                "field_name": "age",
                "mean_function": {
                    "type": "linear",
                    "params": {
                        "slope": 0.005,
                        "intercept": 0.01
                    }
                }
            }
        }
    },
    "profession_value": {
        "primary_residence": {
            "farmer": {
                "field_name": "age",
                "mean_function": {
                    "type": "linear",
                    "params": {
                        "slope": 1000,
                        "intercept": 50000
                    }
                },
                "noise_function": {
                    "type": "normal",
                    "params": {
                        "field_name": "age",
                        "scale_factor": {
                            "type": "linear",
                            "params": {
                                "slope": 100,
                                "intercept": 5000
                            }
                        }
                    }
                }
            }
        },
        "starships": {
            "farmer": {
                "field_name": "age",
                "mean_function": {
                    "type": "linear",
                    "params": {
                        "slope": 2000,
                        "intercept": 100000
                    }
                },
                "noise_function": {
                    "type": "normal",
                    "params": {
                        "field_name": "age",
                        "scale_factor": {
                            "type": "linear",
                            "params": {
                                "slope": 200,
                                "intercept": 10000
                            }
                        }
                    }
                }
            }
        }
    },
    "metadata": {
        "currency": "credits",
        "era": "Clone Wars"
    }
}
```

## Configuration Details

### Profession Liquid Currency

The `profession_liquid_currency` section defines how liquid currency is generated for each profession. Each profession entry contains:
- `field_name`: The character attribute to use (e.g., "age")
- `mean_function`: Function configuration for the mean value
- `noise_function`: Function configuration for the noise/variation

### Asset Ownership and Values

Assets are configured through two main sections:

1. `profession_has`: Defines the probability of owning each asset type
   - Each asset type contains profession-specific configurations
   - The mean function must output a probability between 0 and 1
   - No noise function is used (ownership is determined by a Bernoulli trial)

2. `profession_value`: Defines the value distribution for owned assets
   - Each asset type contains profession-specific configurations
   - The mean function determines the base value
   - The noise function adds variation to the value
   - Values are only generated if the character owns that asset type

### Function Types

The configuration supports several function types for both mean and noise calculations:

1. **Linear**: `y = mx + b`
   ```json
   {
       "type": "linear",
       "params": {
           "slope": 5,
           "intercept": 100
       }
   }
   ```

2. **Exponential**: `y = a * e^(rx)`
   ```json
   {
       "type": "exponential",
       "params": {
           "base": 50,
           "rate": 0.1
       }
   }
   ```

3. **Quadratic**: `y = ax² + bx + c`
   ```json
   {
       "type": "quadratic",
       "params": {
           "a": 1,
           "b": 2,
           "c": 3
       }
   }
   ```

4. **Constant**: `y = k`
   ```json
   {
       "type": "constant",
       "params": {
           "value": 1000
       }
   }
   ```

## Notes

1. All monetary values are in the specified currency units (defaults to "credits")
2. Functions can use any numeric character attribute (age, experience, etc.)
3. Noise functions support normal, lognormal, and truncated normal distributions
4. The configuration is validated when loaded to ensure all required fields are present
5. Asset ownership is determined by a Bernoulli trial using the probability from the corresponding `profession_has` field
6. Asset values are only generated if a character owns that asset type
7. Each asset type follows the same pattern: a probability of ownership and a value distribution if owned 