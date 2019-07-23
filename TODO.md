* trust eval
    * for example, when card is clicked, simply flip the selected boolean first and then verify on the server and correct if necessary

* front end hand table
    * faster hand labeling

* auto join on server creation

* ~~rename room to server~~

* switch to FastAPI

* local tests on all base classes and emitting counterparts

* testing view with iframes

* ~~switch to async for base game timeout~~
    * not doing; base game has no timer, but can optionally use GreenThread

* ~~easiest to calculate hash~~
    * check that the hash is uniform

* add support for deciding certain behavior like whether add cards to a hand deselects those cards or not, etc.

* add state check fired by faust worker

* handle settings in some environment that differentiates development and production

* use cookie to remember user login

* add checks for player being unfinished; finished players literally shouldn't be able to do anything

* add `permitted` checks for `PresidentsError`'s

* high level for same hand play notifications
    * faust worker processes hand plays (the action of playing a hand, captured at the moment the hand is played). this involves adding the information necessary to emit an event to an individual player to the table (pretty sure this is just sid and not the namespace since sids are unique for each socket connection but need to confirm) such that the table maps from each hand hash to a list of the sids, say
    * each time an sid is added to a hand_hash's list of sids, an event should be emitted to each of these sids that increments the count that is shown to them of how many other people just played the same hand as them; this will be accomplished with a redis queue of events to emit
    * users should not continue to get updates after the 2 second block that they fell in at play time (this should be the time that the play command was received by the server) expires

* add in-game chat
