import unittest

from src.deduplicate import deduplicate
from src.models import Record
from src.validate import normalize_record, validate


class DeduplicateTests(unittest.TestCase):
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
