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
      2. Species base_probability are adjusted using the city's city_species factors.
      3. Allegiance is sampled using base allegiance base_probability adjusted by city_allegiance and species_allegiance.
      4. Gender is sampled using base gender base_probability adjusted by city_gender and species_gender.
      5. Profession is sampled using base profession base_probability adjusted by city_profession and species_profession.
    """
    city = random.choices(
        population=list(config.city_base_probability.keys()),
        weights=list(config.city_base_probability.values()),
        k=1,
    )[0]

    species = random.choices(
        population=list(config.species_base_probability.keys()),
        weights=list(config.species_base_probability.values()),
        k=1,
    )[0]

    profession = random.choices(
        population=list(config.profession_base_probability.keys()),
        weights=list(config.profession_base_probability.values()),
        k=1,
    )[0]

    allegiance = random.choices(
        population=list(config.allegiance_base_probability.keys()),
        weights=list(config.allegiance_base_probability.values()),
        k=1,
    )[0]

    gender = random.choices(
        population=list(config.gender_base_probability.keys()),
        weights=list(config.gender_base_probability.values()),
        k=1,
    )[0]

    # --- Other attributes remain based on defaults.
    planet = config.planet
    is_female = gender.lower() == "female"
    # first_name = generate_name(species, is_female)
    # surname = generate_name(species, False)
    first_name = "Test"
    surname = "Test"

    age = 30
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
