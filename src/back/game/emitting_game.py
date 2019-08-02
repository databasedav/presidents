from typing import Callable, Dict, List, Optional, Set, Union, Iterable

from bidict import bidict
from socketio import AsyncServer

import asyncio

# from ..server.server import Server
Server = None

from . import (
    Hand,
    DuplicateCardError,
    FullHandError,
    CardNotInChamberError,
    EmittingChamber,
    Game,
    base_hand,
    PresidentsError,
)

from datetime import datetime

from ..data.stream.records import HandPlay
from ..data.stream.agents import hand_play_agent

# TODO: decide what to do for the removal of asking options
# TODO: spectators should get a completely hidden view of the game being
#       played and maybe if you are friends with another player, you can
#       see that player's cards and stuff like that

class EmittingGame(Game):
    def __init__(self, server: Server, **kwargs):
        super().__init__(**kwargs)
        # TODO: server stuff (including emitting should be entirely handled by the Server, which is an AsyncNamespace)
        self._server: Server = server
        assert self._server is None
        self._chambers: List[Optional[EmittingChamber]] = [
            EmittingChamber(self._server) for _ in range(4)
        ]
        self._server: Optional[str] = None
        self._spot_sid_bidict: bidict = bidict()
        self.sid_user_id_dict: Dict[str, str] = dict()
        self.num_spectators: int = 0  # TODO

    # properties

    @property
    def _current_player_sid(self) -> str:
        return self._get_sid(self._current_player)

    # setup related methods

    def set_server(self, server: str) -> None:
        self._server = server

    async def add_player(self, sid: str, name: str) -> None:
        rand_open_spot: int = self._rand_open_spot()
        self._chambers[rand_open_spot].set_sid(sid)
        self._spot_sid_bidict.inv[sid] = rand_open_spot
        await self._set_name(rand_open_spot, name)
        self.num_players += 1

    def remove_player(self, sid: str) -> None:
        self._spot_sid_bidict.inv.pop(sid)
        super().remove_player(self._get_spot(sid))

    async def _deal_cards(self, deck: Optional[List[Iterable[int]]] = None) -> None:
        '''
        Deals cards to all players.
        '''
        await asyncio.gather(*[self._deal_cards_indiv(spot, sid, cards) for (spot, sid), cards in zip(self._spot_sid_bidict.items(), deck or self._make_shuffled_deck())])

    async def _deal_cards_indiv(self, spot: str, sid: str, cards: Iterable[int]):
        '''
        Deals cards to a single player; for utilizing concurrency with
        asyncio.gather.
        '''
        chamber = self._chambers[spot]
        await chamber.reset()
        chamber.set_sid(sid)
        await chamber.add_cards(cards)
        await self._emit("set_spot", {"spot": spot}, sid)

    # game flow related methods

    async def _start_round(
        self, *, deck: Optional[List[Iterable[int]]] = None
    ) -> None:
        assert self.num_players == 4, "four players required to start round"
        await self._deal_cards(deck=deck)
        self._make_and_set_turn_manager()
        self._num_consecutive_rounds += 1
        self._message(f"🏁 round {self._num_consecutive_rounds} has begun")
        await self._next_player()

    async def _next_player(self) -> None:
        try:  # current player is no longer on turn
            await self._emit_to_players(
                "set_on_turn",
                {"on_turn": False, "spot": self._current_player, "time": 0},
            )
        except KeyError:  # self._current_player is None (round start)
            pass
        super()._next_player(timer=False)
        await self._emit_set_on_turn_handler()

    async def _emit_set_on_turn_handler(self):
        """
        handles callback timer for player whose turn it is and updates
        other players' views of that timer as well

        TODO: clean
        """
        time: int = 2
        self._set_dot_color(self._current_player, "green")
        await self._emit(
            "set_on_turn",
            {
                "on_turn": True,
                "spot": self._current_player,
                "time": time * 1000,
            },
            self._current_player_sid,
            callback=lambda: self._start_timer(self._current_player, time),
        )
        await self._emit_to_players(
            "set_time",
            {"spot": self._current_player, "time": time * 1000},
            skip_sid=self._current_player_sid,
        )

    def _player_finish(self, spot: int) -> None:
        self._set_dot_color(spot, "purple")
        super()._player_finish(spot)

    # card management related methods

    async def add_or_remove_card(self, sid: str, card: int) -> None:
        spot: int = self._get_spot(sid)
        try:
            super().add_or_remove_card(spot, card)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    # TODO
    def store_hand(self, spot: int) -> None:
        # super().store_hand(spot)
        # await self._emit(...)
        ...

    # playing and passing related methods

    async def maybe_unlock_play(self, spot: int, sid: str) -> None:
        try:
            super().maybe_unlock_play(spot)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def maybe_play_current_hand(
        self, sid: str, timestamp: datetime
    ) -> None:
        spot: int = self._get_spot(sid)
        try:
            super().maybe_play_current_hand(spot, sid=sid, timestamp=timestamp)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def _play_current_hand(self, spot, **kwargs):
        hand: Hand = super()._play_current_hand(spot, handle_post=False)
        await hand_play_agent.send(
            HandPlay(
                hand_hash=hash(hand),
                sid=kwargs.get("sid"),
                timestamp=kwargs.get("timestamp"),
            )
        )
        self._set_dot_color(spot, "blue")
        for other_spot in self._get_other_spots(spot, exclude_finished=True):
            self._set_dot_color(other_spot, "red")
        await self._emit_to_players(
            "set_cards_remaining",
            {"spot": spot, "cards_remaining": self._chambers[spot].num_cards},
        )
        self._post_play_handler(spot)

    async def maybe_unlock_pass_turn(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        try:
            super().maybe_unlock_pass_turn(spot)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def _unlock_pass(self, spot: int) -> None:
        super()._unlock_pass(spot)
        await self._emit(
            "set_pass_unlocked", {"pass_unlocked": True}, self._get_sid(spot)
        )

    async def _lock_pass(self, spot: int) -> None:
        super()._lock_pass(spot)
        await self._emit(
            "set_pass_unlocked", {"pass_unlocked": False}, self._get_sid(spot)
        )

    async def maybe_pass_turn(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        try:
            super().maybe_pass_turn(spot)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    def _pass_turn(self, spot):
        super()._pass_turn(spot, handle_post=False)
        self._set_dot_color(spot, "yellow")
        self._post_pass_handler()

    async def _clear_hand_in_play(self) -> None:
        super()._clear_hand_in_play()
        await self._emit_to_players("clear_hand_in_play", {})

    # trading related methods

    async def _initiate_trading(self) -> None:
        super()._initiate_trading()
        for spot in range(4):
            self._set_dot_color(spot, "red")
        await self._emit_to_players("set_on_turn", {"on_turn": False})

    async def set_selected_asking_option(self, sid: str, value: int) -> None:
        spot: int = self._get_spot(sid)
        try:
            super().set_selected_asking_option(spot, value)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def maybe_unlock_ask(self, spot: int, sid: str) -> None:
        try:
            super().maybe_unlock_ask(spot)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def ask_for_card(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        try:
            super().ask_for_card(spot)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def _select_asking_option(self, spot: int, value: int) -> None:
        super()._select_asking_option(spot, value)
        await self._emit(
            "select_asking_option", {"value": value}, self._get_sid(spot)
        )

    async def _deselect_asking_option(self, spot: int, value: int) -> None:
        super()._deselect_asking_option(spot, value)
        await self._emit(
            "deselect_asking_option", {"value": value}, self._get_sid(spot)
        )

    async def maybe_unlock_give(self, spot: int, sid: str) -> None:
        try:
            super().maybe_unlock_give(spot)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def give_card(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        try:
            super().give_card(spot)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def _set_giving_options(
        self, spot: int, giving_options: Set[int]
    ) -> None:
        super()._set_giving_options(spot, giving_options)
        await self._emit(
            "set_giving_options",
            {"options": list(giving_options), "highlight": True},
            self._get_sid(spot),
        )

    async def _clear_giving_options(self, spot: int) -> None:
        await self._emit(
            "set_giving_options",
            {"options": list(self._giving_options[spot]), "highlight": False},
            self._get_sid(spot),
        )
        super()._clear_giving_options(spot)

    # misc

    async def unlock_handler(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        if self.trading:
            if self._is_asking(spot):
                self.maybe_unlock_ask(spot, sid)
            elif self._is_giving(spot):
                self.maybe_unlock_give(spot, sid)
            else:
                await self._emit_alert(
                    "you must select something before attempting to unlock",
                    sid,
                )
        else:
            self.maybe_unlock_play(spot, sid)

    def lock_handler(self, sid: str) -> None:
        self.lock(self._get_spot(sid))

    async def _unlock(self, spot: int) -> None:
        super()._unlock(spot)
        await self._emit(
            "set_unlocked", {"unlocked": True}, self._get_sid(spot)
        )

    async def lock(self, spot: int) -> None:
        super().lock(spot)
        await self._emit(
            "set_unlocked", {"unlocked": False}, self._get_sid(spot)
        )

    async def _message(self, message: str) -> None:
        super()._message(message)
        await self._emit_to_server("message", {"message": message})

    # getters

    def _get_sid(self, spot: int) -> str:
        return self._spot_sid_bidict[spot]

    def _get_spot(self, sid: str) -> int:
        return self._spot_sid_bidict.inv[sid]

    def get_user_id(self, sid: str) -> str:
        return self.sid_user_id_dict[sid]

    # setters

    async def _set_name(self, spot: int, name: str) -> None:
        self._names[spot] = name
        await self._emit_to_players("set_names", {"names": self._names})

    async def _set_hand_in_play(self, hand: Hand) -> None:
        super()._set_hand_in_play(hand)
        await self._emit_to_players(
            "set_hand_in_play",
            {
                "hand_in_play": hand.to_list(),
                "hand_in_play_desc": hand.id_desc,
            },
        )

    async def _set_asker(
        self, spot: int, asker: bool, takes_and_gives: int
    ) -> None:
        super()._set_asker(spot, asker, takes_and_gives)
        await self._emit("set_asker", {"asker": asker}, self._get_sid(spot))

    async def _set_trading(self, trading: bool) -> None:
        super()._set_trading(trading)
        await self._emit_to_server("set_trading", {"trading": trading})

    async def _set_giver(self, spot: int, giver: bool) -> None:
        await self._emit("set_giver", {"giver": giver}, self._get_sid(spot))

    async def _set_takes_remaining(
        self, spot: int, takes_remaining: int
    ) -> None:
        super()._set_takes_remaining(spot, takes_remaining)
        await self._emit(
            "set_takes_remaining",
            {"takes_remaining": takes_remaining},
            self._get_sid(spot),
        )

    async def _set_gives_remaining(
        self, spot: int, gives_remaining: int
    ) -> None:
        super()._set_gives_remaining(spot, gives_remaining)
        await self._emit(
            "set_gives_remaining",
            {"gives_remaining": gives_remaining},
            self._get_sid(spot),
        )

    def _add_to_already_asked(self, spot: int, value: int) -> None:
        super()._add_to_already_asked(spot, value)
        # await self._emit('remove_asking_option', {'value': value}, self._get_sid(spot))

    async def _set_dot_color(self, spot: int, dot_color: str) -> None:
        await self._emit_to_players(
            "set_dot_color", {"spot": spot, "dot_color": dot_color}
        )

    async def _set_vice_asshole(self, spot):
        await self._emit_to_players(
            "set_on_turn", {"on_turn": False, "spot": spot, "time": 0}
        )
        super()._set_vice_asshole(spot)

    # emitters

    async def _emit(self, *args, **kwargs) -> None:
        await self._server.emit(*args, **kwargs)

    async def _emit_to_players(self, *args, **kwargs):
        '''
        Emits to all players by default. Pass in skip_sid with a string
        or a list to skip players.

        The difference between this and _emit_to_server is that the
        latter emits to spectators as well.
        '''
        maybe_skip_sid = kwargs.get('skip_sid')
        if not maybe_skip_sid:
            await asyncio.gather(*[self._emit(*args, room=sid, **kwargs) for sid in self._spot_sid_bidict.values()])
        elif isinstance(maybe_skip_sid, str):
            await asyncio.gather(*[self._emit(*args, room=sid, **kwargs) for sid in self._spot_sid_bidict.values() if sid != maybe_skip_sid])
        elif isinstance(maybe_skip_sid, list):
            await asyncio.gather(*[self._emit(*args, room=sid, **kwargs) for sid in self._spot_sid_bidict.values() if sid not in maybe_skip_sid])
        else:
            raise AssertionError('skip_sid can only be a string or a list')

    async def _emit_to_server(self, *args, **kwargs):
        await self._emit(*args, **kwargs)

    # alerting related methods

    async def _emit_alert(self, alert, sid: str) -> None:
        await self._emit("alert", {"alert": alert}, room=sid)
