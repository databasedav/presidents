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

* rewrite front end in typescript

* high level for same hand play notifications
    * faust worker processes hand plays (the action of playing a hand, captured at the moment the hand is played). this involves adding the information necessary to emit an event to an individual player to the table (pretty sure this is just sid and not the namespace since sids are unique for each socket connection but need to confirm) such that the table maps from each hand hash to a list of the sids, say
    * each time an sid is added to a hand_hash's list of sids, an event should be emitted to each of these sids that increments the count that is shown to them of how many other people just played the same hand as them; this will be accomplished with a redis queue of events to emit
    * users should not continue to get updates after the 2 second block that they fell in at play time (this should be the time that the play command was received by the server) expires

* add in-game chat

* test messaging

* separate rooms for players and spectators so namespace can be used to emit to all people sitting in a server (since namespace is unique per server) and game specific events (that should not be visible to spectators) can be emitted to the 'players' room

* full demonstration of the same hand played feature via docker-compose
    * multiple container setup
        * uvicorn server
        * faust workers
        * dumb bot farm
        * viewing container which just allows you to play any card/hand (this can potentially be wrapped in a vue) 
    * this doesn't actually need the database to be set up but is obviously preferred to show off more stuff

* write out complete rules of presidents

* look into making presidents a mode service

* better way to do the game methods that just need to be re-written with awaits for emitting game

* switch to java null pointer exception bait

* tell miguel that users should be able to add namespaces after already connected and also access the callback function from anywhere in the event catching function

* record whether a move was autoplayed

* some sort of hot reloadable testing setup where I have access to all 4 players and the game automatically gets to some point that I can define as part of the setup

* add separate hud element for reserve time

* pausing testing

* minimize calculations on client-side