# data-worldgen
Project exploring data technologies using world generation as an example.

## World Builder

Module that creates characters from a specific world.

Has a Pydantic model for the config. Samples static or slowly-changing dimensions related to the character based on a factor-graph approach.

### Population Configuration

The population configuration is a JSON-based system that defines the demographic makeup of a world. It specifies base probabilities for various character attributes (like species, profession, and allegiance), along with a factor-graph approach to model how these attributes influence each other (e.g., how being in a certain city affects the likelihood of different professions). The config also supports distribution-based attributes like age, with the ability to override or transform these distributions based on other character traits.

## Namegen

Generates names using a Markov chain approach based on the data in the United States baby names dataset.

### References
U.S. name analysis taken from https://catalog.data.gov/dataset/baby-names-from-social-security-card-applications-national-data
Wookieepedia for list of Star Wars planets which were used to generate surnames based on planet names
