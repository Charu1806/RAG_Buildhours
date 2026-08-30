"""Hard-locked corpus: the five Groww URLs from the architecture. Nothing else."""

from __future__ import annotations

from typing import TypedDict


class FundPage(TypedDict):
    fund_name: str
    source_url: str
    slug: str


CORPUS: tuple[FundPage, ...] = (
    {
        "fund_name": "HDFC Large Cap Fund Direct Growth",
        "source_url": "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
        "slug": "hdfc-large-cap-fund-direct-growth",
    },
    {
        "fund_name": "HDFC Flexi Cap Fund Direct Growth",
        "source_url": "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
        "slug": "hdfc-equity-fund-direct-growth",
    },
    {
        "fund_name": "HDFC ELSS Tax Saver Fund Direct Plan Growth",
        "source_url": "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
        "slug": "hdfc-elss-tax-saver-fund-direct-plan-growth",
    },
    {
        "fund_name": "HDFC Small Cap Fund Direct Growth",
        "source_url": "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
        "slug": "hdfc-small-cap-fund-direct-growth",
    },
    {
        "fund_name": "HDFC Balanced Advantage Fund Direct Growth",
        "source_url": "https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth",
        "slug": "hdfc-balanced-advantage-fund-direct-growth",
    },
)

ALLOWED_URLS = frozenset(page["source_url"] for page in CORPUS)


def allowed_url(url: str) -> bool:
    return url in ALLOWED_URLS
