"""Near duplicate pages with MinHash.

Purpose
The same exercise often appears in a textbook, lecture notes and past exams. Mark copies so the
index does not return the same text three times. The quality gate blocks a candidate whose
duplicate rate is above the threshold in PlatformSettings.

Input
The pages of the current run keyed by document version and page number, plus the MinHash
signatures of pages already in the knowledge base.

Output
A mapping from a duplicate page key to the key of the page it copies. W5 stores that key in
PageFlags.dup_of.

What to build
datasketch MinHash over word shingles with an LSH index, a Jaccard threshold around 0.8.
Persist signatures so later runs compare against the whole knowledge base, for example in a new
table of the ingest schema owned by this worker, added with a platform migration.

How to test
Two pages that differ by one word are duplicates, two unrelated pages are not.
"""

from datasketch import MinHash, MinHashLSH

PageKey = tuple[str, int]

_NUM_PERMUTATIONS = 128
_JACCARD_THRESHOLD = 0.8


def _shingles(text: str) -> list[str]:
    """Word level shingles for MinHash signature."""
    return text.lower().split()


def _signature(text: str) -> MinHash:
    """Build a MinHash signature for text over its word shingles."""
    m = MinHash(num_perm=_NUM_PERMUTATIONS)
    for shingle in _shingles(text):
        if shingle:
            m.update(shingle.encode("utf-8"))
    return m


def find_duplicates(pages: dict[PageKey, str]) -> dict[PageKey, PageKey]:
    """Map each near duplicate page key to the first page that preceded it."""
    if len(pages) <= 1:
        return {}
    lsh = MinHashLSH(threshold=_JACCARD_THRESHOLD, num_perm=_NUM_PERMUTATIONS)
    found: dict[PageKey, PageKey] = {}
    for key in sorted(pages):
        sig = _signature(pages[key])
        near = lsh.query(sig)
        if near:
            found[key] = sorted(near)[0]
        lsh.insert(key, sig)
    return found
