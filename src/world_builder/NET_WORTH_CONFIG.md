# Net Worth Configuration

This document describes the configuration format for net worth generation in the world builder.

## Overview

The net worth configuration file is a JSON file that defines how net worth values are generated for characters based on their professions. The configuration allows for flexible, profession-specific distributions that can take into account character attributes like age or experience.

## Configuration Format

The configuration file has two main sections:

1. `profession_liquid_currency`: Defines the net worth generation rules for each profession
2. `metadata`: Contains additional configuration metadata

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
    "metadata": {
        "currency": "credits",
        "era": "Clone Wars"
    }
}
```

## Configuration Fields

1. **profession_liquid_currency**: A dictionary mapping profession names to their net worth configurations.
   Each profession entry contains:
   - `field_name`: The character attribute to use (e.g., "age")
   - `mean_function`: Function configuration for the mean value
   - `noise_function`: Function configuration for the noise/variation

2. **metadata**: Optional metadata fields
   - `currency`: The currency type (defaults to "credits")
   - `era`: The era this configuration is for

## Function Types

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

## Example: Complex Configuration

```json
{
    "profession_liquid_currency": {
        "merchant": {
            "field_name": "experience",
            "mean_function": {
                "type": "exponential",
                "params": {
                    "base": 50,
                    "rate": 0.1
                }
            },
            "noise_function": {
                "type": "normal",
                "params": {
                    "field_name": "experience",
                    "scale_factor": {
                        "type": "quadratic",
                        "params": {
                            "a": 0.01,
                            "b": 0,
                            "c": 0
                        }
                    }
                }
            }
        }
    },
    "metadata": {
        "currency": "credits"
    }
}
```

## Notes

1. All monetary values are in the specified currency units (defaults to "credits")
2. Functions can use any numeric character attribute (age, experience, etc.)
3. Noise functions support normal, lognormal, and truncated normal distributions
4. The configuration is validated when loaded to ensure all required fields are present 