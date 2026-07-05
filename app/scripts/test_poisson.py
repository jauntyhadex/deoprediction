from app.prediction.probability import ProbabilityPredictor

print(
    ProbabilityPredictor.match_probabilities(
        1.8,
        1.1,
    )
)

print(
    ProbabilityPredictor.btts_probability(
        1.8,
        1.1,
    )
)

print(
    ProbabilityPredictor.over_under(
        1.8,
        1.1,
    )
)