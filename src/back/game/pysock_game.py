from typing import Callable, Dict, List, Optional, Set, Union, Iterable

from bidict import bidict
from socketio import AsyncServer

from asyncio import gather
import inspect
import re
from time import mktime

from ..game.hand import NotPlayableOnError
from ..utils import spawn_after
from ..services.monitor import HandPlay


# TODO: add indicator for received cards
# TODO: last round positions

from . import (
    Hand,
    DuplicateCardError,
    FullHandError,
    CardNotInChamberError,
    EmittingChamber,
    # Game,
    base_hand,
    PresidentsError,
)
from .gamee import Game

from datetime import datetime

# TODO: decide what to do for the removal of asking options; and whether
#       or not to remove them
# TODO: spectators should get a completely hidden view of the game being
#       played and maybe if you are friends with another player, you can
#       see that player's cards and stuff like that
# TODO: block receiving user events during autoplay
# TODO: block autoplaying while user event is being processed
# TODO: in general, make sure certain state has actually changed before
#       notifying client
# TODO: ok here is what is gna happen: timer will start server side
#       w 0 delay and then the on_turn acks will be stored in the db
#       for analysis, the timer start time will be sent to the front
#       end so it can determine how much time the player actually has
#       the fact that the player will actually have less time to play
#       will be handled by the fact that they have reserve time and
#       also the fact that they should get a better internet connection, bitch
# TODO: normalize emit event names with frontend
# TODO: add UI elements for takes and gives remaining
# TODO: go through all gathers and consider whether doing things
#       concurrently won't break something
# TODO: whenever concurrently emitting same event to multiple spots,
#       randomly decide order, e.g. not just
#       "for sid in spot_sid_bidict.values()"  or "for spot in range(4)"
# TODO: fix idling on phone bug
# TODO: make base game class async and agnostic to event emittal
#       implementation
# TODO: serialize and store full game state at the start of every round
#       and store all major game state changing actions in a round (e.g.
#       this includes valid hand plays but excludes card clicks) so when
#       assertions are failed (or some other unknown bug), reproduction
#       can be attempted without accessing game actions table

