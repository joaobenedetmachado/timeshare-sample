import unittest

from src.deduplicate import deduplicate
from src.extract import published_place, published_resorts
from src.models import Record
from src.normalize import normalize_address, normalize_phone, normalize_resort
from src.validate import normalize_record, validate


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


class PipelineTests(unittest.TestCase):
    def test_duplicate_contact_at_same_resort_collapses(self) -> None:
        sparse = Record(
            name="Pinnacle Vacations",
            phone_number="+18004855632",
            resort="Mountain Loft",
            source="Pinnacle Vacations",
            source_url="https://example.test/a",
            collected_at="2026-10-02T00:00:00Z",
            contact_type="company",
        )
        richer = Record(
            name="Pinnacle Vacations",
            phone_number="+18004855632",
            address="4600 Summerlin Road, Fort Myers, FL 33919",
            resort="Mountain Loft",
            source="Pinnacle Vacations",
            source_url="https://example.test/b",
            collected_at="2026-10-02T00:00:00Z",
            contact_type="company",
        )
        kept = deduplicate([sparse, richer])
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0].address, richer.address)

    def test_same_phone_at_different_resorts_is_kept(self) -> None:
        first = Record(
            name="SellMyTimeshareNow",
            phone_number="+18552993829",
            resort="Star Island Resort and Club",
            source="SellMyTimeshareNow",
            source_url="https://example.test/1",
            collected_at="2026-10-02T00:00:00Z",
            contact_type="company",
        )
        second = Record(
            name="SellMyTimeshareNow",
            phone_number="+18552993829",
            resort="Christie Lodge",
            source="SellMyTimeshareNow",
            source_url="https://example.test/2",
            collected_at="2026-10-02T00:00:00Z",
            contact_type="company",
        )
        self.assertEqual(len(deduplicate([first, second])), 2)

    def test_empty_record_is_rejected(self) -> None:
        record = normalize_record(
            Record(
                source="RedWeek",
                source_url="https://www.redweek.com/timeshare-companies/hgvc",
                collected_at="2026-10-02T00:00:00Z",
                contact_type="unknown",
            )
        )
        self.assertEqual(validate([record]), [])

    def test_sale_by_owner_label_does_not_change_contact_type(self) -> None:
        record = normalize_record(
            Record(
                name="SellMyTimeshareNow",
                phone_number="1-855-299-3829",
                resort="Hilton Grand Vacations Club on the Boulevard",
                source="SellMyTimeshareNow",
                source_url="https://www.sellmytimesharenow.com/timeshares/index/content/details/AdNumber/1/sale/",
                collected_at="2026-10-02T00:00:00Z",
                contact_type="company",
            )
        )
        self.assertEqual(record.contact_type, "company")
        self.assertEqual(record.phone_number, "+18552993829")
        self.assertNotEqual(record.contact_type, "owner")


if __name__ == "__main__":
    unittest.main()
