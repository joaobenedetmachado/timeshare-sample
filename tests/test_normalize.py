import unittest

from src.extract import published_place, published_resorts
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


if __name__ == "__main__":
    unittest.main()
