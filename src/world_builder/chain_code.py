"""
This is a module for generating a 'chain code', which is essentially a UUID.
"""
import os
import time
import uuid


def generate_uuidv7():
    timestamp_ms = int(time.time() * 1000)

    if timestamp_ms >= (1 << 48):
        raise ValueError("Timestamp too large for UUIDv7")

    rand_bytes = os.urandom(10)
    rand_int = int.from_bytes(rand_bytes, "big")

    uuid_int = timestamp_ms << 80
    uuid_int |= 0x7 << 76
    uuid_int |= 0x2 << 62
    uuid_int |= rand_int & ((1 << 62) - 1)

    return uuid.UUID(int=uuid_int)


def generate_chain_code(species="unknown", is_female=False):
    species_code = species.upper()[:3]
    gender_code = "F" if is_female else "M"

    prefix = "CC" + "-" + species_code + "-" + gender_code + "-"

    sampled_uuid = generate_uuidv7()

    chain_code = prefix + str(sampled_uuid)
    return chain_code
