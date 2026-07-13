class XGBiasCorrection:

    HOME_XG_SUBTRACTION = 0.15
    AWAY_XG_ADDITION = 0.05

    MINIMUM_CORRECTED_XG = 0.20
    MAXIMUM_CORRECTED_XG = 4.50

    @staticmethod
    def clamp(
        value: float,
        minimum: float,
        maximum: float,
    ) -> float:

        return max(
            minimum,
            min(
                float(value),
                maximum,
            ),
        )

    @classmethod
    def apply(
        cls,
        home_xg: float,
        away_xg: float,
    ) -> tuple[float, float]:

        corrected_home_xg = cls.clamp(
            float(home_xg)
            - cls.HOME_XG_SUBTRACTION,
            cls.MINIMUM_CORRECTED_XG,
            cls.MAXIMUM_CORRECTED_XG,
        )

        corrected_away_xg = cls.clamp(
            float(away_xg)
            + cls.AWAY_XG_ADDITION,
            cls.MINIMUM_CORRECTED_XG,
            cls.MAXIMUM_CORRECTED_XG,
        )

        return (
            corrected_home_xg,
            corrected_away_xg,
        )
