"""Near duplicate pages with MinHash. Stub owned by Lane B.

Purpose
The same exercise often appears in a textbook, lecture notes and past exams. Mark copies so the
index does not return the same text three times. The quality gate blocks a candidate whose
duplicate rate is above the threshold in PlatformSettings.

Input
The pages of the current run keyed by document version and page number, plus the MinHash
signatures of pages already in the corpus.

Output
A mapping from a duplicate page key to the key of the page it copies. W5 stores that key in
PageFlags.dup_of.

What to build
datasketch MinHash over word shingles with an LSH index, a Jaccard threshold around 0.9.
Persist signatures so later runs compare against the whole corpus, for example as a column in a
new Iceberg table owned by this worker.

How to test
Two pages that differ by one word are duplicates, two unrelated pages are not.
"""

PageKey = tuple[str, int]


def find_duplicates(pages: dict[PageKey, str]) -> dict[PageKey, PageKey]:
    raise NotImplementedError("dedupe is not written yet")
