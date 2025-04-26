import os
import time
import uuid

SPECIES_ABBREVIATIONS = {
    "bothan": "BOT",
    "human": "HUM",
    "ithorian": "ITH",
    "moncal": "MON",
    "rodian": "ROD",
    "sullustan": "SUL",
    "trandoshan": "TRA",
    "twilek": "TWI",
    "wookiee": "WOK",
    "zabrak": "ZAB"
}

def generate_uuidv7():
    # Get current time in milliseconds since epoch
    timestamp_ms = int(time.time() * 1000)

    # Ensure 48-bit max
    if timestamp_ms >= (1 << 48):
        raise ValueError("Timestamp too large for UUIDv7")

    # Generate 80 bits of randomness
    rand_bytes = os.urandom(10)  # 80 bits
    rand_int = int.from_bytes(rand_bytes, "big")

    # Compose 128-bit UUID
    uuid_int = (timestamp_ms << 80)             # top 48 bits
    uuid_int |= (0x7 << 76)                     # version = 7 (bits 76-79)
    uuid_int |= (0x2 << 62)                     # variant = 10 (RFC 4122)
    uuid_int |= (rand_int & ((1 << 62) - 1))    # low 62 bits of randomness

    return uuid.UUID(int=uuid_int)

def generate_chain_code(species='unknown', is_female=False):
    species_code = SPECIES_ABBREVIATIONS.get(species, 'UNK')
    gender_code = 'F' if is_female else 'M'

    prefix = 'CC' + '-' + species_code + '-' + gender_code + '-'

    sampled_uuid = generate_uuidv7()

    chain_code = prefix + str(sampled_uuid)
    return chain_code
