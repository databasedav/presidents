<template>
  <v-row>
    <v-col cols="6" v-for="i in 1">
      <Game
        :server="'/server=dev'"
        :testing="true"
      ></Game>
    </v-col>
  </v-row>
</template>

<script>
import Game from "../components/Game.vue";

export default {
  name: "Tester",
  components: {
    Game
  }
};
</script>

<style></style>
