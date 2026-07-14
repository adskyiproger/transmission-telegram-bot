from models.PostsBrowser import PostsBrowser


def test_post_output_escapes_untrusted_tracker_content():
    browser = PostsBrowser(
        posts=[
            {
                "title": "<b>tracker title</b>",
                "size": "1GB",
                "date": "2026-01-01",
                "seed": "1",
                "leach": "0",
                "info": "javascript:alert(1)",
                "tracker": "<tracker>",
            }
        ]
    )

    page = browser.get_page()

    assert "&lt;b&gt;tracker title&lt;/b&gt;" in page
    assert "javascript:" not in page
    assert "&lt;tracker&gt;" in page
