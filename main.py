import re
import csv
import unicodedata
from requests import get
from bs4 import BeautifulSoup as bs


def create_link(path: str) -> str:
    """
    Build a full URL from a relative path.

    Args:
        path (str): Relative path such as "ps3?xjazyk=CZ".

    Returns:
        str: Full constructed URL.
    """
    return f"https://www.volby.cz/pls/ps2017nss/{path}"


def get_parsed_response(url: str) -> bs:
    """
    Takes an url and returns parsed HTML .

    Args:
        url (str): Page URL.

    Returns:
        BeautifulSoup: Parsed HTML.
    """
    html = bs(get(url).text, features="html.parser")
    return html


def parse_regions(html: bs) -> tuple[list[str], list[str]]:
    """
    Parses region links (hrefs) and region names.

    Args:
        html (BeautifulSoup): Parsed HTML.

    Returns:
        Tuple[List[str], List[str]]:
            - href list for regions
            - region names
    """
    td_region_links = html.find_all("td", {"headers": re.compile(r"t.+sa3")})
    td_region_names = html.find_all("td", {"headers": re.compile(r"t.+sa1\s+t.+sb2")})
    region_hrefs = [a["href"] for td in td_region_links for a in td.find_all("a")]
    region_names = [td.text for td in td_region_names]
    return region_hrefs, region_names


def parse_municipalities(html: bs) -> tuple[list[str], list[str], list[str]]:
    """
    Parses municipalities for a region.

    Args:
        html (BeautifulSoup): Parsed HTML.

    Returns:
        Tuple[list[str], list[str], list[str]]:
            - municipality hrefs
            - municipality IDs
            - municipality names
    """
    td_municipality_number = html.find_all("td", {"class": "cislo"})
    td_municipality_name = html.find_all("td", {"class": "overflow_name"})
    municipality_hrefs = [
        a["href"] for td in td_municipality_number for a in td.find_all("a")
    ]
    municipality_ids = [
        a.text for td in td_municipality_number for a in td.find_all("a")
    ]
    municipality_names = [td.text for td in td_municipality_name]
    return municipality_hrefs, municipality_ids, municipality_names


def parse_results(html: bs) -> tuple[list[str], list[str], list[str], dict[str, str]]:
    """
    Parses election results for a municipality from html.

    Args:
        html (BeautifulSoup): Parsed HTML of a municipality page.

    Returns:
        Tuple[List[str], List[str], List[str], Dict[str, str]]:
            - registered voters
            - envelopes
            - valid votes
            - dict {party: votes}
    """

    td_registered_voters = html.find_all("td", {"headers": "sa2"})
    td_envelopes = html.find_all("td", {"headers": "sa3"})
    td_valid_votes = html.find_all("td", {"headers": "sa6"})
    td_parties = html.find_all("td", {"class": "overflow_name"})
    td_votes = html.find_all("td", {"headers": re.compile(r"t[12]sa2\s+t[12]sb3")})
    registered_voters = [td.text for td in td_registered_voters]
    envelopes = [td.text for td in td_envelopes]
    valid_votes = [td.text for td in td_valid_votes]
    parties = [td.text for td in td_parties]
    votes = [td.text for td in td_votes]

    return (
        registered_voters,
        envelopes,
        valid_votes,
        {party: vote for party, vote in zip(parties, votes)},
    )


def slugify(name: str) -> str:
    """

    Convert a string into a "slug" suitable for filenames or URLs.

    The function removes diacritics, converts the string to lowercase,
    and replaces spaces with underscores.

    Args:
        name (str): The input string, e.g., a region or municipality name.

    Returns:
        str: A slugified version of the input, e.g., "Ústí nad Labem" -> "usti_nad_labem".

    """
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return name.lower().replace(" ", "_")


def write_municipality_csv(
    region_name: str, all_parties: list[str], rows: list[list[str]]
) -> str:
    """
    Creates CSV for a region with all municipalities.

    Args:
        region_name (str): Region name.
        all_parties (list[str]): List of all parties in region.
        rows (list[list[str]]): Final data rows.

    Returns:
        str: Output filename.
    """

    header = [
        "id",
        "location",
        "registered voters",
        "envelopes",
        "valid votes",
    ] + all_parties

    filename = f"vysledky_{slugify(region_name)}.csv"

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(header)
        csv_writer.writerows(rows)
    return filename


def main() -> None:
    """
    Download complete election results:
    - all regions
    - all municipalities in each region
    - save each region as a separate CSV
    """
    basic_href = "ps3?xjazyk=CZ"
    start_url = create_link(basic_href)
    html = get_parsed_response(start_url)

    region_hrefs, region_names = parse_regions(html)
    for region_href, region_name in zip(region_hrefs, region_names):

        region_url = create_link(region_href)
        region_html = get_parsed_response(region_url)

        municipality_hrefs, municipality_ids, municipality_names = parse_municipalities(
            region_html
        )

        all_parties_set = set()
        rows = []

        for municipality_id, municipality_name, municipality_href in zip(
            municipality_ids, municipality_names, municipality_hrefs
        ):
            municipality_url = create_link(municipality_href)
            try:
                municipality_html = get_parsed_response(municipality_url)
            except Exception as e:
                print(f"Error loading {municipality_url}: {e}")
                continue

            registered_voters, envelopes, valid_votes, party_votes = parse_results(
                municipality_html
            )

            all_parties_set.update(party_votes.keys())

            row = [
                municipality_id,
                municipality_name,
                registered_voters[0] if registered_voters else "",
                envelopes[0] if envelopes else "",
                valid_votes[0] if valid_votes else "",
            ]
            rows.append((row, party_votes))

        all_parties = sorted(all_parties_set)

        final_rows = []
        for row, party_vote in rows:
            votes = [party_vote.get(party, "0") for party in all_parties]
            final_rows.append(row + votes)

        filename = write_municipality_csv(region_name, all_parties, final_rows)
        print(f"Saved {filename}")


if __name__ == "__main__":
    main()
