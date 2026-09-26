from typing import Annotated, Literal
from pydantic import Field
from packages.contracts.models import Record


class ChatInput(Record):
    utterance: Annotated[str, Field(min_length=1, max_length=2000)]
    amount_brl: Annotated[str, Field(pattern=r"^(0|[1-9][0-9]{0,9})([.,][0-9]{1,2})?$")]
    consent_to_analysis: bool
    demo_case: Literal["standard", "denied", "crisis"] = "standard"

    def amount_cents(self):
        whole, _, fraction = self.amount_brl.replace(",", ".").partition(".")
        return int(whole) * 100 + int((fraction + "00")[:2])
