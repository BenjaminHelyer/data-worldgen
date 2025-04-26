import random

# from namegen.generate_name import generate_name
from .age import sample_age
from .chain_code import generate_chain_code


class Character:
    def __init__(
        self,
        chain_code,
        first_name,
        surname,
        species,
        age,
        gender,
        profession,
        planet,
        city,
        allegiance,
    ):
        self.chain_code = chain_code
        self.first_name = first_name
        self.surname = surname
        self.species = species
        self.age = age
        self.gender = gender
        self.profession = profession
        self.planet = planet
        self.city = city
        self.allegiance = allegiance

    def __repr__(self):
        return (
            f"{self.first_name} {self.surname}, {self.species}, {self.gender}, "
            f"{self.profession} from {self.city}, {self.planet} (Age: {self.age}). Allegiance: {self.allegiance}"
        )


def create_character(config):
    """
    Creates a random character using a factor-graph approach.
    The factors are applied in stages:
      1. City is sampled first.
      2. Species weights are adjusted using the city's city_species factors.
      3. Allegiance is sampled using base allegiance weights adjusted by city_allegiance and species_allegiance.
      4. Gender is sampled using base gender weights adjusted by city_gender and species_gender.
      5. Profession is sampled using base profession weights adjusted by city_profession and species_profession.
    """
    # --- 1. Sample City (upstream)
    city = random.choices(
        population=list(config["city_weights"].keys()),
        weights=list(config["city_weights"].values()),
        k=1,
    )[0]

    # --- 2. Sample Species adjusted by city_species factors.
    base_species = config["species_weights"]
    adjusted_species = {}
    # Lookup city_species factors (if any) for this city.
    city_species_factors = (
        config.get("factors", {}).get("city_species", {}).get(city, {})
    )
    for sp, weight in base_species.items():
        # Use the factor if defined; keys in city_species are expected to be lower-case.
        multiplier = city_species_factors.get(sp.lower(), 1.0)
        adjusted_species[sp] = weight * multiplier
    species = random.choices(
        population=list(adjusted_species.keys()),
        weights=list(adjusted_species.values()),
        k=1,
    )[0]

    # --- 3. Sample Profession adjusted by city_profession and species_profession factors.
    base_profession = config["profession_weights"]
    adjusted_profession = {}
    city_profession_factors = (
        config.get("factors", {}).get("city_profession", {}).get(city, {})
    )
    species_profession_factors = (
        config.get("factors", {}).get("species_profession", {}).get(species.lower(), {})
    )
    for prof, weight in base_profession.items():
        mult_city = city_profession_factors.get(prof.lower(), 1.0)
        mult_species = species_profession_factors.get(prof.lower(), 1.0)
        adjusted_profession[prof] = weight * mult_city * mult_species
    profession = random.choices(
        population=list(adjusted_profession.keys()),
        weights=list(adjusted_profession.values()),
        k=1,
    )[0]

    # --- 4. Sample Allegiance adjusted by city_allegiance, species_allegiance, and profession_allegiance factors.
    base_allegiance = config["allegiance_weights"]
    adjusted_allegiance = {}
    city_allegiance_factors = (
        config.get("factors", {}).get("city_allegiance", {}).get(city, {})
    )
    species_allegiance_factors = (
        config.get("factors", {}).get("species_allegiance", {}).get(species.lower(), {})
    )
    profession_allegiance_factors = (
        config.get("factors", {})
        .get("profession_allegiance", {})
        .get(profession.lower(), {})
    )
    for alleg, weight in base_allegiance.items():
        mult_city = city_allegiance_factors.get(alleg, 1.0)
        mult_species = species_allegiance_factors.get(alleg, 1.0)
        mult_profession = profession_allegiance_factors.get(alleg, 1.0)
        adjusted_allegiance[alleg] = weight * mult_city * mult_species * mult_profession
    allegiance = random.choices(
        population=list(adjusted_allegiance.keys()),
        weights=list(adjusted_allegiance.values()),
        k=1,
    )[0]

    # --- 5. Sample Gender adjusted by city_gender and species_gender factors.
    base_gender = config["gender_weights"]
    adjusted_gender = {}
    city_gender_factors = config.get("factors", {}).get("city_gender", {}).get(city, {})
    species_gender_factors = (
        config.get("factors", {}).get("species_gender", {}).get(species.lower(), {})
    )
    for gen, weight in base_gender.items():
        # Normalize keys to lower-case for the lookup.
        mult_city = city_gender_factors.get(gen.lower(), 1.0)
        mult_species = species_gender_factors.get(gen.lower(), 1.0)
        adjusted_gender[gen] = weight * mult_city * mult_species
    gender = random.choices(
        population=list(adjusted_gender.keys()),
        weights=list(adjusted_gender.values()),
        k=1,
    )[0]

    # --- Other attributes remain based on defaults.
    planet = config["planet"]
    is_female = gender.lower() == "female"
    # first_name = generate_name(species, is_female)
    # surname = generate_name(species, False)
    first_name = "Test"
    surname = "Test"

    age = sample_age(species, city, profession, config)
    chain_code = generate_chain_code(species, is_female)

    return Character(
        chain_code,
        first_name,
        surname,
        species,
        age,
        gender,
        profession,
        planet,
        city,
        allegiance,
    )
