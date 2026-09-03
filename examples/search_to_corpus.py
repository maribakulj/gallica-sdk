from gallica import Gallica

QUERY = 'gallica all "Verdun"'

with Gallica() as gallica:
    page = gallica.search(QUERY, maximum_records=10)
    page.write_jsonl("./output/verdun-page.jsonl")

    report = gallica.corpus(page.arks).fetch(
        "./output/verdun-corpus",
        metadata=True,
        text=False,
        resume=True,
    )

print(f"success={len(report.successes)} failures={len(report.failures)} skipped={len(report.skipped)}")
