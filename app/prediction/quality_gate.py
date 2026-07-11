class PredictionQualityGate:

    MINIMUM_CONFIDENCE = 45.0

    @staticmethod
    def passes(prediction) -> bool:

        if prediction is None:
            return False

        confidence = float(
            prediction.confidence or 0
        )

        return (
            confidence
            >= PredictionQualityGate.MINIMUM_CONFIDENCE
        )