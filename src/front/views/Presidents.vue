<template>
  <Game :game_id="game_id"></Game>
</template>

<script>
import Game from "../components/Game.vue";

export default {
  name: "Presidents",

  components: {
    Game
  },

  props: {
    game_id: String
  },

  // beforeRouteLeave(to, from, next) {
  //   const answer = window.confirm("do you really want to leave?");
  //   if (answer) {
  //     next();
  //   } else {
  //     next(false);
  //   }
  // }
};
</script>
