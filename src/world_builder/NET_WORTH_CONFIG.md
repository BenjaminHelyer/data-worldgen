# Net Worth Configuration

This document describes the configuration format for net worth generation in the world builder.

## Overview

The net worth configuration file is a JSON file that defines how net worth values are generated for characters based on their professions. The configuration allows for flexible, profession-specific distributions that can take into account character attributes like age or experience.

## Configuration Format

The configuration file has the following main sections:

1. `profession_liquid_currency`: Defines the net worth generation rules for each profession
2. `profession_has_primary_residence`: Optional section defining the probability of owning a primary residence for each profession
3. `profession_primary_residence_value`: Optional section defining the value distribution for owned primary residences
4. `profession_has_other_properties`: Optional section defining the probability of owning other properties for each profession
5. `profession_other_properties_net_value`: Optional section defining the value distribution for owned other properties
6. `profession_has_starships`: Optional section defining the probability of owning starships for each profession
7. `profession_starships_net_value`: Optional section defining the value distribution for owned starships
8. `profession_has_speeders`: Optional section defining the probability of owning speeders for each profession
9. `profession_speeders_net_value`: Optional section defining the value distribution for owned speeders
10. `profession_has_other_vehicles`: Optional section defining the probability of owning other vehicles for each profession
11. `profession_other_vehicles_net_value`: Optional section defining the value distribution for owned other vehicles
12. `profession_has_luxury_property`: Optional section defining the probability of owning luxury property for each profession
13. `profession_luxury_property_net_value`: Optional section defining the value distribution for owned luxury property
14. `profession_has_galactic_stock`: Optional section defining the probability of owning galactic stock for each profession
15. `profession_galactic_stock_net_value`: Optional section defining the value distribution for owned galactic stock
16. `profession_has_business`: Optional section defining the probability of owning a business for each profession
17. `profession_business_net_value`: Optional section defining the value distribution for owned businesses
18. `metadata`: Contains additional configuration metadata

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
    "profession_has_primary_residence": {
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
    "profession_primary_residence_value": {
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
    "profession_has_other_properties": {
        "farmer": {
            "field_name": "age",
            "mean_function": {
                "type": "linear",
                "params": {
                    "slope": 0.01,
                    "intercept": 0.05
                }
            }
        }
    },
    "profession_other_properties_net_value": {
        "farmer": {
            "field_name": "age",
            "mean_function": {
                "type": "linear",
                "params": {
                    "slope": 500,
                    "intercept": 25000
                }
            },
            "noise_function": {
                "type": "normal",
                "params": {
                    "field_name": "age",
                    "scale_factor": {
                        "type": "linear",
                        "params": {
                            "slope": 50,
                            "intercept": 2500
                        }
                    }
                }
            }
        }
    },
    "profession_has_starships": {
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
    },
    "profession_starships_net_value": {
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
    },
    "profession_has_speeders": {
        "farmer": {
            "field_name": "age",
            "mean_function": {
                "type": "linear",
                "params": {
                    "slope": 0.015,
                    "intercept": 0.05
                }
            }
        }
    },
    "profession_speeders_net_value": {
        "farmer": {
            "field_name": "age",
            "mean_function": {
                "type": "linear",
                "params": {
                    "slope": 300,
                    "intercept": 15000
                }
            },
            "noise_function": {
                "type": "normal",
                "params": {
                    "field_name": "age",
                    "scale_factor": {
                        "type": "linear",
                        "params": {
                            "slope": 30,
                            "intercept": 1500
                        }
                    }
                }
            }
        }
    },
    "profession_has_other_vehicles": {
        "farmer": {
            "field_name": "age",
            "mean_function": {
                "type": "linear",
                "params": {
                    "slope": 0.01,
                    "intercept": 0.03
                }
            }
        }
    },
    "profession_other_vehicles_net_value": {
        "farmer": {
            "field_name": "age",
            "mean_function": {
                "type": "linear",
                "params": {
                    "slope": 400,
                    "intercept": 20000
                }
            },
            "noise_function": {
                "type": "normal",
                "params": {
                    "field_name": "age",
                    "scale_factor": {
                        "type": "linear",
                        "params": {
                            "slope": 40,
                            "intercept": 2000
                        }
                    }
                }
            }
        }
    },
    "profession_has_luxury_property": {
        "farmer": {
            "field_name": "age",
            "mean_function": {
                "type": "linear",
                "params": {
                    "slope": 0.008,
                    "intercept": 0.02
                }
            }
        }
    },
    "profession_luxury_property_net_value": {
        "farmer": {
            "field_name": "age",
            "mean_function": {
                "type": "linear",
                "params": {
                    "slope": 3000,
                    "intercept": 150000
                }
            },
            "noise_function": {
                "type": "normal",
                "params": {
                    "field_name": "age",
                    "scale_factor": {
                        "type": "linear",
                        "params": {
                            "slope": 300,
                            "intercept": 15000
                        }
                    }
                }
            }
        }
    },
    "profession_has_galactic_stock": {
        "farmer": {
            "field_name": "age",
            "mean_function": {
                "type": "linear",
                "params": {
                    "slope": 0.012,
                    "intercept": 0.04
                }
            }
        }
    },
    "profession_galactic_stock_net_value": {
        "farmer": {
            "field_name": "age",
            "mean_function": {
                "type": "linear",
                "params": {
                    "slope": 800,
                    "intercept": 40000
                }
            },
            "noise_function": {
                "type": "normal",
                "params": {
                    "field_name": "age",
                    "scale_factor": {
                        "type": "linear",
                        "params": {
                            "slope": 80,
                            "intercept": 4000
                        }
                    }
                }
            }
        }
    },
    "profession_has_business": {
        "farmer": {
            "field_name": "age",
            "mean_function": {
                "type": "linear",
                "params": {
                    "slope": 0.01,
                    "intercept": 0.03
                }
            }
        }
    },
    "profession_business_net_value": {
        "farmer": {
            "field_name": "age",
            "mean_function": {
                "type": "linear",
                "params": {
                    "slope": 2500,
                    "intercept": 125000
                }
            },
            "noise_function": {
                "type": "normal",
                "params": {
                    "field_name": "age",
                    "scale_factor": {
                        "type": "linear",
                        "params": {
                            "slope": 250,
                            "intercept": 12500
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

2. **Asset Ownership and Value Fields**: For each asset type (primary residence, other properties, starships, speeders, other vehicles, luxury property, galactic stock, business), there are two configuration sections:
   - `profession_has_*`: Defines the probability of owning that asset type
     - `field_name`: The character attribute to use (e.g., "age")
     - `mean_function`: Function configuration that outputs a probability between 0 and 1
   - `profession_*_value` or `profession_*_net_value`: Defines the value distribution for owned assets
     - `field_name`: The character attribute to use (e.g., "age")
     - `mean_function`: Function configuration for the mean value
     - `noise_function`: Function configuration for the value variation
   The value distribution is only used if the character owns that asset type.

3. **metadata**: Optional metadata fields
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

## Notes

1. All monetary values are in the specified currency units (defaults to "credits")
2. Functions can use any numeric character attribute (age, experience, etc.)
3. Noise functions support normal, lognormal, and truncated normal distributions
4. The configuration is validated when loaded to ensure all required fields are present
5. Asset ownership is determined by a Bernoulli trial using the probability from the corresponding `profession_has_*` field
6. Asset values are only generated if a character owns that asset type
7. Each asset type follows the same pattern: a probability of ownership and a value distribution if owned 