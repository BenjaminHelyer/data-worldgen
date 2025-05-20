# Net Worth Configuration

This document describes the configuration system for generating character net worth values in the world builder.

## Overview

The net worth configuration system models how a character's wealth evolves over time based on their profession and attributes. The core concept is that net worth follows a predictable trend over a character's lifetime (e.g., increasing with age or experience), but with natural variation at any given point in time. For example, a farmer's wealth might generally increase with age, but two 30-year-old farmers could have different net worths due to various factors like crop yields, market conditions, or personal circumstances.

The system captures this by defining two components for each profession:
1. A mean function that describes the expected wealth trend over time (e.g., linear growth with age)
2. A noise function that adds realistic variation around this trend

This approach allows us to generate realistic net worth distributions that reflect both the systematic progression of wealth in a profession and the natural variation we'd expect to see in real-world scenarios.

The net worth configuration system uses function-based distributions to calculate a character's net worth based on their attributes (e.g., age, experience). Each profession can have its own unique function that determines how net worth scales with these attributes.

## Configuration Structure

The configuration is defined in a JSON file with the following structure:

```json
{
    "profession_net_worth": {
        "profession_name": {
            "field_name": "attribute_name",
            "mean_function": {
                "type": "function_type",
                "params": {
                    // Function-specific parameters
                }
            },
            "noise_function": {
                "type": "normal",
                "params": {
                    "field_name": "attribute_name",
                    "scale_factor": {
                        "type": "function_type",
                        "params": {
                            // Function-specific parameters
                        }
                    }
                }
            }
        }
    },
    "metadata": {
        "currency": "currency_type",
        // Additional metadata fields
    }
}
```

### Components

1. **profession_net_worth**: A dictionary mapping profession names to their net worth configurations.

2. **field_name**: The character attribute to use for net worth calculation (e.g., "age", "experience").

3. **mean_function**: Defines how the base net worth scales with the attribute.
   - **type**: One of "linear", "exponential", or "quadratic"
   - **params**: Parameters specific to the function type:
     - Linear: `slope` and `intercept`
     - Exponential: `base` and `rate`
     - Quadratic: `a`, `b`, and `c`

4. **noise_function**: Defines the random variation in net worth.
   - **type**: Currently only supports "normal" distribution
   - **params**:
     - **field_name**: The attribute to use for scaling
     - **scale_factor**: A function configuration that determines how the standard deviation scales with the attribute

5. **metadata**: Optional metadata fields.
   - **currency**: The type of currency (defaults to "credits")

## Example Configurations

### Constant Net Worth

### Net Worth with Age

The net worth configuration system models how a character's wealth evolves over time based on their profession and attributes. Each profession can have its own unique function that determines how net worth scales with these attributes.

For example, a Sith's net worth might be constant regardless of age, as they are provided for by the Empire:

```json
{
    "profession_net_worth": {
        "Sith": {
            "field_name": "age",
            "mean_function": {
                "type": "constant",
                "params": {
                    "value": 10000
                }
            },
            "noise_function": {
                "type": "normal",
                "params": {
                    "field_name": "age",
                    "scale_factor": {
                        "type": "constant",
                        "params": {
                            "value": 1000
                        }
                    }
                }
            }
        }
    },
    "metadata": {
        "currency": "imperial_credits"
    }
}
```

In this example, a Sith would have a mean net worth of 10,000 imperial credits with a standard deviation of 1,000 credits, regardless of their age.

### Linear Scaling with Age

```json
{
    "profession_net_worth": {
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
        "currency": "credits"
    }
}
```

In this example:
- A 30-year-old farmer would have a mean net worth of 250 credits (5 * 30 + 100)
- The standard deviation would be 3 credits (0.1 * 30 + 0)

### Exponential Growth with Experience

```json
{
    "profession_net_worth": {
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
    }
}
```

In this example:
- A merchant with 5 years of experience would have a mean net worth of 82.4 credits (50 * e^(0.1 * 5))
- The standard deviation would be 0.25 credits (0.01 * 5^2)

## Implementation Details

The net worth generation process:
1. Gets the character's attribute value (e.g., age)
2. Calculates the mean net worth using the mean_function
3. Calculates the standard deviation using the noise_function's scale_factor
4. Generates the final net worth by adding normally distributed noise
5. Ensures the net worth is never negative

## Best Practices

1. **Mean Functions**:
   - Use linear functions for steady growth
   - Use exponential functions for accelerating growth
   - Use quadratic functions for growth that accelerates then slows

2. **Noise Functions**:
   - Keep scale factors small relative to mean values
   - Consider using quadratic scale factors for professions where wealth variation increases with experience

3. **Field Selection**:
   - Use "age" for professions where experience correlates with age
   - Use "experience" for professions where experience can be gained independently of age 