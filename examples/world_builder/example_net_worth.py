from pathlib import Path

from world_builder.population.character import Character
from world_builder.population.net_worth_generator import generate_net_worth
from world_builder.population.net_worth_config import NetWorthConfig, load_config

example_character = Character(
    species="human",
    age=30,
    profession="farmer",
    character_id="TEST123",
)

file_path = Path(__file__).parent / "example_net_worth_config.json"

net_worth_config = load_config(file_path)

net_worth = generate_net_worth(example_character, net_worth_config)
print(net_worth)
