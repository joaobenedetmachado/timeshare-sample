import unittest

from bs4 import BeautifulSoup

from src.collectors.ltrba import _profile_fields
from src.collectors.smtn import _listing_address
from src.extract import (
    address_from_page_text,
    combine_resorts,
    member_place,
    published_brand_list,
    published_place,
    published_resorts,
)
from src.normalize import normalize_address, normalize_phone, normalize_resort


class NormalizeTests(unittest.TestCase):
    def test_us_phone_and_extension(self) -> None:
        self.assertEqual(normalize_phone("970-453-1226 x4"), "+19704531226 x4")
        self.assertEqual(normalize_phone("1-877-815-4227"), "+18778154227")
        self.assertEqual(normalize_phone("800.485.5632"), "+18004855632")

    def test_text_prefix_and_second_number(self) -> None:
        self.assertEqual(normalize_phone("or Text 801-661-1763"), "+18016611763")
        self.assertEqual(
            normalize_phone("+44 (0) 20 32 90 90 32 or +34 952 886 340"),
            "+442032909032",
        )

    def test_uk_trunk_zero(self) -> None:
        self.assertEqual(normalize_phone("(+44) 01784 451355"), "+441784451355")

    def test_incomplete_phone_is_left_empty(self) -> None:
        self.assertEqual(normalize_phone("ext 4"), "")
        self.assertEqual(normalize_phone(""), "")

    def test_resort_title_case_only_when_shouted(self) -> None:
        self.assertEqual(normalize_resort("MOUNTAIN LOFT"), "Mountain Loft")
        self.assertEqual(normalize_resort("EILAN HOTEL AND SPA"), "Eilan Hotel and Spa")
        self.assertEqual(
            normalize_resort("Hilton Grand Vacations Club on the Boulevard"),
            "Hilton Grand Vacations Club on the Boulevard",
        )

    def test_published_resort_and_place_come_from_the_text(self) -> None:
        bio = (
            "I specialize in Marriott Vacation Club weeks as well as "
            "Breckenridge Grand Vacations, Westin and Hilton."
        )
        self.assertIn("Marriott Vacation Club", published_resorts(bio))
        self.assertIn("Breckenridge Grand Vacations", published_resorts(bio))
        place = published_place(
            "I'm a licensed broker in Orlando, Florida.",
            "",
        )
        self.assertEqual(place, "Orlando, Florida")
        self.assertEqual(
            published_place("Our office is located at the Lahaina Cannery Mall in Maui and we are open.", ""),
            "Lahaina Cannery Mall in Maui",
        )
        raw = "4600 Summerlin Road, Suite C-2, Box 277 • Fort Myers, FL 33919"
        self.assertEqual(
            normalize_address(raw),
            "4600 Summerlin Road, Suite C-2, Box 277, Fort Myers, FL 33919",
        )
        self.assertEqual(
            normalize_address("80 East Harmon Avenue, Las Vegas, Nevada, Outside US"),
            "80 East Harmon Avenue, Las Vegas, Nevada",
        )

    def test_markets_and_resort_cities_are_not_an_address(self) -> None:
        self.assertEqual(
            published_place(
                "I am always in need of timeshares in ski locations like Utah, Colorado, and California.",
                "",
            ),
            "",
        )
        self.assertEqual(
            published_place(
                "TRI West specializes in Four Seasons Residence Clubs at Aviara in Carlsbad CA.",
                "",
            ),
            "",
        )
        self.assertEqual(member_place("Oceanside", "CA", "USA"), "Oceanside, CA")
        self.assertEqual(member_place("Reno", "Offices: CA and NV", "USA"), "Reno")
        self.assertEqual(member_place("", "OK", "USA"), "")
        self.assertEqual(
            member_place("Staines Upon Thames", "Surrey", "United Kingdom"),
            "Staines Upon Thames, Surrey, United Kingdom",
        )

    def test_profile_city_is_kept_when_the_bio_names_a_resort_city(self) -> None:
        html = """
        <input placeholder="City" value="Oceanside"/>
        <input placeholder="State" value="CA"/>
        <input placeholder="Country" value="USA"/>
        <textarea placeholder="Biography">Exclusive broker for Four Seasons Residence Clubs at Aviara in Carlsbad CA.</textarea>
        <textarea placeholder="Timeshare Brands">Marriott
Hilton</textarea>
        """
        fields = _profile_fields(html)
        self.assertEqual(
            member_place(fields["city"], fields["state"], fields["country"]),
            "Oceanside, CA",
        )
        resorts = combine_resorts(
            published_brand_list(fields["brands"]),
            published_resorts(fields["biography"]),
        )
        self.assertIn("Marriott", resorts)
        self.assertIn("Four Seasons Residence Clubs at Aviara", resorts)

    def test_shouted_brand_is_kept_and_old_job_is_not(self) -> None:
        self.assertIn("Marriott", published_resorts("Specializing in MARRIOTT Vacations Worldwide."))
        bio = (
            "I joined the sales team at Sunterra Pacific (now Vacation Internationale) in 1997. "
            "We currently own WorldMark and Club Wyndham."
        )
        resorts = published_resorts(bio)
        self.assertNotIn("Sunterra", resorts)
        self.assertNotIn("and Club", resorts)
        self.assertIn("WorldMark", resorts)
        self.assertIn("Club Wyndham", resorts)
        shouted = published_resorts(
            "WORLDMARK THE CLUB (WORLDMARK BY WYNDHAM) VACATION INTERNATIONALE CLUB WYNDHAM"
        )
        self.assertIn("WorldMark the Club", shouted)
        self.assertNotIn("BY", shouted)

    def test_postal_address_beats_license_states(self) -> None:
        page = (
            "Utah License Number: 5475527. Nevada License Number: B 1001059. "
            "The physical address is 3423 Stanton Drive, Salt Lake City, Utah, 84120."
        )
        self.assertEqual(
            address_from_page_text(page),
            "3423 Stanton Drive, Salt Lake City, Utah 84120",
        )

    def test_marketplace_country_bucket_is_dropped(self) -> None:
        html = '<div class="location">L.G. Smith Boulevard 99, Palm Beach, Outside US</div>'
        self.assertEqual(
            _listing_address(BeautifulSoup(html, "html.parser")),
            "L.G. Smith Boulevard 99, Palm Beach",
        )


if __name__ == "__main__":
    unittest.main()
