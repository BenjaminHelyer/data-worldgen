# --- Age Sampling Extensions (Continuous) ---
import random
import math

def sample_from_distribution(dist):
    """
    Samples a value from a given distribution definition.
    Currently supports:
      - 'normal': uses 'mean' and 'std'
      - 'lognormal': uses 'mean' and 'sigma'
    Returns an absolute integer sample.
    """
    mean = dist.get("mean", None)
    std = dist.get("std", None)
    min_val = dist.get("min", None)
    max_val = dist.get("max", None)

    # compute these for lognormal distributions
    log_mu = math.log(mean**2 / math.sqrt(std**2 + mean**2))
    log_std = math.sqrt(math.log(1 + (std**2 / mean**2)))

    if dist["type"] == "normal":
        return abs(int(random.gauss(mean, std)))
    elif dist["type"] == "lognormal":
        return abs(int(random.lognormvariate(log_mu, log_std)))
    elif dist["type"] == "truncated_normal":
        sample = random.gauss(mean, std)
        # use a trial num to prevent an infinite loop
        trial_num = 0
        trial_cutoff = 10
        while (sample < min_val or sample > max_val) and (trial_num < trial_cutoff):
            sample = random.gauss(mean, std)
            trial_num += 1
            if trial_num == trial_cutoff:
                # in a nicely defined distribution, 
                # this shouldn't happen often, but it prevents the loop from running too long
                # in the case it does, we shove it to the min value, meaning realistically there will be slightly more younger folks 
                # than folks at the max age
                sample = min_val
        return int(sample)
    elif dist["type"] == "truncated_lognormal":
        sample = abs(int(random.lognormvariate(log_mu, log_std)))
        # use a trial num to prevent an infinite loop
        trial_num = 0
        trial_cutoff = 10
        while (sample < min_val or sample > max_val) and (trial_num < trial_cutoff):
            sample = abs(int(random.lognormvariate(log_mu, log_std)))
            trial_num += 1
            if trial_num == trial_cutoff:
                # in a nicely defined distribution, 
                # this shouldn't happen often, but it prevents the loop from running too long
                # in the case it does, we shove it to the min value, meaning realistically there will be slightly more younger folks 
                # than folks at the max age
                sample = min_val
        return int(sample)
    else:
        raise ValueError(f"Unsupported distribution type: {dist['type']}")


def sample_age_override(species, city, profession, config):
    """
    Samples age using the override approach.
    Checks for an override in a fixed order:
      1. Species override (keys are lower-case)
      2. City override (keys are case-sensitive)
      3. Profession override (keys are lower-case)
    Returns the sampled age if an override exists;
    Otherwise, returns -1.
    """
    overrides = config.get("overrides", {})

    # 1. Check profession override
    # we do this first because some professions have hard limits
    # e.g., the Imperial military might not accept people under (say) 20
    profession_override = overrides.get("profession", {}).get(profession.lower(), {})
    if "age_distribution" in profession_override:
        return sample_from_distribution(profession_override["age_distribution"])

    # 2. Check species override
    species_override = overrides.get("species", {}).get(species.lower(), {})
    if "age_distribution" in species_override:
        return sample_from_distribution(species_override["age_distribution"])

    # 3. Check city override
    city_override = overrides.get("city", {}).get(city, {})
    if "age_distribution" in city_override:
        return sample_from_distribution(city_override["age_distribution"])

    # No override found
    return -1


def sample_age_factor(species, city, profession, config):
    """
    Samples age using a factor-graph approach.
    Starts with the default age_distribution (top-level) and applies
    cumulative adjustments from factors stored under:
      - "species_age"  (keys expected to be lower-case)
      - "city_age"     (keys are case-sensitive)
      - "profession_age" (keys expected to be lower-case)
    Each factor adjusts the default mean (via an additive shift) and
    scales the default std (via a multiplicative factor).
    """
    # Get the base age distribution (top-level)
    base = config.get("age_distribution", {"type": "normal", "mean": 40, "std": 15})
    final_mean = float(base["mean"])
    final_std = float(base["std"])

    # Get top-level factors
    factors = config.get("factors", {})

    # Apply profession_age factor (keys are lower-case)
    prof_factor = factors.get("profession_age", {}).get(profession.lower(), {})
    final_mean += prof_factor.get("mean_shift", 0)
    final_std *= prof_factor.get("std_mult", 1.0)


    # Apply species_age factor (keys are lower-case)
    sp_factor = factors.get("species_age", {}).get(species.lower(), {})
    final_mean += sp_factor.get("mean_shift", 0)
    final_std *= sp_factor.get("std_mult", 1.0)

    # Apply city_age factor
    city_factor = factors.get("city_age", {}).get(city, {})
    final_mean += city_factor.get("mean_shift", 0)
    final_std *= city_factor.get("std_mult", 1.0)

    # Sample using the adjusted parameters
    return abs(int(random.gauss(final_mean, final_std)))


def sample_age(species, city, profession, config):
    """
    Wrapper function to sample age:
      1. Calls sample_age_override; if an override exists, its value is returned.
      2. If no override is found (i.e. override returns -1), falls back to sample_age_factor.
    """
    age_val = sample_age_override(species, city, profession, config)

    if age_val == -1: # no override present, sample as usual
        age_val = sample_age_factor(species, city, profession, config)
    
    # check for ensuring ages aren't less than 0
    if age_val < 0:
        return 0
    else:
        return age_val
