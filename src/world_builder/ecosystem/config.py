"""
Module for loading the ecosystem configuration.
This module implements a basic helper function, load_config, to load the ecosystem configuration.
This helper function returns a Pydantic model, which automatically validates the config.

The config is a JSON file that contains the following fields:
- base_probabilities_finite: finite categorical fields (e.g., species, habitat)
- base_probabilities_distributions: distribution-based fields (e.g., age, population_size)
- factors: optional factor graph for conditional probabilities
- override_distributions: optional distribution overrides
- transform_distributions: optional distribution transformations
- metadata: optional metadata fields
"""

from typing import Dict, List
import json
from pathlib import Path
import math

from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing_extensions import Self

from world_builder.distributions_config import (
    Distribution,
    DistributionOverride,
    DistributionTransformMap,
    DistributionTransformOperation,
)


class EcosystemConfig(BaseModel):
    """
    Loads the ecosystem config for the world into a Pydantic model.
    """

    model_config = ConfigDict(frozen=True)

    # finite base probabilities allow the user to specify the probability for fields where one of several values may be chosen
    # so, for example, nested in the "base_probabilities_discrete" key in the config, we might have:
    #   {"base_probabilities_finite":
    #       "species": {
    #           "fox": 0.3,
    #           "rabbit": 0.5,
    #           "hawk": 0.2 } ...}
    base_probabilities_finite: Dict[str, Dict[str, float]] = Field(
        description="Required base probabilities for fields with a finite set of options specified by the user. All probabilities within a specific base probability must sum to unity."
    )

    # distribution base probabilities allow the user to draw a field from some distribution with a specified parameter list
    # for example, they could specify 'age' to be drawn from a normal distribution with mean=5 and std=2
    base_probabilities_distributions: Dict[str, Distribution] = Field(
        description="Required base probabilities for fields which have values drawn from a specified distribution."
    )

    # this is probably the most gnarly part of the config
    # we use a factor-graph approach which means we need a nested dict of factors
    # an example is probably useful here...the expected JSON is of the form:
    # {..."factors": {
    #           "habitat": {
    #               "species": {
    #                   "forest": {
    #                       "fox": 2.0 ...}
    # the above JSON would multiply the chances of a species in forest being a fox by a factor of 2
    # i.e., it's a statement of the form, "If habitat is forest, then species is 2x more likely to be fox"
    factors: Dict[str, Dict[str, Dict[str, Dict[str, float]]]] = Field(
        default_factory=dict,
        description=(
            "Optional nested factors: factor_name -> dimension_name -> key -> subkey -> multiplier."
            "All multipliers must be non-negative."
        ),
    )

    # n.b. -- overrides are performed in the order they are written in the config
    # therefore, if multiple overrides match, we go for the *first* override mentioned in the config
    override_distributions: List[DistributionOverride] = Field(
        default=None,
        description=(
            "Optional overrides for base distributions based on specific field conditions. "
            "Overrides are processed in order; the first match applies."
        ),
    )

    # transformations to apply to the probability distribution section
    transform_distributions: DistributionTransformMap = Field(
        default_factory=dict,
        description=(
            "Optional field-to-trait-based transformations for distributions. "
            "E.g., population_size -> habitat -> 'wetland' -> mean shift."
        ),
    )

    # catch-all dict for any miscellaneous, constant metadata fields
    metadata: Dict[str, str] = Field(
        default_factory=dict,
        description="Optional metadata fields. Can be used to store any string-like constants or metadata.",
    )

    @model_validator(mode="after")
    def validate_base_probabilities(self) -> Self:
        """
        Validates the base probabilities for each category.
        Each base probability must sum to unity, otherwise an error will be raised.
        """
        for category in self.base_probabilities_finite.keys():
            total_weight = sum(
                [prob for prob in self.base_probabilities_finite[category].values()]
            )
            if (
                abs(total_weight - 1.0) > 1e-6
            ):  # add a small tolerance for floating point errors
                raise ValueError(
                    f"Base probabilities for {category} must be 1.0. Received {total_weight} != 1.0"
                )

        # per pydantic convention, return self after validation
        return self

    @model_validator(mode="after")
    def validate_factors(self) -> Self:
        """
        Validates nested factor multipliers are structured and non-negative.
        """
        for factor_name, dims in self.factors.items():
            if not isinstance(dims, dict):
                raise ValueError(
                    f"Factor '{factor_name}' must map to a dict of dimensions."
                )
            for dimension, mapping in dims.items():
                if not isinstance(mapping, dict):
                    raise ValueError(
                        f"Factor '{factor_name}' dimension '{dimension}' must be a dict of key→subkey mappings."
                    )
                for key, submap in mapping.items():
                    if not isinstance(submap, dict):
                        raise ValueError(
                            f"Factor '{factor_name}'[{dimension}]['{key}'] must be a dict of subkey→multiplier."
                        )
                    for subkey, multiplier in submap.items():
                        if not isinstance(multiplier, (int, float)) or multiplier < 0:
                            raise ValueError(
                                f"Multiplier for factor '{factor_name}'[{dimension}]['{key}']['{subkey}'] "
                                f"must be non-negative number (got {multiplier})."
                            )
        return self

    @model_validator(mode="after")
    def validate_factor_consistency(self) -> "EcosystemConfig":
        """
        Checks if the factors are consistent with previous elements named in the config.

        For example, a factor for the field element 'biome' would fail validation if only a field for 'habitat' were specified.
        Likewise, if 'tundra' is mentioned in the factors as a possible field value,
        but 'tundra' never appears in the base distribution, then validation would fail.
        """
        # get the list of possible factors as the list of field element names
        possible_factors = list(self.base_probabilities_finite.keys()) + list(
            self.base_probabilities_distributions.keys()
        )
        # validate that both (1) factor field names, and (2) factor field values are defined previously in the 'base' sections of the config
        for factor_var, influences in self.factors.items():
            if factor_var not in possible_factors:
                raise ValueError(
                    f"Factor variable '{factor_var}' not defined in possible factors: {possible_factors}"
                )
            for inf_var, key_map in influences.items():
                # check sub-factors, i.e., under each field, ensure that the values mentioned by the factors are specified earlier in the config
                domain_keys = self.base_probabilities_finite.get(factor_var, {})
                influenced_keys = self.base_probabilities_finite.get(inf_var, {})
                for key, submap in key_map.items():
                    if key not in domain_keys:
                        raise ValueError(
                            f"Key '{key}' not in base_probabilities_finite['{factor_var}']."
                        )
                    for subkey in submap:
                        if subkey not in influenced_keys:
                            raise ValueError(
                                f"Subkey '{subkey}' not in base_probabilities_finite['{inf_var}']."
                            )
        return self

    @model_validator(mode="after")
    def validate_acyclic_factor_graph(self) -> "EcosystemConfig":
        """
        Validates that the factor graph is acyclic and respects the order defined in the factors mapping.
        Categories listed earlier in the factors mapping cannot be influenced by later categories.

        In order to leverage ancestral sampling, the factor graph must be a DAG.
        Thus, it is important to verify that the factor graph is acyclic before proceeding.
        """
        # preserve insertion order of factor keys
        factor_keys = list(self.factors.keys())
        idx_map = {key: idx for idx, key in enumerate(factor_keys)}

        # build adjacency for dimensions -> factor_var edges when both are in factor_keys
        graph = {key: [] for key in factor_keys}
        for factor_var, influences in self.factors.items():
            for dimension in influences:
                if dimension in graph:
                    graph[dimension].append(factor_var)

        # cycle detection via DFS
        visited: Dict[str, int] = {}  # 0=unvisited, 1=visiting, 2=visited

        def dfs(node: str):
            visited[node] = 1
            for neigh in graph.get(node, []):
                if visited.get(neigh, 0) == 1:
                    raise ValueError(
                        f"Cycle detected in factor graph: '{neigh}' <-> '{node}'"
                    )
                if visited.get(neigh, 0) == 0:
                    dfs(neigh)
            visited[node] = 2

        for node in factor_keys:
            if visited.get(node, 0) == 0:
                dfs(node)

        # enforce top-down ordering: dimensions must come before factor_var
        for factor_var, influenced_vars in self.factors.items():
            pos_f = idx_map[factor_var]
            for influenced_var in influenced_vars:
                if influenced_var in idx_map:
                    pos_i = idx_map[influenced_var]
                    if pos_i <= pos_f:
                        raise ValueError(
                            f"Invalid factor ordering: '{factor_var}' influences '{influenced_var}', "
                            f"but '{influenced_var}' appears at position {pos_i} before '{factor_var}' ({pos_f}) in factors."
                        )
        return self

    @model_validator(mode="after")
    def validate_override_distributions(self) -> Self:
        """
        Validates override_distributions to ensure:
        - The field to override exists in base_probabilities_distributions
        - The condition keys exist in base_probabilities_finite
        - The condition values are valid options in their corresponding finite distributions
        """
        if self.override_distributions:
            for i, override in enumerate(self.override_distributions):
                if override.field not in self.base_probabilities_distributions:
                    raise ValueError(
                        f"Override #{i} targets unknown field '{override.field}', which is not in base_probabilities_distributions."
                    )
                for cond_key, cond_val in override.condition.items():
                    if cond_key not in self.base_probabilities_finite:
                        raise ValueError(
                            f"Override #{i} uses condition key '{cond_key}' not found in base_probabilities_finite."
                        )
                    allowed_values = self.base_probabilities_finite[cond_key]
                    if cond_val not in allowed_values:
                        raise ValueError(
                            f"Override #{i} condition value '{cond_val}' is not valid for key '{cond_key}'. "
                            f"Expected one of: {list(allowed_values.keys())}"
                        )
        return self

    @model_validator(mode="after")
    def _validate_transform_structure(self) -> "EcosystemConfig":
        """
        Validates that the structure of transform_distributions is well-formed:
        - Top-level keys are distribution fields.
        - Each maps to a dict of condition fields (e.g., species, habitat).
        - Each maps to dicts of values (e.g., 'fox') to transform objects.
        """
        for dist_field, trait_map in self.transform_distributions.items():
            if not isinstance(trait_map, dict):
                raise ValueError(
                    f"Transform for '{dist_field}' must be a dictionary of traits."
                )

            for trait_name, value_map in trait_map.items():
                if not isinstance(value_map, dict):
                    raise ValueError(
                        f"Trait '{trait_name}' under '{dist_field}' must map to a dictionary."
                    )

                for trait_value, transform in value_map.items():
                    if not isinstance(transform, DistributionTransformOperation):
                        raise ValueError(
                            f"Invalid transform object for {dist_field}.{trait_name}.{trait_value}: must be a DistributionTransformOperation."
                        )
        return self

    @model_validator(mode="after")
    def _validate_transform_values(self) -> "EcosystemConfig":
        """
        Validates numerical correctness of each DistributionTransformOperation:
        - mean_shift must be finite, if present
        - std_mult must be positive and finite, if present
        - (No enforcement of presence — empty transforms are allowed for forward compatibility)
        """
        for dist_field, trait_map in self.transform_distributions.items():
            for trait_name, value_map in trait_map.items():
                for trait_value, transform in value_map.items():
                    if transform.mean_shift is not None:
                        if math.isnan(transform.mean_shift) or math.isinf(
                            transform.mean_shift
                        ):
                            raise ValueError(
                                f"Invalid mean_shift for {dist_field}.{trait_name}.{trait_value}: must be a finite number."
                            )

                    if transform.std_mult is not None:
                        if (
                            transform.std_mult <= 0
                            or math.isnan(transform.std_mult)
                            or math.isinf(transform.std_mult)
                        ):
                            raise ValueError(
                                f"Invalid std_mult for {dist_field}.{trait_name}.{trait_value}: must be a positive finite number."
                            )
        return self


def load_config(config_filepath: Path) -> EcosystemConfig:
    """
    Loads the JSON configuration file and validates each distribution.
    """
    with open(config_filepath, "r", encoding="utf-8") as f:
        try:
            config_json = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Tried to load {config_filepath} into JSON object and failed. Check to ensure it the file provided is valid JSON."
            ) from e
    ecosystem_config = EcosystemConfig(**config_json)
    return ecosystem_config
