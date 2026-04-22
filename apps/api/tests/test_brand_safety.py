from app.services.brand_safety import check_product


def test_flags_real_money_gaming() -> None:
    report = check_product(
        product_name="RummyKing",
        product_description="Win real cash playing rummy online",
    )
    assert not report.ok
    assert "real_money_gaming" in report.flags


def test_clean_product_passes() -> None:
    report = check_product(
        product_name="Acme Coffee",
        product_description="Freshly roasted coffee beans shipped weekly",
    )
    assert report.ok
    assert report.flags == []
