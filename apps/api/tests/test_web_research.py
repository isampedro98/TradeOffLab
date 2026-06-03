from app.services.web_research import _normalize_search_result_url


def test_normalize_search_result_url_extracts_duckduckgo_target() -> None:
    redirect_url = (
        "https://duckduckgo.com/l/?uddg="
        "https%3A%2F%2Flearn.microsoft.com%2Fen-us%2Fwindows-server%2Fvirtualization%2Fhyper-v%2F"
    )

    normalized = _normalize_search_result_url(redirect_url)

    assert normalized == (
        "https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/"
    )
