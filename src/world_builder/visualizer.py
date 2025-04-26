import matplotlib.pyplot as plt
from collections import Counter


def create_population_dashboard(characters, save_filepath):
    """
    Generates a simple dashboard visualization showing:
      - Species distribution
      - Gender distribution
      - Top 10 professions
    """
    species_counts = Counter(char.species for char in characters)
    gender_counts = Counter(char.gender for char in characters)
    profession_counts = Counter(char.profession for char in characters)
    cities_counts = Counter(char.city for char in characters)
    allegiance_counts = Counter(char.allegiance for char in characters)

    # Create subplots for each distribution
    fig, axs = plt.subplots(1, 5, figsize=(15, 5))

    # Species Distribution
    axs[0].bar(species_counts.keys(), species_counts.values())
    axs[0].set_title("Species Distribution")
    axs[0].tick_params(axis="x", rotation=45)

    # Gender Distribution
    axs[1].bar(gender_counts.keys(), gender_counts.values())
    axs[1].set_title("Gender Distribution")

    # Top 10 Professions
    top_professions = profession_counts.most_common(10)
    prof_names = [prof for prof, count in top_professions]
    prof_counts = [count for prof, count in top_professions]
    axs[2].bar(prof_names, prof_counts)
    axs[2].set_title("Top 10 Professions")
    axs[2].tick_params(axis="x", rotation=45)

    axs[3].bar(cities_counts.keys(), cities_counts.values())
    axs[3].set_title("Cities Distribution")
    axs[3].tick_params(axis="x", rotation=45)

    axs[4].bar(allegiance_counts.keys(), allegiance_counts.values())
    axs[4].set_title("Allegiance Distribution")
    axs[4].tick_params(axis="x", rotation=45)

    plt.tight_layout()
    plt.savefig(save_filepath)