class PySockGame(Game):
    """
    Game that emits events using a python-socketio server.
    """
    def __init__(self, *, name: str, sio, agents: dict, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self._sio = sio
        self._events_counter = agents.get('events_counter')
        self._hand_play_processor = agents.get('hand_play_processor')
        self._chambers: List[EmittingChamber] = [
            EmittingChamber(self._sio) for _ in range(4)
        ]
        self._spot_sid_bidict: bidict = bidict()
        self._user_ids: List[str] = [None for _ in range(4)]
        self.num_spectators: int = 0  # TODO

    # properties

    @property
    def _current_player_sid(self) -> str:
        return self._get_sid(self._current_player)

    # setup related methods

    def set_sio(self, sio) -> None:
        self._sio = sio
        for chamber in self._chambers:
            chamber.set_sio(sio)

    async def add_player_to_spot(
        self, name: str, spot: int, sid: str, user_id: str
    ) -> None:
        self._spot_sid_bidict[spot] = sid
        self._chambers[spot].set_sid(sid)
        # sid must be set prior to the emitting done here
        super().add_player_to_spot(name, spot)
        self._user_ids[spot] = user_id

    async def remove_player(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        await super().remove_player(spot)
        self._spot_sid_bidict.pop(spot)
        self._chambers[spot].set_sid(None)
        self._user_ids[spot] = None

    def in_players(self, user_id: str):
        return user_id in self._user_ids
    
    async def _emit_set_spot(self, spot: int) -> None:
        await self._emit('set_spot', {'spot': spot}, room=self._get_sid(spot))

    async def _emit_set_num_cards_remaining(self, spot: int, num_cards_remaining: int) -> None:
        await self._emit_to_players('set_num_cards_remaining', {'spot': spot, 'num_cards_remaining': num_cards_remaining})
    
    async def _emit_set_on_turn(self, spot: int, on_turn: bool) -> None:
        try:
            await self._emit('set_on_turn', {'on_turn': on_turn}, room=self._get_sid(spot))
        except KeyError:  # current player is None at round start
            pass
    
    async def _emit_set_dot_color(self, spot: int, dot_color: str) -> None:
        await self._emit_to_players("set_dot_color", {"spot": spot, "dot_color": dot_color})

    async def _emit_set_on_turn_handler(self, spot: int) -> None:
        await gather(
            self._emit(
                "set_on_turn", {"on_turn": True}, room=self._get_sid(spot)
            ),
            self._set_dot_color(spot, "green"),
        )

    async def _emit_set_time(self, which: str, seconds: float, spot: int) -> None:
        payload = {'which': which, 'time': seconds * 1000}
        if spot:
            payload['spot'] = spot
        await self._emit_to_players('set_time', payload)

    async def _emit_set_timer_state(
        self, which: str, state: bool, spot: int, timestamp: datetime
    ) -> None:
        payload = {
            "which": which,
            "state": state,
        }
        if state:
            # accounts for server/client latency
            payload['timestamp'] = mktime(timestamp.timetuple())
        if spot:
            payload["spot"] = spot
        await self._emit_to_players("set_timer_state", payload)

    async def _emit_set_paused(self, paused: bool) -> None:
        await self._emit_to_players('set_paused', {'paused': paused})

    async def card_handler(self, sid: str, card: int) -> None:
        await super().card_handler(self._get_spot(sid), card)

    async def play_handler(self, sid: str) -> None:
        await super().play_handler(self._get_spot(sid))

    async def unlock_pass_handler(self, sid: str) -> None:
        await super().unlock_pass_handler(self._get_spot(sid))

    async def _emit_set_pass_unlocked(self, spot: int, pass_unlocked: bool) -> None:
        await self._emit(
            "set_pass_unlocked",
            {"pass_unlocked": pass_unlocked},
            room=self._get_sid(spot),
        )

    async def pass_handler(self, sid: str) -> None:
        await super().pass_handler(self._get_spot(sid))

    async def _emit_clear_hand_in_play(self) -> None:
        await self._emit_to_players("clear_hand_in_play", {})

    # trading related methods

    async def rank_handler(self, sid: str, rank: int) -> None:
        await super().rank_handler(self._get_spot(sid))

    async def _emit_set_rank(self, spot: int, rank: int) -> None:
        await self._emit('set_rank', {'rank': rank}, room=self._get_sid(spot))

    async def ask_handler(self, sid: str) -> None:
        await super().ask_handler(self._get_spot(sid))

    async def give_handler(self, sid: str) -> None:
        await super().give_handler(self._get_spot(sid))

    async def _emit_set_giving_options(
        self, spot: int, giving_options: Set[int]
    ) -> None:
        await self._emit(
            "set_giving_options",
            {"giving_options": list(giving_options)},
            room=self._get_sid(spot),
        )

    # misc

    async def lock_handler(self, sid: str) -> None:
        await super().lock_handler(self._get_spot(sid))
    
    async def unlock_handler(self, sid: str) -> None:
        await super().unlock_handler(self._get_spot(sid))

    async def _emit_set_unlocked(self, spot: int, unlocked: bool) -> None:
        await self._emit('set_unlocked', {'unlocked': unlocked}, room=self._get_sid(spot))

    async def _emit_message(self, message: str) -> None:
        await self._emit_to_players("message", {"message": message})

    # getters

    def _get_sid(self, spot: int) -> str:
        return self._spot_sid_bidict[spot]

    def _get_spot(self, sid: str) -> int:
        return self._spot_sid_bidict.inv[sid]

    # setters

    async def _emit_set_name(self, spot: int, name: str) -> None:
        await self._emit_to_players("set_name", {'spot': spot, 'name': name or ''})

    async def _emit_set_hand_in_play(self, hand: Hand) -> None:
        await self._emit_to_players(
            "set_hand_in_play",
            {
                "hand_in_play": list(hand),
                "hand_in_play_str": hand.id_str,
            },
        )

    async def _emit_set_asker(
        self, spot: int, asker: bool, takes_and_gives: int
    ) -> None:
        self._emit(
            "set_asker", {"asker": asker}, room=self._get_sid(spot)
        )

    async def _emit_set_giver(self, spot: int, giver: bool) -> None:
        await self._emit(
            "set_giver", {"giver": giver}, room=self._get_sid(spot)
        )

    async def _emit_set_takes(self, spot: int, takes: int) -> None:
        await self._emit(
            "set_takes", {"takes": takes}, room=self._get_sid(spot)
        )

    async def _emit_set_gives(self, spot: int, gives: int) -> None:
        await self._emit(
            "set_gives", {"gives": gives}, room=self._get_sid(spot)
        )

    async def _emit_add_to_already_asked(self, spot: int, rank: int) -> None:
        await self._emit('add_to_already_asked', {'rank': rank}, self._get_sid(spot))

    async def _emit_set_dot_color(self, spot: int, dot_color: str) -> None:
        await self._emit_to_players(
            "set_dot_color", {"spot": spot, "dot_color": dot_color}
        )

    # emitters

    async def _emit(self, *args, **kwargs) -> None:
        await self._sio.emit(*args, **kwargs)

    async def _emit_to_players(self, *args, **kwargs):
        """
        Emits to all players by default. Pass in skip_sid with a string
        or a list to skip players.

        The difference between this and _emit_to_server is that the
        latter emits to spectators as well.

        TODO: to should work instead of room
        """
        maybe_skip_sid = kwargs.get("skip_sid")
        if not maybe_skip_sid:
            await gather(
                *[
                    self._emit(*args, room=sid, **kwargs)
                    for sid in self._spot_sid_bidict.values()
                ]
            )
        elif isinstance(maybe_skip_sid, str):
            await gather(
                *[
                    self._emit(*args, room=sid, **kwargs)
                    for sid in self._spot_sid_bidict.values()
                    if sid != maybe_skip_sid
                ]
            )
        elif isinstance(maybe_skip_sid, list):
            await gather(
                *[
                    self._emit(*args, room=sid, **kwargs)
                    for sid in self._spot_sid_bidict.values()
                    if sid not in maybe_skip_sid
                ]
            )
        else:
            raise AssertionError("skip_sid can only be a string or a list")

    # TODO
    async def _emit_to_spectators(self, *args, **kwargs):
        ...

    # TODO
    async def _emit_to_server(self, *args, **kwargs):
        """
        Emits to players and spectators
        """
        ...


    async def cast_event(self, event):
        await self._events_counter.cast(event)

    async def _emit_hand_play(self, hand_hash: int):
        await self._hand_play_processor.cast(
            HandPlay(game_id=self.game_id, hand_hash=hand_hash)
        )

    async def _emit_alert(self, spot: int, alert: str) -> None:
        await self._emit("alert", {"alert": alert}, room=self._get_sid(spot))
