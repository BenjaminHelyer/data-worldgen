<div align="center">
  <img src="simple_pdf_circle_logo_preview.png" alt="data-worldgen logo" width="200">
</div>

# data-worldgen

Synthetic data generation pipeline which uses a factor-graph approach. Two use-cases are currently supported:

1. Ecosystem generation - generates hypothetical organisms of various species in a given ecosystem

2. Character economics generation - generates hypothetical characters and their economic situations in a fictional universe

## Overview

Module that creates synthetic records for entities from a specific context, such as ecosystems or populations.

Has a Pydantic model for the config. Samples static or slowly-changing dimensions related to entities based on a factor-graph approach.

## Get Started Quickly

First, clone the repository then install dependencies:

```
pip install -e .
```

To run the world builder with a config file, use the example script:

```
cd examples/world_builder
python ecosystem_example.py
```

This uses the config at `examples/world_builder/ecosystem_config.json` and generates 100 entities (in this case, organisms), saving them to a Parquet file.

Then, you can visualize the results of your generation by running the dashboard script:

```
streamlit run ../../src/world_builder/ecosystem/dashboard.py 
```

Or, you can plot them simply via the plotting functionality:

```
python plot_ecosystem.py
```

![Ecosystem Species and Age Distributions](readme_example_plot.png)
