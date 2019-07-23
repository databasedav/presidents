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