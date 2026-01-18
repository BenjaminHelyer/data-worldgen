"""
This is a module for generating an 'animal_id', which is essentially a UUID.
"""

import os
import time
from uuid import UUID


def generate_uuidv7() -> UUID:
    """
    Generates a UUID which is similar to UUIDv7.

    UUIDv7 is a UUID variant that includes a timestamp. Essentially UUIDv7 is
    timestamp + random sequence, with a few other added bits. Due to the fact
    that the unique identifier is prefaced by a timestamp, monotonicity is in
    some situations garunteed. This can eable quicker INSERT operations on a
    database (in a typical case, INSERTs would simply be an append if the UUID
    is used as a primary key). Indexing and partitioning can also be improved
    if one uses UUIDv7 as a primary key, rather than a completely random UUID.

    Returns:
        UUID: The generated UUIDv7.
    """
    timestamp_ms = int(time.time() * 1000)  # timestamp since Unix epoch

    # defensive programming in case of a huge timestamp value
    # this could happen since we are dealing with fictional universes
    if timestamp_ms >= (1 << 48):
        raise ValueError("Timestamp too large for UUIDv7")

    rand_bytes = os.urandom(10)  # 10 random bytes, i.e., 80 random bits
    rand_int = int.from_bytes(rand_bytes, "big")

    uuid_int = timestamp_ms << 80
    uuid_int |= 0x7 << 76  # set version bit to 7
    uuid_int |= 0x2 << 62  # set variant bit to 2
    uuid_int |= rand_int & ((1 << 62) - 1)

    return UUID(int=uuid_int)


def generate_animal_id(species: str = "unknown", habitat: str = "unknown") -> str:
    """
    Generates the animal_id for an animal.
    Args:
        species (str): The species of the animal.
        habitat (str): The habitat/environment where the animal lives.
    Returns:
        str: The animal_id for the animal.
    """
    species_code = species.upper()[:3]
    habitat_code = habitat.upper()[:3]

    prefix = "AN" + "-" + species_code + "-" + habitat_code + "-"

    sampled_uuid = generate_uuidv7()

    animal_id = prefix + str(sampled_uuid)
    return animal_id
