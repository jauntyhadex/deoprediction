from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def main() -> None:

    print()
    print(
        "DEOPREDICTION MARKET CATALOG TEST"
    )
    print("=" * 60)

    catalog_response = client.get(
        "/markets/catalog"
    )

    assert (
        catalog_response.status_code
        == 200
    ), catalog_response.text

    catalog = catalog_response.json()

    market_types = catalog.get(
        "market_types",
        [],
    )

    selections = catalog.get(
        "selections",
        [],
    )

    grades = catalog.get(
        "pick_grades",
        [],
    )

    assert market_types
    assert selections
    assert grades

    assert any(
        item["market_type"]
        == "MATCH_RESULT"
        for item in market_types
    )

    assert any(
        item["selection"]
        == "HOME"
        for item in selections
    )

    assert any(
        item["grade"]
        == "A"
        for item in grades
    )

    print(
        "MARKET CATALOG PASSED"
    )

    types_response = client.get(
        "/markets/types"
    )

    assert (
        types_response.status_code
        == 200
    ), types_response.text

    assert types_response.json()[
        "market_types"
    ]

    print(
        "MARKET TYPES PASSED"
    )

    type_detail_response = client.get(
        "/markets/types/MATCH_RESULT"
    )

    assert (
        type_detail_response.status_code
        == 200
    ), type_detail_response.text

    assert (
        type_detail_response.json()[
            "market_type"
        ]["market_type"]
        == "MATCH_RESULT"
    )

    print(
        "MARKET TYPE DETAIL PASSED"
    )

    missing_response = client.get(
        "/markets/types/NOT_A_MARKET"
    )

    assert (
        missing_response.status_code
        == 404
    ), missing_response.text

    print(
        "MARKET TYPE NOT-FOUND PASSED"
    )

    selections_response = client.get(
        "/markets/selections"
    )

    assert (
        selections_response.status_code
        == 200
    ), selections_response.text

    assert selections_response.json()[
        "selections"
    ]

    print(
        "MARKET SELECTIONS PASSED"
    )

    grades_response = client.get(
        "/markets/grades"
    )

    assert (
        grades_response.status_code
        == 200
    ), grades_response.text

    assert grades_response.json()[
        "grades"
    ]

    print(
        "PICK GRADES PASSED"
    )

    public_response = client.get(
        "/markets/catalog"
    )

    assert (
        public_response.status_code
        == 200
    ), public_response.text

    print(
        "PUBLIC MARKET CATALOG ACCESS PASSED"
    )

    print("=" * 60)
    print(
        "MARKET CATALOG TEST PASSED"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
