# data-worldgen
Project exploring data technologies using world generation as an example.

## World Builder

Module that creates characters from a specific world.

Has a Pydantic model for the config. Samples static or slowly-changing dimensions related to the character based on a factor-graph approach.

## Namegen

Generates names using a Markov chain approach based on the data in the United States baby names dataset.

### References
U.S. name analysis taken from https://catalog.data.gov/dataset/baby-names-from-social-security-card-applications-national-data
Wookieepedia for list of Star Wars planets which were used to generate surnames based on planet names
