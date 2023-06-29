from __future__ import annotations

import dataclasses
from typing import Any, Dict, List, Optional, Type, TypeVar

from chia.consensus.constants import ConsensusConstants
from chia.consensus.default_constants import DEFAULT_CONSTANTS
from chia.types.blockchain_format.coin import Coin
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.util.ints import uint64
from chia.util.streamable import Streamable, streamable


@dataclasses.dataclass(frozen=True)
class CoinSelectionConfig:
    min_coin_amount: uint64
    max_coin_amount: uint64
    excluded_coin_amounts: List[uint64]
    excluded_coin_ids: List[bytes32]

    def to_json_dict(self) -> Dict[str, Any]:
        return CoinSelectionConfigLoader(
            self.min_coin_amount,
            self.max_coin_amount,
            self.excluded_coin_amounts,
            self.excluded_coin_ids,
        ).to_json_dict()


@dataclasses.dataclass(frozen=True)
class TXConfig:
    coin_selection_config: CoinSelectionConfig
    reuse_puzhash: bool

    def to_json_dict(self) -> Dict[str, Any]:
        return TXConfigLoader(
            self.coin_selection_config.min_coin_amount,
            self.coin_selection_config.max_coin_amount,
            self.coin_selection_config.excluded_coin_amounts,
            self.coin_selection_config.excluded_coin_ids,
            self.reuse_puzhash,
        ).to_json_dict()


_T_CoinSelectionConfigLoader = TypeVar("_T_CoinSelectionConfigLoader", bound="CoinSelectionConfigLoader")


@streamable
@dataclasses.dataclass(frozen=True)
class CoinSelectionConfigLoader(Streamable):
    min_coin_amount: Optional[uint64] = None
    max_coin_amount: Optional[uint64] = None
    excluded_coin_amounts: Optional[List[uint64]] = None
    excluded_coin_ids: Optional[List[bytes32]] = None

    def autofill(
        self,
        constants: ConsensusConstants,
    ) -> CoinSelectionConfig:
        return CoinSelectionConfig(
            min_coin_amount=uint64(0) if self.min_coin_amount is None else self.min_coin_amount,
            max_coin_amount=uint64(constants.MAX_COIN_AMOUNT) if self.max_coin_amount is None else self.max_coin_amount,
            excluded_coin_amounts=[] if self.excluded_coin_amounts is None else self.excluded_coin_amounts,
            excluded_coin_ids=[] if self.excluded_coin_ids is None else self.excluded_coin_ids,
        )

    @classmethod
    def from_json_dict(
        cls: Type[_T_CoinSelectionConfigLoader], json_dict: Dict[str, Any]
    ) -> _T_CoinSelectionConfigLoader:
        if "excluded_coins" in json_dict:
            excluded_coins: List[Coin] = [Coin.from_json_dict(c) for c in json_dict["excluded_coins"]]
            excluded_coin_ids: List[str] = [c.name().hex() for c in excluded_coins]
            if "excluded_coin_ids" in json_dict:
                json_dict["excluded_coin_ids"] = [*excluded_coin_ids, *json_dict["excluded_coin_ids"]]
            json_dict["excluded_coin_ids"] = excluded_coin_ids
        return super().from_json_dict(json_dict)


@streamable
@dataclasses.dataclass(frozen=True)
class TXConfigLoader(Streamable):
    min_coin_amount: Optional[uint64] = None
    max_coin_amount: Optional[uint64] = None
    excluded_coin_amounts: Optional[List[uint64]] = None
    excluded_coin_ids: Optional[List[bytes32]] = None
    reuse_puzhash: Optional[bool] = None

    def autofill(
        self,
        config: Dict[str, Any],
        logged_in_fingerprint: int,
        constants: ConsensusConstants,
    ) -> TXConfig:
        if self.reuse_puzhash is None:
            reuse_puzhash_config = config.get("reuse_public_key_for_change", None)
            if reuse_puzhash_config is None:
                reuse_puzhash = False
            else:
                reuse_puzhash = reuse_puzhash_config.get(str(logged_in_fingerprint), False)

        return TXConfig(
            CoinSelectionConfig(
                min_coin_amount=uint64(0) if self.min_coin_amount is None else self.min_coin_amount,
                max_coin_amount=uint64(constants.MAX_COIN_AMOUNT)
                if self.max_coin_amount is None
                else self.max_coin_amount,
                excluded_coin_amounts=[] if self.excluded_coin_amounts is None else self.excluded_coin_amounts,
                excluded_coin_ids=[] if self.excluded_coin_ids is None else self.excluded_coin_ids,
            ),
            reuse_puzhash=reuse_puzhash,
        )


DEFAULT_COIN_SELECTION_CONFIG = CoinSelectionConfig(uint64(0), uint64(DEFAULT_CONSTANTS.MAX_COIN_AMOUNT), [], [])
DEFAULT_TX_CONFIG = TXConfig(
    DEFAULT_COIN_SELECTION_CONFIG,
    False,
)
