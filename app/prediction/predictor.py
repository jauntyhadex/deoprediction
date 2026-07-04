import random


class MatchPredictor:

    def predict(self, home_team, away_team):

        home_strength = random.uniform(0.35, 0.65)
        away_strength = random.uniform(0.20, 0.55)

        draw_probability = 1 - (home_strength + away_strength)

        if draw_probability < 0:
            draw_probability = 0.10

        total = (
            home_strength +
            away_strength +
            draw_probability
        )

        home_strength /= total
        away_strength /= total
        draw_probability /= total

        predicted_home_score = round(home_strength * 3)
        predicted_away_score = round(away_strength * 3)

        confidence = max(
            home_strength,
            away_strength,
            draw_probability
        )

        return {
            "home_win_probability": round(home_strength, 2),
            "draw_probability": round(draw_probability, 2),
            "away_win_probability": round(away_strength, 2),
            "predicted_home_score": predicted_home_score,
            "predicted_away_score": predicted_away_score,
            "confidence": round(confidence, 2),
        }