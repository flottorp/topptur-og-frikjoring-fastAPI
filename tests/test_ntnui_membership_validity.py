"""
Test that NTNUI validity is derived from the group membership flag

The /groups/{slug}/memberships/ endpoint lists everyone who has ever joined
the group, and exposes two independent fields:

  has_valid_group_membership  - the group membership, renewed per calendar year
  ntnui_contract_expiry_date  - the separate NTNUI-wide contract

Validity must come from the first. The two disagree for a large share of the
members, so reading the contract date both rejects valid members and accepts
members who have left the group.
"""
import asyncio
from datetime import date

from app.services.external_ntnuiAPI import NTNUIAPIClient
from app.services.sync_members import MemberSyncService
from app.models.member import Base

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _membership(phone, group_valid, contract_expiry, first="Test", last="Person"):
    return {
        "phone_number": phone,
        "first_name": first,
        "last_name": last,
        "email": f"{phone}@example.com",
        "has_valid_group_membership": group_valid,
        "ntnui_contract_expiry_date": contract_expiry,
    }


class TestNormalization:
    """normalize_memberships_to_members maps the right field"""

    def setup_method(self):
        self.client = NTNUIAPIClient(api_key="dummy")
        self.year_end = date(date.today().year, 12, 31)

    def test_group_membership_valid_despite_expired_contract(self):
        """The common case: group membership is valid, NTNUI contract has expired"""
        out = self.client.normalize_memberships_to_members(
            [_membership("+4791110001", True, "2020-06-30")]
        )
        assert len(out) == 1
        assert out[0]["ntnui_valid"] is True
        assert out[0]["ntnui_valid_until"] == self.year_end

    def test_no_group_membership_despite_valid_contract(self):
        """Left the group but the NTNUI contract still runs - not a member"""
        out = self.client.normalize_memberships_to_members(
            [_membership("+4791110002", False, "2099-12-31")]
        )
        assert out[0]["ntnui_valid"] is False
        assert out[0]["ntnui_valid_until"] is None

    def test_both_valid(self):
        out = self.client.normalize_memberships_to_members(
            [_membership("+4791110003", True, "2099-12-31")]
        )
        assert out[0]["ntnui_valid"] is True
        assert out[0]["ntnui_valid_until"] == self.year_end

    def test_missing_flag_is_not_valid(self):
        entry = _membership("+4791110004", None, None)
        del entry["has_valid_group_membership"]
        out = self.client.normalize_memberships_to_members([entry])
        assert out[0]["ntnui_valid"] is False

    def test_unparseable_contract_date_does_not_break_normalization(self):
        out = self.client.normalize_memberships_to_members(
            [_membership("+4791110005", True, "ikke-en-dato")]
        )
        assert out[0]["ntnui_valid"] is True

    def test_string_false_is_not_valid(self):
        """NTNUI's schema types the flag as a string; bool("False") would be True"""
        out = self.client.normalize_memberships_to_members(
            [_membership("+4791110006", "False", "2020-01-01")]
        )
        assert out[0]["ntnui_valid"] is False
        assert out[0]["ntnui_valid_until"] is None

    def test_string_true_is_valid(self):
        out = self.client.normalize_memberships_to_members(
            [_membership("+4791110007", "True", "2020-01-01")]
        )
        assert out[0]["ntnui_valid"] is True

    def test_unrecognised_flag_value_is_not_valid(self):
        out = self.client.normalize_memberships_to_members(
            [_membership("+4791110008", 42, "2020-01-01")]
        )
        assert out[0]["ntnui_valid"] is False

    def test_rows_without_phone_are_skipped(self):
        out = self.client.normalize_memberships_to_members(
            [_membership("", True, "2099-12-31")]
        )
        assert out == []


class TestSyncWritesTheFlag:
    """The flag must survive all the way into the database"""

    def setup_method(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        self.db = sessionmaker(bind=engine)()
        self.service = MemberSyncService(self.db)
        self.year_end = date(date.today().year, 12, 31)

        # Group membership valid, NTNUI contract long expired
        self.ntnui_rows = [
            {
                "phone": "+4791110001",
                "first_name": "Ola",
                "last_name": "Nordmann",
                "email": "ola@example.com",
                "ntnui_valid": True,
                "ntnui_valid_until": self.year_end,
            },
            {
                "phone": "+4791110002",
                "first_name": "Kari",
                "last_name": "Nordmann",
                "email": "kari@example.com",
                "ntnui_valid": False,
                "ntnui_valid_until": None,
            },
        ]

    def _stub_clients(self, tf_rows):
        async def fake_ntnui():
            return self.ntnui_rows

        async def fake_tf():
            return tf_rows

        self.service.ntnui_client.get_members = fake_ntnui
        self.service.tf_client.get_members = fake_tf

    def test_sync_from_ntnui_uses_the_flag(self):
        self._stub_clients([])
        result = asyncio.run(self.service.sync_from_ntnui())
        assert result["status"] == "success"

        valid = self.service.get_member_by_id("+4791110001")
        assert valid.ntnui_valid is True
        assert valid.ntnui_valid_until == self.year_end

        invalid = self.service.get_member_by_id("+4791110002")
        assert invalid.ntnui_valid is False

    def test_sync_all_uses_the_flag(self):
        """sync_all is what the daily job runs - it must agree with sync_from_ntnui"""
        self._stub_clients([
            {
                "phone": "+4791110001",
                "first_name": "Ola",
                "last_name": "Nordmann",
                "email": "ola@example.com",
                "tf_valid_until": self.year_end,
            }
        ])
        result = asyncio.run(self.service.sync_all())
        assert result["status"] == "success"

        both = self.service.get_member_by_id("+4791110001")
        assert both.tf_valid is True
        assert both.ntnui_valid is True

        ntnui_only = self.service.get_member_by_id("+4791110002")
        assert ntnui_only.ntnui_valid is False
        assert ntnui_only.tf_valid is False

    def test_sync_all_keeps_tf_only_member_without_ntnui(self):
        """A TF payer who is not in the NTNUI list must not become ntnui_valid"""
        self._stub_clients([
            {
                "phone": "+4799999999",
                "first_name": "Bare",
                "last_name": "TF",
                "email": "bare@example.com",
                "tf_valid_until": self.year_end,
            }
        ])
        asyncio.run(self.service.sync_all())

        m = self.service.get_member_by_id("+4799999999")
        assert m.tf_valid is True
        assert m.ntnui_valid is False
        assert m.ntnui_valid_until is None
