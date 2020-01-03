<template>
  <Game :rnsp="this.rnsp"></Game>
</template>

<script>
import Game from "../components/Game.vue";

export default {
  name: "Presidents",

  components: {
    Game
  },

  props: {
    rnsp: String
  },

  created() {
    this.$store.dispatch("plugin_server", {
      rnsp: this.rnsp
    });
  },

  beforeRouteLeave(to, from, next) {
    const answer = window.confirm("do you really want to leave?");
    if (answer) {
      next();
    } else {
      next(false);
    }
  }
};
</script>
